import os
from pydantic import BaseModel, Field, ValidationError
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load environment variables from .env file
load_dotenv(dotenv_path=".env")

class Settings(BaseSettings):
    # AWS Credentials
    aws_access_key_id: str = Field(..., env="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str = Field(..., env="AWS_SECRET_ACCESS_KEY")
    aws_region: str = Field(..., env="AWS_REGION")
    s3_bucket_name: str = Field(..., env="S3_BUCKET_NAME")

    # GitHub OAuth
    github_client_id: str = Field(..., env="GITHUB_CLIENT_ID")
    github_client_secret: str = Field(..., env="GITHUB_CLIENT_SECRET")
    github_repo: str = Field("", env="GITHUB_REPO")

    # Optional settings
    github_org: str = Field(None, env="GITHUB_ORG")
    environment: str = Field("development", env="ENVIRONMENT")

try:
    settings = Settings()
except ValidationError as e:
    print("Configuration validation error:", e)
    raise
