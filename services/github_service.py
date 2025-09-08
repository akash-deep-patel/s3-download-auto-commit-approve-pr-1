
from config import settings
from services.github_mcp import GitHubMCP
import os

class GitHubService:
    def __init__(self, access_token=None):
        if not access_token:
            raise ValueError("GitHub access token is required for GitHub operations")
        self.mcp = GitHubMCP(access_token=access_token)
        self.repo_name = self._get_repo_name()
        self.org = settings.github_org if settings.github_org and settings.github_org.strip() else None

    def _get_repo_name(self):
        if settings.github_repo and settings.github_repo.strip():
            return settings.github_repo.split('/')[-1]
        return settings.s3_bucket_name.replace('_', '-')

    def repo_exists(self):
        try:
            repos = self.mcp.list_repositories()
            full_name = f"{self.org}/{self.repo_name}" if self.org else self.repo_name
            return any(r.get('full_name', r.get('name')) == full_name for r in repos)
        except Exception:
            return False

    def create_repo(self):
        try:
            params = {"name": self.repo_name}
            if self.org:
                params["org"] = self.org
            return self.mcp.call_mcp_tool("create_repo", params)
        except Exception as e:
            raise RuntimeError(f"Failed to create repository: {e}")

    def upload_file(self, file_path, repo_path, commit_message, branch="main"):
        try:
            with open(file_path, "rb") as f:
                content = f.read()
            repo_full_name = f"{self.org}/{self.repo_name}" if self.org else self.repo_name
            params = {
                "repository": repo_full_name,
                "path": repo_path,
                "content": content.decode("utf-8") if isinstance(content, bytes) else content,
                "message": commit_message,
                "branch": branch
            }
            return self.mcp.call_mcp_tool("upload_file", params)
        except Exception as e:
            raise RuntimeError(f"Failed to upload file: {e}")

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
