# S3 Download, Auto-Commit & Approve PR Workflow

## Description
This project automates the workflow of downloading files from AWS S3, committing them to a GitHub repository, and approving pull requests using FastAPI, AWS S3, and GitHub MCP. The application is designed for extensibility and clean separation of concerns, supporting future enhancements for workflow automation and integration.

## Installation

### Prerequisites
- Python 3.9 or higher (required for GitHub MCP compatibility)
- [pip](https://pip.pypa.io/en/stable/)

### Setup
1. Clone the repository:
   ```sh
   git clone <repo-url>
   cd s3-download-auto-commit-approve-pr
   ```
2. (Recommended) Create and activate a virtual environment:
   ```sh
   python -m venv venv
   venv\Scripts\activate
   ```
3. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```

## Usage

Start the FastAPI application using Uvicorn:
```sh
uvicorn main:app --reload
```

Access the API documentation at [http://localhost:8000/docs](http://localhost:8000/docs)


### Health Check
- `GET /health` — Returns API status and timestamp

### Authentication
- `GET /auth/github` — Redirects to GitHub OAuth login
- `GET /auth/callback?code=...` — Handles OAuth callback and returns access token and user info

### Workflow Automation
- `POST /workflow/download-and-commit` — Orchestrates S3 download, repo creation, commit, and PR
   - **Request Body Example:**
      ```json
      {
         "s3_prefix": "your/s3/folder/",
         "local_dir": "./downloads",
         "commit_message": "Automated update from S3",
         "branch_name": "auto-update",
         "pr_title": "Automated S3 Update",
         "pr_body": "This PR contains files downloaded from S3 and committed automatically."
      }
      ```
   - **Response Example:**
      ```json
      {
         "repo_created": true,
         "files_committed": 5,
         "pr_url": "https://github.com/your-org/your-repo/pull/1",
         "message": "Workflow completed successfully."
      }
      ```

## Error Handling & Logging
- All endpoints include robust error handling and log requests/responses for traceability.

## Project Structure
```
├── main.py                # FastAPI application entry point
├── requirements.txt       # Python dependencies
├── README.md              # Project documentation
├── app/                   # Core application modules
│   └── __init__.py
├── services/              # Business logic services (S3, GitHub MCP, etc.)
│   └── __init__.py
├── auth/                  # Authentication modules (GitHub OAuth, etc.)
│   └── __init__.py
├── routers/               # API route modules
│   └── __init__.py
```

## Configuration
- Environment variables and configuration details will be added in future phases.
- Use `.env` files and `python-dotenv` for managing secrets and settings.

## GitHub MCP Integration
- GitHub operations will use the Model Context Protocol (MCP) package for robust and secure automation.
- PyGithub is replaced by MCP for all GitHub-related tasks.

## License
MIT
