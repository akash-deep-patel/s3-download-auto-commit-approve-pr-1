import requests
from config import settings

class GitHubMCP:
    def create_repo(self, name, org=None, private=False, description=None):
        params = {"name": name, "private": private}
        if org:
            params["org"] = org
        if description:
            params["description"] = description
        return self.call_mcp_tool("create_repo", params)

    def upload_file(self, repository, path, content, message, branch="main"):
        params = {
            "repository": repository,
            "path": path,
            "content": content,
            "message": message,
            "branch": branch
        }
        return self.call_mcp_tool("upload_file", params)

    def commit_changes(self, repository, message, branch="main"):
        params = {
            "repository": repository,
            "message": message,
            "branch": branch
        }
        return self.call_mcp_tool("commit_changes", params)

    def create_branch(self, repository, branch, source_branch="main"):
        params = {
            "repository": repository,
            "branch": branch,
            "source_branch": source_branch
        }
        return self.call_mcp_tool("create_branch", params)

    def create_pull_request(self, repository, title, body, head, base="main"):
        params = {
            "repository": repository,
            "title": title,
            "body": body,
            "head": head,
            "base": base
        }
        return self.call_mcp_tool("create_pull_request", params)

    def approve_pr(self, repository, pr_number):
        params = {
            "repository": repository,
            "pr_number": pr_number
        }
        return self.call_mcp_tool("approve_pr", params)

    def merge_pr(self, repository, pr_number):
        params = {
            "repository": repository,
            "pr_number": pr_number
        }
        return self.call_mcp_tool("merge_pr", params)
    def __init__(self, access_token=None, mcp_api_url=None):
        if not access_token:
            raise ValueError("GitHub access token is required")
        self.access_token = access_token
        self.mcp_api_url = mcp_api_url or "https://api.githubcopilot.com/mcp/"

    def call_mcp_tool(self, action, params):
        payload = {
            "action": action,
            "params": params
        }
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "User-Agent": "S3-GitHub-Automation/1.0"
        }
        try:
            response = requests.post(self.mcp_api_url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
            if not result.get("success", False):
                raise Exception(result.get("error", "MCP operation failed"))
            return result.get("data")
        except Exception as e:
            raise RuntimeError(f"MCP API call failed: {e}")

    def list_repositories(self):
        return self.call_mcp_tool("list_repositories", {"sort": "updated", "per_page": 100})

    def list_files(self, repo_full_name, path="", branch="main"):
        return self.call_mcp_tool("list_files", {"repository": repo_full_name, "path": path, "branch": branch})

    def read_file(self, repo_full_name, file_path, branch="main"):
        result = self.call_mcp_tool("read_file", {"repository": repo_full_name, "path": file_path, "branch": branch})
        if result.get("encoding") == "base64":
            import base64
            return base64.b64decode(result["content"]).decode("utf-8")
        return result["content"]

    def get_file_info(self, repo_full_name, file_path, branch="main"):
        return self.call_mcp_tool("get_file_info", {"repository": repo_full_name, "path": file_path, "branch": branch})

    def clone_repository(self, repo_full_name, target_path, branch="main"):
        return self.call_mcp_tool("clone_repository", {"repository": repo_full_name, "target_path": target_path, "branch": branch})

    def search_repositories(self, query, limit=10):
        return self.call_mcp_tool("search_repositories", {"query": query, "limit": limit})

    def get_user_info(self):
        return self.call_mcp_tool("get_user", {})

# Usage example:
# mcp = GitHubMCP(access_token="your_token", mcp_api_url="http://your-mcp-server/api/github/mcp")
# repos = mcp.list_repositories()
