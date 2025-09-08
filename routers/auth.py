from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse, JSONResponse
from auth.github_oauth import GitHubOAuth

router = APIRouter(prefix="/auth", tags=["auth"])
github_oauth = GitHubOAuth()

@router.get("/github")
def github_login():
    url = github_oauth.get_auth_url()
    return RedirectResponse(url)

@router.get("/callback")
def github_callback(request: Request):
    code = request.query_params.get("code")
    if not code:
        return JSONResponse(status_code=400, content={"error": "Missing code parameter"})
    try:
        token = github_oauth.get_token(code)
        user = github_oauth.get_user(token)
        return {"access_token": token, "user": user}
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})
