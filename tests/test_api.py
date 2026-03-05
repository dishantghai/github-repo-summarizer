import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test root health check endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "service" in data
    assert "version" in data


def test_health_endpoint():
    """Test detailed health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "llm_configured" in data
    assert "github_token_configured" in data


def test_summarize_invalid_url_format():
    """Test with invalid URL format"""
    response = client.post(
        "/summarize",
        json={"github_url": "https://invalid-url.com/repo"}
    )
    assert response.status_code == 400 or response.status_code == 422


def test_summarize_missing_github_url():
    """Test with missing github_url field"""
    response = client.post("/summarize", json={})
    assert response.status_code == 422


def test_summarize_empty_github_url():
    """Test with empty github_url field"""
    response = client.post("/summarize", json={"github_url": ""})
    assert response.status_code == 422 or response.status_code == 400


@pytest.mark.asyncio
async def test_summarize_valid_repo_mocked():
    """Test with mocked responses for valid repository"""
    mock_metadata = {
        "description": "Test repository",
        "language": "Python",
        "topics": ["test"],
        "default_branch": "main",
        "size": 100,
        "is_private": False,
    }
    
    mock_tree = [
        {"path": "README.md", "type": "blob", "size": 100},
        {"path": "main.py", "type": "blob", "size": 200},
        {"path": "src", "type": "tree", "size": 0},
    ]
    
    mock_llm_result = {
        "summary": "A test repository for demonstration purposes.",
        "technologies": ["Python", "FastAPI"],
        "structure": "Simple project structure with main.py entry point.",
    }
    
    with patch("app.api.routes.fetch_repo_metadata", new_callable=AsyncMock) as mock_meta, \
         patch("app.api.routes.fetch_repo_tree", new_callable=AsyncMock) as mock_tree_func, \
         patch("app.api.routes.build_context", new_callable=AsyncMock) as mock_context, \
         patch("app.api.routes.call_llm", new_callable=AsyncMock) as mock_llm:
        
        mock_meta.return_value = mock_metadata
        mock_tree_func.return_value = mock_tree
        mock_context.return_value = "Test context"
        mock_llm.return_value = mock_llm_result
        
        response = client.post(
            "/summarize",
            json={"github_url": "https://github.com/test/repo"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "technologies" in data
        assert "structure" in data
        assert isinstance(data["technologies"], list)


def test_url_parsing():
    """Test GitHub URL parsing"""
    from app.services.github_service import parse_github_url
    
    # Valid URLs
    owner, repo = parse_github_url("https://github.com/psf/requests")
    assert owner == "psf"
    assert repo == "requests"
    
    owner, repo = parse_github_url("https://github.com/owner/repo-name")
    assert owner == "owner"
    assert repo == "repo-name"
    
    owner, repo = parse_github_url("https://github.com/owner/repo/tree/main")
    assert owner == "owner"
    assert repo == "repo"
    
    # Invalid URLs
    with pytest.raises(ValueError):
        parse_github_url("https://gitlab.com/owner/repo")
    
    with pytest.raises(ValueError):
        parse_github_url("invalid-url")


def test_file_filtering():
    """Test file filtering logic"""
    from app.services.content_processor import should_ignore_file, get_file_priority
    
    # Should be ignored
    assert should_ignore_file("node_modules/package.json") is True
    assert should_ignore_file("package-lock.json") is True
    assert should_ignore_file("yarn.lock") is True
    assert should_ignore_file("image.png") is True
    assert should_ignore_file("dist/bundle.js") is True
    assert should_ignore_file("__pycache__/module.pyc") is True
    
    # Should not be ignored
    assert should_ignore_file("README.md") is False
    assert should_ignore_file("main.py") is False
    assert should_ignore_file("package.json") is False
    assert should_ignore_file("src/app.js") is False


def test_file_prioritization():
    """Test file priority scoring"""
    from app.services.content_processor import get_file_priority
    
    # High priority (1-2)
    assert get_file_priority("README.md") == 1
    assert get_file_priority("package.json") == 2
    assert get_file_priority("pyproject.toml") == 2
    
    # Medium priority (3-6)
    assert get_file_priority("requirements.txt") == 3
    assert get_file_priority("Dockerfile") == 4
    assert get_file_priority("main.py") == 6
    
    # Low priority (999)
    assert get_file_priority("random-file.txt") == 999


def test_llm_response_parsing():
    """Test LLM response parsing"""
    from app.services.llm_service import parse_llm_response
    
    # Valid JSON
    valid_response = '{"summary": "Test", "technologies": ["Python"], "structure": "Simple"}'
    result = parse_llm_response(valid_response)
    assert result["summary"] == "Test"
    assert result["technologies"] == ["Python"]
    assert result["structure"] == "Simple"
    
    # JSON with markdown code block
    markdown_response = '```json\n{"summary": "Test", "technologies": ["Python"], "structure": "Simple"}\n```'
    result = parse_llm_response(markdown_response)
    assert result["summary"] == "Test"
    
    # Invalid JSON
    with pytest.raises(ValueError):
        parse_llm_response("not valid json")
    
    # Missing fields
    with pytest.raises(ValueError):
        parse_llm_response('{"summary": "Test"}')
