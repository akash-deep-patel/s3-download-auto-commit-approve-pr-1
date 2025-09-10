
from config import settings
from services.github_mcp import GitHubMCP
import os
import base64
import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GitHubService:
    def __init__(self, access_token=None, s3_prefix=None, bucket_name=None):
        if not access_token:
            raise ValueError("GitHub access token is required for GitHub operations")
        self.mcp = GitHubMCP(access_token=access_token)
        self.s3_prefix = s3_prefix
        self.bucket_name = bucket_name or settings.s3_bucket_name
        self.repo_name = self._get_repo_name()
        self.org = settings.github_org if settings.github_org and settings.github_org.strip() else None

    def _get_repo_name(self):
        if settings.github_repo and settings.github_repo.strip():
            return settings.github_repo.split('/')[-1]
        
        # Create repo name from bucket name and S3 prefix
        base_name = self.bucket_name.replace('_', '-')
        
        if self.s3_prefix:
            # Clean the S3 prefix to make it suitable for repo name
            prefix_clean = self._clean_prefix_for_repo_name(self.s3_prefix)
            if prefix_clean:
                return f"{base_name}-{prefix_clean}"
        
        return base_name
    
    def _clean_prefix_for_repo_name(self, prefix):
        """Clean S3 prefix to make it suitable for GitHub repo name"""
        if not prefix:
            return ""
        
        # Remove leading/trailing slashes and spaces
        clean = prefix.strip('/ \t')
        
        # Replace slashes with dashes
        clean = clean.replace('/', '-').replace('\\', '-')
        
        # Remove invalid characters and keep only alphanumeric, hyphens, and underscores
        clean = re.sub(r'[^a-zA-Z0-9_-]', '-', clean)
        
        # Replace multiple consecutive hyphens with single hyphen
        clean = re.sub(r'-+', '-', clean)
        
        # Remove leading/trailing hyphens
        clean = clean.strip('-')
        
        # Limit length to 50 characters (GitHub repo names can be up to 100, but keeping reasonable)
        if len(clean) > 50:
            clean = clean[:50].rstrip('-')
        
        return clean
    
    def _get_repo_description(self):
        """Generate a repository description based on S3 prefix and bucket"""
        description = f"Repository auto-generated from S3 bucket '{self.bucket_name}'"
        
        if self.s3_prefix:
            clean_prefix = self.s3_prefix.strip('/ ')
            description += f" with prefix '{clean_prefix}'"
        
        description += ". Contains files downloaded and committed automatically."
        return description

    def repo_exists(self):
        try:
            logger.info("Checking if repository exists...calling mcp.list_repositories()")
            repos = self.mcp.list_repositories()
            logger.info(f"Existing repositories: {repos}")
            #log the repos
            full_name = f"{self.org}/{self.repo_name}" if self.org else self.repo_name
            return any(r.get('full_name', r.get('name')) == full_name for r in repos)
        except Exception:
            return False

    def create_repo(self):
        try:
            params = {
                "name": self.repo_name,
                "description": self._get_repo_description(),
                "private": False  # Make public by default, can be made configurable
            }
            if self.org:
                params["org"] = self.org
            return self.mcp.call_mcp_tool("create_repository", params)
        except Exception as e:
            raise RuntimeError(f"Failed to create repository: {e}")

    def upload_file(self, file_path, repo_path, commit_message, branch="main"):
        try:
            with open(file_path, "rb") as f:
                content = f.read()
            
            # Handle content encoding
            try:
                # Try to decode as UTF-8 for text files
                content_str = content.decode("utf-8")
                encoding = "utf-8"
            except UnicodeDecodeError:
                # For binary files, use base64 encoding
                content_str = base64.b64encode(content).decode("ascii")
                encoding = "base64"
            
            repo_full_name = f"{self.org}/{self.repo_name}" if self.org else self.repo_name
            params = {
                "repository": repo_full_name,
                "path": repo_path,
                "content": content_str,
                "message": commit_message,
                "branch": branch,
                "encoding": encoding
            }
            return self.mcp.call_mcp_tool("upload_file", params)
        except Exception as e:
            raise RuntimeError(f"Failed to upload file '{file_path}': {e}")

    def commit_changes(self, commit_message, branch="main"):
        try:
            repo_full_name = f"{self.org}/{self.repo_name}" if self.org else self.repo_name
            params = {
                "repository": repo_full_name,
                "message": commit_message,
                "branch": branch
            }
            return self.mcp.call_mcp_tool("commit_changes", params)
        except Exception as e:
            if 'rate limit' in str(e).lower():
                raise RuntimeError("GitHub API rate limit exceeded.")
            if 'permission' in str(e).lower():
                raise RuntimeError("Insufficient permissions for GitHub operation.")
            raise RuntimeError(f"Failed to commit changes: {e}")

    def create_branch(self, branch_name, source_branch="main"):
        try:
            repo_full_name = f"{self.org}/{self.repo_name}" if self.org else self.repo_name
            params = {
                "repository": repo_full_name,
                "branch": branch_name,
                "source_branch": source_branch
            }
            return self.mcp.call_mcp_tool("create_branch", params)
        except Exception as e:
            if 'rate limit' in str(e).lower():
                raise RuntimeError("GitHub API rate limit exceeded.")
            if 'permission' in str(e).lower():
                raise RuntimeError("Insufficient permissions for branch creation.")
            raise RuntimeError(f"Failed to create branch: {e}")

    def create_pull_request(self, title, body, head, base="main"):
        try:
            repo_full_name = f"{self.org}/{self.repo_name}" if self.org else self.repo_name
            params = {
                "repository": repo_full_name,
                "title": title,
                "body": body,
                "head": head,
                "base": base
            }
            return self.mcp.call_mcp_tool("create_pull_request", params)
        except Exception as e:
            if 'rate limit' in str(e).lower():
                raise RuntimeError("GitHub API rate limit exceeded.")
            if 'permission' in str(e).lower():
                raise RuntimeError("Insufficient permissions for PR creation.")
            raise RuntimeError(f"Failed to create pull request: {e}")

    def approve_and_merge_pr(self, pr_number):
        try:
            repo_full_name = f"{self.org}/{self.repo_name}" if self.org else self.repo_name
            params = {
                "repository": repo_full_name,
                "pr_number": pr_number
            }
            self.mcp.call_mcp_tool("approve_pr", params)
            self.mcp.call_mcp_tool("merge_pr", params)
            return True
        except Exception as e:
            if 'rate limit' in str(e).lower():
                raise RuntimeError("GitHub API rate limit exceeded.")
            if 'permission' in str(e).lower():
                raise RuntimeError("Insufficient permissions for PR approval/merge.")
            raise RuntimeError(f"Failed to approve/merge PR: {e}")
