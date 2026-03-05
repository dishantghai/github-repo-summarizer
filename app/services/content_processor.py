import re
from typing import List, Dict
from app.config import settings
from app.services.github_service import fetch_file_content

# Patterns to ignore (binary files, dependencies, build artifacts)
IGNORE_PATTERNS = [
    # Directories
    r"node_modules/",
    r"vendor/",
    r"\.git/",
    r"__pycache__/",
    r"\.pytest_cache/",
    r"dist/",
    r"build/",
    r"\.venv/",
    r"venv/",
    r"env/",
    r"\.next/",
    r"\.nuxt/",
    r"coverage/",
    r"\.idea/",
    r"\.vscode/",
    r"target/",
    r"\.tox/",
    r"\.mypy_cache/",
    r"\.ruff_cache/",
    # Lock files
    r".*\.lock$",
    r"package-lock\.json$",
    r"yarn\.lock$",
    r"Pipfile\.lock$",
    r"poetry\.lock$",
    r"composer\.lock$",
    r"Gemfile\.lock$",
    r"pnpm-lock\.yaml$",
    r"bun\.lockb$",
    # Minified files
    r".*\.min\.js$",
    r".*\.min\.css$",
    r".*\.map$",
    r".*\.bundle\.js$",
    # Binary/Media files
    r".*\.(png|jpg|jpeg|gif|ico|svg|webp|bmp|tiff)$",
    r".*\.(woff|woff2|ttf|eot|otf)$",
    r".*\.(mp4|avi|mov|wmv|mkv|webm)$",
    r".*\.(mp3|wav|ogg|flac|aac)$",
    r".*\.(zip|tar|gz|rar|7z|bz2|xz)$",
    r".*\.(exe|dll|so|dylib|bin|dmg|msi)$",
    r".*\.(pdf|doc|docx|xls|xlsx|ppt|pptx)$",
    r".*\.(db|sqlite|sqlite3)$",
    r".*\.(pyc|pyo|class|o|obj)$",
    # Generated files
    r".*\.generated\.",
    r"\.DS_Store$",
    r"Thumbs\.db$",
]

# Priority levels (lower number = higher priority)
FILE_PRIORITIES = {
    # Priority 1: Documentation
    r"^README\.(md|rst|txt)$": 1,
    r"^readme\.(md|rst|txt)$": 1,
    r"^CONTRIBUTING\.(md|rst)$": 1,
    # Priority 2: Package/Project configuration
    r"^package\.json$": 2,
    r"^pyproject\.toml$": 2,
    r"^setup\.py$": 2,
    r"^setup\.cfg$": 2,
    r"^Cargo\.toml$": 2,
    r"^pom\.xml$": 2,
    r"^build\.gradle$": 2,
    r"^go\.mod$": 2,
    r"^composer\.json$": 2,
    r"^Gemfile$": 2,
    r"^mix\.exs$": 2,
    r"^deno\.json$": 2,
    # Priority 3: Dependencies
    r"^requirements\.txt$": 3,
    r"^requirements/.*\.txt$": 3,
    r"^Pipfile$": 3,
    # Priority 4: Infrastructure/DevOps
    r"^Dockerfile$": 4,
    r"^docker-compose\.ya?ml$": 4,
    r"^\.github/workflows/.*\.ya?ml$": 4,
    r"^\.gitlab-ci\.yml$": 4,
    r"^Makefile$": 4,
    r"^Procfile$": 4,
    r"^vercel\.json$": 4,
    r"^netlify\.toml$": 4,
    # Priority 5: Configuration
    r"^\.env\.example$": 5,
    r"^config\.(js|ts|py|yml|yaml|json)$": 5,
    r"^tsconfig\.json$": 5,
    r"^webpack\.config\.js$": 5,
    r"^vite\.config\.(js|ts)$": 5,
    r"^next\.config\.(js|mjs)$": 5,
    r"^\.eslintrc.*$": 5,
    r"^\.prettierrc.*$": 5,
    # Priority 6: Main entry points
    r"^(main|index|app|server)\.(py|js|ts|go|rs|java|rb)$": 6,
    r"^src/(main|index|app|server)\.(py|js|ts|jsx|tsx)$": 6,
    r"^lib/(main|index)\.(py|js|ts|rb)$": 6,
    r"^cmd/.*\.go$": 6,
    r"^src/lib\.rs$": 6,
    # Priority 7: Source directories
    r"^src/.*\.(py|js|ts|jsx|tsx|go|rs|java|rb)$": 7,
    r"^lib/.*\.(py|js|ts|rb)$": 7,
    r"^app/.*\.(py|js|ts|jsx|tsx|rb)$": 7,
    r"^pkg/.*\.go$": 7,
}


def should_ignore_file(path: str) -> bool:
    """Check if file should be ignored based on patterns"""
    for pattern in IGNORE_PATTERNS:
        if re.search(pattern, path, re.IGNORECASE):
            return True
    return False


def get_file_priority(path: str) -> int:
    """
    Get priority score for a file (lower = higher priority).
    Returns 999 for files not matching any pattern.
    """
    for pattern, priority in FILE_PRIORITIES.items():
        if re.search(pattern, path, re.IGNORECASE):
            return priority
    return 999


def prioritize_files(tree_items: List[Dict]) -> List[Dict]:
    """
    Filter and sort files by priority.
    
    Returns:
        List of file dicts sorted by priority (highest first)
    """
    files = [
        item
        for item in tree_items
        if item["type"] == "blob" and not should_ignore_file(item["path"])
    ]

    for file in files:
        file["priority"] = get_file_priority(file["path"])

    files.sort(key=lambda x: (x["priority"], x["path"]))

    return files


def generate_tree_structure(tree_items: List[Dict], max_lines: int = 100) -> str:
    """
    Generate a visual directory tree structure.
    
    Returns:
        String representation of directory tree
    """
    all_paths = []

    for item in tree_items:
        if should_ignore_file(item["path"]):
            continue
        if item["type"] == "tree":
            all_paths.append(item["path"] + "/")
        elif get_file_priority(item["path"]) <= 7:
            all_paths.append(item["path"])

    all_paths.sort()

    if len(all_paths) > max_lines:
        all_paths = all_paths[:max_lines]
        truncated = True
    else:
        truncated = False

    tree_lines = ["Project Structure:", ""]
    
    for path in all_paths:
        depth = path.count("/")
        indent = "  " * depth
        name = path.rstrip("/").split("/")[-1]
        if path.endswith("/"):
            name += "/"
        tree_lines.append(f"{indent}{name}")

    if truncated:
        tree_lines.append(
            f"\n... (truncated, showing {max_lines} of {len(tree_items)} items)"
        )

    return "\n".join(tree_lines)


async def build_context(
    owner: str, repo: str, branch: str, tree_items: List[Dict], metadata: Dict
) -> str:
    """
    Build optimized context string for LLM.
    
    Strategy:
    1. Add repository metadata
    2. Add directory tree structure
    3. Add README content (high priority)
    4. Add config/dependency files
    5. Add key source files
    6. Track token budget and stop when approaching limit
    
    Returns:
        Formatted context string
    """
    context_parts = []
    char_count = 0
    max_chars = settings.MAX_CONTEXT_TOKENS * 4

    # 1. Repository metadata
    topics_str = ", ".join(metadata.get("topics", [])) if metadata.get("topics") else "None"
    meta_section = f"""Repository: {owner}/{repo}
Description: {metadata.get('description') or 'No description'}
Primary Language: {metadata.get('language') or 'Unknown'}
Topics: {topics_str}
"""
    context_parts.append(meta_section)
    char_count += len(meta_section)

    # 2. Directory tree
    tree_str = generate_tree_structure(tree_items, max_lines=settings.MAX_TREE_LINES)
    context_parts.append(f"\n{tree_str}\n")
    char_count += len(tree_str) + 2

    # 3. Prioritize and fetch files
    prioritized_files = prioritize_files(tree_items)
    files_fetched = 0

    for file_info in prioritized_files:
        if files_fetched >= settings.MAX_FILES_TO_FETCH:
            break

        if char_count >= max_chars * 0.9:
            break

        path = file_info["path"]

        try:
            content = await fetch_file_content(owner, repo, path, branch)

            if not content or not content.strip():
                continue

            if len(content) > 3000:
                content = content[:3000] + "\n... (truncated)"

            file_section = f"\n--- File: {path} ---\n{content}\n"

            if char_count + len(file_section) > max_chars:
                truncated_content = content[:1000] + "\n... (truncated)"
                file_section = f"\n--- File: {path} ---\n{truncated_content}\n"

                if char_count + len(file_section) > max_chars:
                    break

            context_parts.append(file_section)
            char_count += len(file_section)
            files_fetched += 1

        except Exception:
            continue

    return "".join(context_parts)
