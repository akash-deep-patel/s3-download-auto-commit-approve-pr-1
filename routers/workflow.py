from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ValidationError
from services.s3_service import S3Service
from services.github_service import GitHubService
from services.zip_service import ZipService
from config import settings
import os
import logging
import traceback
import time
from datetime import datetime
import re

router = APIRouter(prefix="/workflow", tags=["workflow"])
logger = logging.getLogger(__name__)

def clean_extracted_path(file_path: str) -> str:
    """
    Clean file paths by removing '_extracted' suffixes from directory names
    
    Args:
        file_path: Original file path that may contain '_extracted' directories
        
    Returns:
        str: Cleaned path with '_extracted' suffixes removed
        
    Example:
        'test_repo-master_extracted/src/main.py' -> 'test_repo-master/src/main.py'
        'code-analyzer_extracted/app.py' -> 'code-analyzer/app.py'
    """
    # Replace '_extracted/' with '/' and '_extracted\\' with '\\' (for Windows paths)
    cleaned_path = re.sub(r'_extracted([/\\])', r'\1', file_path)
    
    # Handle case where '_extracted' is at the end of the path (directory name only)
    if cleaned_path.endswith('_extracted'):
        cleaned_path = cleaned_path[:-10]  # Remove '_extracted' suffix
    
    return cleaned_path

class DownloadAndCommitRequest(BaseModel):
    github_access_token: str
    s3_prefix: str
    local_dir: str
    commit_message: str
    branch_name: str = "auto-update"
    pr_title: str = "Automated S3 Update"
    pr_body: str = "This PR contains files downloaded from S3 and committed automatically."

class DownloadAndCommitResponse(BaseModel):
    repo_created: bool
    files_committed: int
    pr_url: str
    message: str

@router.post("/download-and-commit", response_model=DownloadAndCommitResponse)
def download_and_commit(data: DownloadAndCommitRequest):
    logger.info(f"Received request: {data}")
    
    # Validation checks
    if not data.github_access_token or data.github_access_token.strip() == "":
        logger.error("GitHub access token is missing or empty")
        raise HTTPException(status_code=400, detail="GitHub access token is required")
    
    if not data.s3_prefix or data.s3_prefix.strip() == "":
        logger.error("S3 prefix is missing or empty")
        raise HTTPException(status_code=400, detail="S3 prefix is required")
    
    # Generate unique local directory to avoid conflicts
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # Include milliseconds
    unique_local_dir = f"{data.local_dir}_{timestamp}"
    logger.info(f"Using unique local directory: {unique_local_dir}")
    
    if not data.commit_message or data.commit_message.strip() == "":
        logger.error("Commit message is missing or empty")
        raise HTTPException(status_code=400, detail="Commit message is required")
    
    try:
        logger.info("Initializing S3 service...")
        s3 = S3Service()
        logger.info("S3 service initialized successfully")
        
        logger.info("Initializing GitHub service...")
        github = GitHubService(
            access_token=data.github_access_token, 
            s3_prefix=data.s3_prefix,
            bucket_name=settings.s3_bucket_name
        )
        logger.info(f"GitHub service initialized successfully. Repo name will be: {github.repo_name}")
        
        # Download files from S3
        logger.info(f"Downloading files from S3 prefix: {data.s3_prefix}")
        
        # Ensure unique local directory exists
        if not os.path.exists(unique_local_dir):
            os.makedirs(unique_local_dir, exist_ok=True)
            logger.info(f"Created unique local directory: {unique_local_dir}")
        
        # Download with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                s3.download_folder(data.s3_prefix, unique_local_dir)
                logger.info(f"S3 download completed successfully on attempt {attempt + 1}")
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                logger.warning(f"S3 download attempt {attempt + 1} failed: {e}. Retrying...")
                time.sleep(2)
        
        # Wait a moment to ensure download is complete
        time.sleep(1)
        
        # Extract ZIP files if any exist
        logger.info("Checking for ZIP files to extract...")
        zip_extraction_success, extracted_files = ZipService.extract_all_zips_in_directory(unique_local_dir)
        if extracted_files:
            logger.info(f"Successfully extracted {len(extracted_files)} files from ZIP archives")
        else:
            logger.info("No ZIP files found or extracted")
        
        # Get all files after extraction (excluding any remaining ZIP files)
        files = ZipService.get_all_files_after_extraction(unique_local_dir)
        logger.info(f"Found {len(files)} files to commit (after ZIP extraction)")
        
        if len(files) == 0:
            logger.warning("No files found to commit")
            raise ValueError(f"No files found in S3 prefix '{data.s3_prefix}' or local directory '{unique_local_dir}'")
        
        # Create repo if not exists
        repo_created = False
        logger.info("Checking if repository exists...")
        if not github.repo_exists():
            logger.info("Repository does not exist, creating...")
            github.create_repo()
            repo_created = True
            logger.info("Repository created successfully")
        else:
            logger.info("Repository already exists")
        
        # Create branch
        logger.info(f"Creating branch: {data.branch_name}")
        github.create_branch(data.branch_name)
        logger.info("Branch created successfully")
        
        # Upload files and commit
        logger.info("Uploading files...")
        path_cleaning_examples = []
        for f in files:
            # Calculate relative path from unique_local_dir
            raw_repo_path = os.path.relpath(f, unique_local_dir).replace("\\", "/")
            # Clean the path by removing '_extracted' suffixes
            repo_path = clean_extracted_path(raw_repo_path)
            
            # Log path transformation for first few files as examples
            if len(path_cleaning_examples) < 3 and raw_repo_path != repo_path:
                path_cleaning_examples.append(f"{raw_repo_path} -> {repo_path}")
            
            github.upload_file(f, repo_path, data.commit_message, branch=data.branch_name)
        
        if path_cleaning_examples:
            logger.info(f"Path cleaning examples: {'; '.join(path_cleaning_examples)}")
        logger.info("Files uploaded successfully")
        
        # logger.info("Committing changes...")
        # github.commit_changes(data.commit_message, branch=data.branch_name)
        # logger.info("Changes committed successfully")
        
        # Create PR
        logger.info("Creating pull request...")
        pr = github.create_pull_request(
            title=data.pr_title,
            body=data.pr_body,
            head=data.branch_name
        )
        pr_url = pr.get("html_url", "") if isinstance(pr, dict) else getattr(pr, "html_url", "")
        logger.info(f"Pull request created: {pr_url}")
        
        return DownloadAndCommitResponse(
            repo_created=repo_created,
            files_committed=len(files),
            pr_url=pr_url,
            message="Workflow completed successfully."
        )
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=f"Validation error: {e}")
    except ValueError as e:
        logger.error(f"Value error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        logger.error(f"Runtime error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=400, detail=f"Unexpected error: {str(e)}")
