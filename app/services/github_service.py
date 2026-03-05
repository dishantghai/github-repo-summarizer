import re
from typing import Tuple, List, Dict, Optional
import httpx
from app.config import settings


def parse_github_url(url: str) -> Tuple[str, str]:
    """
    Extract owner and repo from GitHub URL.
    
    Handles formats:
    - https://github.com/owner/repo
    - https://github.com/owner/repo.git
    - https://github.com/owner/repo/tree/branch
    - http://github.com/owner/repo
    
    Returns:
        Tuple[owner, repo]
    
    Raises:
        ValueError: If URL format is invalid
    """
    pattern = r"github\.com/([^/]+)/([^/\.]+)"
    match = re.search(pattern, url)

    if not match:
        raise ValueError("Invalid GitHub URL format")

    owner = match.group(1)
    repo = match.group(2)

    return owner, repo


async def fetch_repo_metadata(owner: str, repo: str) -> dict:
    """
    Fetch repository metadata from GitHub API.
    
    Returns:
        {
            'description': str,
            'language': str,
            'topics': List[str],
            'default_branch': str,
            'size': int,
            'is_private': bool
        }
    """
    url = f"{settings.GITHUB_API_BASE}/repos/{owner}/{repo}"
    headers = {"Accept": "application/vnd.github.v3+json"}

    if settings.GITHUB_TOKEN:
        headers["Authorization"] = f"token {settings.GITHUB_TOKEN}"

    async with httpx.AsyncClient(timeout=settings.GITHUB_TIMEOUT) as client:
        response = await client.get(url, headers=headers)

        if response.status_code == 404:
            raise ValueError("Repository not found or is private")
        elif response.status_code == 403:
            raise ValueError("GitHub API rate limit exceeded. Try again later.")
        elif response.status_code == 401:
            raise ValueError("GitHub authentication failed")

        response.raise_for_status()
        data = response.json()

        return {
            "description": data.get("description", "") or "",
            "language": data.get("language", "") or "",
            "topics": data.get("topics", []),
            "default_branch": data.get("default_branch", "main"),
            "size": data.get("size", 0),
            "is_private": data.get("private", False),
        }


async def fetch_repo_tree(
    owner: str, repo: str, branch: Optional[str] = None
) -> List[Dict]:
    """
    Fetch complete file tree from GitHub API.
    
    Returns:
        List of dicts with 'path', 'type', 'size' keys
    """
    if not branch:
        metadata = await fetch_repo_metadata(owner, repo)
        branch = metadata["default_branch"]

    url = f"{settings.GITHUB_API_BASE}/repos/{owner}/{repo}/git/trees/{branch}"
    params = {"recursive": "1"}
    headers = {"Accept": "application/vnd.github.v3+json"}

    if settings.GITHUB_TOKEN:
        headers["Authorization"] = f"token {settings.GITHUB_TOKEN}"

    async with httpx.AsyncClient(timeout=settings.GITHUB_TIMEOUT) as client:
        response = await client.get(url, params=params, headers=headers)

        if response.status_code == 404:
            raise ValueError("Branch not found")
        elif response.status_code == 409:
            raise ValueError("Repository is empty")
        elif response.status_code == 403:
            raise ValueError("GitHub API rate limit exceeded. Try again later.")

        response.raise_for_status()
        data = response.json()

        tree_items = []
        for item in data.get("tree", []):
            tree_items.append(
                {
                    "path": item["path"],
                    "type": item["type"],
                    "size": item.get("size", 0),
                }
            )

        return tree_items


async def fetch_file_content(
    owner: str, repo: str, path: str, branch: str = "main"
) -> str:
    """
    Fetch raw file content from GitHub.
    
    Uses raw.githubusercontent.com for efficiency.
    """
    url = f"{settings.GITHUB_RAW_BASE}/{owner}/{repo}/{branch}/{path}"

    async with httpx.AsyncClient(timeout=settings.GITHUB_TIMEOUT) as client:
        try:
            response = await client.get(url)

            if response.status_code == 404:
                return ""

            response.raise_for_status()

            content = response.text[: settings.MAX_FILE_SIZE_CHARS]
            return content
        except httpx.TimeoutException:
            return ""
        except Exception:
            return ""
