from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse
from config import settings
import requests
import os

GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_API_URL = "https://api.github.com"

class GitHubOAuth:
    def __init__(self):
        self.client_id = settings.github_client_id
        self.client_secret = settings.github_client_secret
        self.redirect_uri = os.getenv("GITHUB_REDIRECT_URI", "http://localhost:8000/auth/callback")

    def get_auth_url(self, state=None):
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "repo user",
            "state": state or ""
        }
        query = "&".join([f"{k}={v}" for k, v in params.items() if v])
        return f"{GITHUB_AUTH_URL}?{query}"

    def get_token(self, code):
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": self.redirect_uri
        }
        headers = {"Accept": "application/json"}
        response = requests.post(GITHUB_TOKEN_URL, data=data, headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="GitHub token exchange failed")
        return response.json().get("access_token")

    def get_user(self, token):
        headers = {"Authorization": f"token {token}"}
        response = requests.get(f"{GITHUB_API_URL}/user", headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch GitHub user info")
        return response.json()
