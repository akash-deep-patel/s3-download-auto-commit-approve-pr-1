from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.s3_service import S3Service
from services.github_service import GitHubService
import os

router = APIRouter(prefix="/workflow", tags=["workflow"])

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
    s3 = S3Service()
    github = GitHubService(access_token=data.github_access_token)
    try:
        # Download files from S3
        s3.download_folder(data.s3_prefix, data.local_dir)
        files = []
        for root, _, filenames in os.walk(data.local_dir):
            for fname in filenames:
                files.append(os.path.join(root, fname))
        # Create repo if not exists
        repo_created = False
        if not github.repo_exists():
            github.create_repo()
            repo_created = True
        # Create branch
        github.create_branch(data.branch_name)
        # Upload files and commit
        for f in files:
            repo_path = os.path.relpath(f, data.local_dir).replace("\\", "/")
            github.upload_file(f, repo_path, data.commit_message)
        github.commit_changes(data.commit_message)
        # Create PR
        pr = github.create_pull_request(
            title=data.pr_title,
            body=data.pr_body,
            head=data.branch_name
        )
        pr_url = pr.get("html_url", "") if isinstance(pr, dict) else getattr(pr, "html_url", "")
        return DownloadAndCommitResponse(
            repo_created=repo_created,
            files_committed=len(files),
            pr_url=pr_url,
            message="Workflow completed successfully."
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
