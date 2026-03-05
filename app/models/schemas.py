from pydantic import BaseModel, Field, field_validator
from typing import List
import re


class SummarizeRequest(BaseModel):
    github_url: str = Field(
        ...,
        description="URL of a public GitHub repository",
        json_schema_extra={"example": "https://github.com/psf/requests"}
    )

    @field_validator("github_url")
    @classmethod
    def validate_github_url(cls, v: str) -> str:
        """Validate GitHub URL format"""
        pattern = r"^https?://github\.com/[\w\-\.]+/[\w\-\.]+/?.*$"
        if not re.match(pattern, v):
            raise ValueError("Invalid GitHub URL format")
        return v


class SummarizeResponse(BaseModel):
    summary: str = Field(
        ...,
        description="Human-readable description of what the project does"
    )
    technologies: List[str] = Field(
        ...,
        description="List of main technologies, languages, and frameworks used"
    )
    structure: str = Field(
        ...,
        description="Brief description of the project structure"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "summary": "Requests is a popular Python library for making HTTP requests...",
                "technologies": ["Python", "urllib3", "certifi"],
                "structure": "The project follows a standard Python package layout..."
            }
        }
    }


class ErrorResponse(BaseModel):
    status: str = Field(default="error", description="Error status")
    message: str = Field(..., description="Error message")

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "error",
                "message": "Repository not found or is private"
            }
        }
    }
