import time
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
        self._current_user = None  # Cache for current user info

    def call_mcp_tool(self, action, params):
        # Add access_token to params (like the working implementation)
        enhanced_params = {
            **params,
            "access_token": self.access_token
        }
        
        payload = {
            "action": action,
            "params": enhanced_params
        }
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "User-Agent": "S3-GitHub-Automation/1.0"
        }
        
        try:
            print(f"MCP API call: {action}", payload, headers, self.mcp_api_url)  # Debug logging
            response = requests.post(self.mcp_api_url, json=payload, headers=headers)
            
            print(f"MCP API response status: {response.status_code}")
            
            if not response.ok:
                error_text = response.text
                print(f"MCP API error response: {error_text}")
                raise Exception(f"MCP API call failed: {response.status_code} - {error_text}")
            
            result = response.json()
            print(f"MCP API result: {result}")
            
            if not result.get("success", False):
                raise Exception(result.get("error", "MCP operation failed"))
            
            return result.get("data")
        except Exception as e:
            print(f"MCP Tool Call Error ({action}): {e}")
            print(f"Attempting fallback to direct GitHub API for {action}")
            
            # Try fallback to direct GitHub API for some operations
            try:
                return self._fallback_to_github_api(action, enhanced_params)
            except Exception as fallback_error:
                print(f"Fallback also failed: {fallback_error}")
                raise RuntimeError(f"Both MCP API and GitHub API fallback failed: {e}")

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
    
    def _get_current_username(self):
        """Get the current authenticated user's username"""
        if self._current_user is None:
            try:
                # Try MCP first
                user_info = self.get_user_info()
                self._current_user = user_info.get("login")
            except Exception:
                # Fallback to direct GitHub API
                try:
                    headers = {
                        "Authorization": f"Bearer {self.access_token}",
                        "Accept": "application/vnd.github.v3+json",
                        "User-Agent": "S3-GitHub-Automation/1.0"
                    }
                    response = requests.get("https://api.github.com/user", headers=headers)
                    response.raise_for_status()
                    user_data = response.json()
                    self._current_user = user_data.get("login")
                except Exception as e:
                    raise RuntimeError(f"Failed to get current user: {e}")
        
        return self._current_user
    
    def _get_full_repo_name(self, repo_name):
        """Get full repository name in format owner/repo"""
        if "/" in repo_name:
            # Already in full format
            return repo_name
        else:
            # Add current user as owner
            username = self._get_current_username()
            return f"{username}/{repo_name}"
    
    def _fallback_to_github_api(self, action, params):
        """Fallback to direct GitHub API when MCP fails"""
        print(f"Using GitHub API fallback for action: {action}")
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "S3-GitHub-Automation/1.0"
        }
        
        if action == "create_repository":
            return self._github_api_create_repo(params, headers)
        elif action == "list_repositories":
            return self._github_api_list_repos(params, headers)
        elif action == "upload_file":
            return self._github_api_upload_file(params, headers)
        elif action == "create_branch":
            return self._github_api_create_branch(params, headers)
        # elif action == "commit_changes":  #already done while uploading the files
        #     return self._github_api_commit_changes(params, headers)
        elif action == "create_pull_request":
            return self._github_api_create_pull_request(params, headers)
        elif action == "get_user":
            return self._github_api_get_user(params, headers)
        else:
            raise Exception(f"No GitHub API fallback available for action: {action}")
    
    def _github_api_create_repo(self, params, headers):
        """Create repository using direct GitHub API"""
        api_url = "https://api.github.com/user/repos"

        payload = {
            "name": params["name"],
            "description": params.get("description", ""),
            "private": params.get("private", False)
        }
        
        if params.get("org"):
            api_url = f"https://api.github.com/orgs/{params['org']}/repos"
        
        print(f"Creating repo via GitHub API with params: {payload}, headers: {headers} to url: {api_url}")
        response = requests.post(api_url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    
    def _github_api_list_repos(self, params, headers):
        """List repositories using direct GitHub API"""
        api_url = "https://api.github.com/user/repos"
        query_params = {
            "sort": params.get("sort", "updated"),
            "per_page": params.get("per_page", 100)
        }
        
        response = requests.get(api_url, params=query_params, headers=headers)
        response.raise_for_status()
        return response.json()
    
    def _github_api_upload_file(self, params, headers):
        """Upload file using direct GitHub API"""
        repo = self._get_full_repo_name(params["repository"])
        path = params["path"]
        content = params["content"]
        message = params["message"]
        branch = params.get("branch", "main")
        
        # GitHub API expects base64 encoded content
        import base64
        if isinstance(content, str):
            content_b64 = base64.b64encode(content.encode()).decode()
        else:
            content_b64 = base64.b64encode(content).decode()
        
        api_url = f"https://api.github.com/repos/{repo}/contents/{path}"
        payload = {
            "message": message,
            "content": content_b64,
            "branch": branch
        }
        
        response = requests.put(api_url, json=payload, headers=headers)
        response.raise_for_status()
        print(f"File upload response: {response.json()}")
        return response.json()

    def _github_api_create_branch(self, params, headers):
        """
        Create a new branch in the repository using GitHub API.

        Params should include:
        - repository: full repo name in the format "owner/repo"
        - branch: name of the new branch to create
        - source_branch: branch name from which new branch is created (default main)

        """
        #dummy commit to main branch
        time.sleep(5)
        print("creating dummy commit to main branch README.md")
        self._github_api_upload_file({
            "repository":  params["repository"],
            "path": "README.md",
            "content": "# Initial Commit\nThis repo was created automatically.",
            "message": "Initial commit with README",
            "branch": "main"
        }, headers)

        import requests

        repo = self._get_full_repo_name(params.get("repository"))
        new_branch = params.get("branch")
        source_branch = params.get("source_branch", "main")

        # Step 1: Get the latest commit SHA of the source branch
        ref_url = f"https://api.github.com/repos/{repo}/git/ref/heads/{source_branch}"
        ref_response = requests.get(ref_url, headers=headers)
        ref_response.raise_for_status()
        ref_data = ref_response.json()
        commit_sha = ref_data["object"]["sha"]

        # Step 2: Create the new branch (git ref)
        create_ref_url = f"https://api.github.com/repos/{repo}/git/refs"
        payload = {
            "ref": f"refs/heads/{new_branch}",
            "sha": commit_sha
        }
        create_response = requests.post(create_ref_url, json=payload, headers=headers)
        create_response.raise_for_status()

        return create_response.json()

    def _github_api_create_pull_request(self, params, headers):
        """
        Create a new pull request in the repository using GitHub API.

        Params should include:
        - repository: full repo name in the format "owner/repo"
        - title: PR title (string)
        - body: PR description/body (string)
        - head: name of the branch where your changes are implemented (string)
        - base: name of the branch you want the changes pulled into (string, default 'main')
        """
        import requests

        repo = self._get_full_repo_name(params["repository"])
        title = params["title"]
        body = params.get("body", "")
        head = params["head"]  # source branch name
        base = params.get("base", "main")  # target branch name

        pr_url = f"https://api.github.com/repos/{repo}/pulls"
        payload = {
            "title": title,
            "body": body,
            "head": head,
            "base": base
        }

        response = requests.post(pr_url, json=payload, headers=headers)
        response.raise_for_status()

        return response.json()
    
    def _github_api_get_user(self, params, headers):
        """Get current user info using direct GitHub API"""
        response = requests.get("https://api.github.com/user", headers=headers)
        response.raise_for_status()
        return response.json()

# Usage example:
# mcp = GitHubMCP(access_token="your_token", mcp_api_url="http://your-mcp-server/api/github/mcp")
# repos = mcp.list_repositories()
