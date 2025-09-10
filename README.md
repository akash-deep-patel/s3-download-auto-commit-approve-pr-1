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

## API Endpoints

### Health Check
- **`GET /health`** — Returns API status and timestamp
  
  **Response:**
  ```json
  {
    "status": "ok",
    "timestamp": "2025-09-09T14:05:57.123456Z"
  }
  ```

### Authentication

#### GitHub OAuth Flow
1. **`GET /auth/github`** — Redirects to GitHub OAuth login
   - Redirects user to GitHub for authorization
   - User authorizes the application and is redirected back

2. **`GET /auth/callback?code=...`** — Handles OAuth callback and returns access token
   
   **Response:**
   ```json
   {
     "access_token": "gho_1234567890abcdef...",
     "user": {
       "login": "username",
       "id": 12345678,
       "name": "User Name",
       "email": "user@example.com"
     }
   }
   ```

### Workflow Automation

#### S3 to GitHub Workflow
**`POST /workflow/download-and-commit`** — Downloads files from S3, extracts ZIP archives, creates/updates GitHub repository, and creates a pull request.

**Features:**
- 🔄 Downloads files from specified S3 prefix
- 📦 Automatically extracts ZIP files with smart flattening (removes unnecessary nested directories)
- 🏗️ Creates GitHub repository if it doesn't exist (named using S3 bucket + prefix)
- 🌿 Creates a new branch for changes
- 📤 Uploads all files to the repository
- 🔀 Creates a pull request with the changes
- ✨ Removes `_extracted` suffixes from paths for clean repository structure

**Request Body:**
```json
{
  "github_access_token": "gho_1234567890abcdef...",
  "s3_prefix": "repositories/1/",
  "local_dir": "./downloads",
  "commit_message": "Auto-commit: ZIP files extracted from S3",
  "branch_name": "s3-extracted-content",
  "pr_title": "S3 ZIP Content Extraction",
  "pr_body": "This PR contains files extracted from ZIP archives downloaded from S3. All ZIP files have been automatically extracted with smart flattening for clean repository structure."
}
```

**Complete Workflow Example:**
```bash
# Step 1: Authenticate with GitHub
curl -X GET "http://localhost:8000/auth/github"
# Follow redirect to GitHub, authorize, get redirected back
# Extract access_token from callback response

# Step 2: Execute the workflow
curl -X POST "http://localhost:8000/workflow/download-and-commit" \
  -H "Content-Type: application/json" \
  -d '{
    "github_access_token": "gho_your_token_from_step1",
    "s3_prefix": "repositories/1/",
    "local_dir": "./downloads",
    "commit_message": "Auto-commit: ZIP files extracted from S3",
    "branch_name": "s3-extracted-content",
    "pr_title": "S3 ZIP Content Extraction",
    "pr_body": "Automated extraction and commit of ZIP files from S3 bucket."
  }'
```

**Response Example:**
```json
{
  "repo_created": true,
  "files_committed": 51,
  "pr_url": "https://github.com/username/s3-rsm-repositories-1/pull/1",
  "message": "Workflow completed successfully."
}
```

**Request Parameters:**
- `github_access_token` (required): GitHub personal access token obtained from `/auth/callback`
- `s3_prefix` (required): S3 prefix/folder path to download files from
- `local_dir` (required): Local directory for temporary file storage
- `commit_message` (required): Git commit message
- `branch_name` (optional): Branch name for changes (default: "auto-update")
- `pr_title` (optional): Pull request title (default: "Automated S3 Update")
- `pr_body` (optional): Pull request description

## Key Features

### 🚀 Advanced ZIP Processing
- **Smart ZIP Extraction**: Automatically detects and extracts ZIP files from S3 downloads
- **Directory Flattening**: Removes unnecessary nested directories (e.g., `project-master/` wrapper folders)
- **Clean Repository Structure**: Eliminates `_extracted` suffixes from uploaded paths
- **Multiple Format Support**: Handles both text and binary files with proper encoding

### 🔐 Dynamic GitHub Integration
- **User-Agnostic**: Works with any GitHub user's access token (no hardcoded usernames)
- **OAuth Flow**: Complete GitHub authentication with OAuth 2.0
- **Repository Auto-Creation**: Automatically creates repositories with meaningful names based on S3 structure
- **Branch Management**: Creates feature branches and pull requests
- **MCP Integration**: Uses GitHub Model Context Protocol with fallback to direct GitHub API

### ⚡ Robust Error Handling
- **Comprehensive Logging**: Detailed logs for debugging and monitoring
- **Graceful Fallbacks**: MCP to GitHub API fallback for reliability
- **Input Validation**: Thorough validation of request parameters
- **Retry Logic**: Automatic retries for transient failures

### 🏧 Production Ready
- **Unique Directories**: Timestamp-based directories prevent concurrent request conflicts
- **Memory Efficient**: Streaming file processing for large ZIP archives
- **Security Focused**: Proper token handling and access control
- **Scalable Architecture**: Clean separation of concerns with service-based design

## Error Handling & Logging
- All endpoints include robust error handling and log requests/responses for traceability.
- Detailed error messages help identify and resolve issues quickly.
- Comprehensive logging throughout the workflow for debugging and monitoring.

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

### Environment Variables
Create a `.env` file in the project root with the following variables:

```env
# AWS Credentials (required)
AWS_ACCESS_KEY_ID=your-aws-access-key-id
AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-s3-bucket-name

# GitHub OAuth (required)
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret

# GitHub Repository (optional)
GITHUB_REPO=your-username/your-repo
GITHUB_ORG=your-org-name

# Environment
ENVIRONMENT=development
```

### Setup GitHub OAuth App
1. Go to GitHub Settings → Developer settings → OAuth Apps
2. Create a new OAuth App with:
   - **Application name**: Your app name
   - **Homepage URL**: `http://localhost:8000`
   - **Authorization callback URL**: `http://localhost:8000/auth/callback`
3. Copy the Client ID and Client Secret to your `.env` file

### AWS S3 Setup
1. Create an S3 bucket or use an existing one
2. Ensure your AWS credentials have read access to the bucket
3. Update the `.env` file with your AWS credentials and bucket name

## GitHub MCP Integration

This application uses the **GitHub Model Context Protocol (MCP)** for robust GitHub operations:

### MCP Features
- **Primary Integration**: Uses GitHub MCP server for all GitHub operations
- **Automatic Fallback**: Falls back to direct GitHub REST API if MCP is unavailable
- **Token-Based Auth**: Supports GitHub personal access tokens and OAuth
- **Comprehensive Operations**: Repository management, file uploads, branch creation, PR management

### Supported Operations
- ✅ List repositories
- ✅ Create repositories with descriptions
- ✅ Upload files (text and binary with proper encoding)
- ✅ Create branches
- ✅ Create pull requests
- ✅ Get user information

### Error Handling
- **MCP First**: Attempts GitHub MCP operations first
- **GitHub API Fallback**: Automatically falls back to direct GitHub API calls
- **Comprehensive Logging**: Detailed logs for both MCP and fallback operations

## License
MIT
