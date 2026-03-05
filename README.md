# GitHub Repository Summarizer

API service that analyzes GitHub repositories and generates human-readable summaries using LLMs.

## Features

- **Fast Analysis** - Uses GitHub API directly (no cloning required)
- **LLM-Powered** - Generates summaries using Nebius Token Factory (OpenAI-compatible), with optional OpenAI fallback
- **Smart Filtering** - Automatically ignores binary files, lock files, and dependencies
- **Context Management** - Handles repositories of any size within token limits
- **Secure** - API keys managed via environment variables

## Quick Start

### Prerequisites

- Python 3.10 or higher
- `uv` package manager ([Install uv](https://github.com/astral-sh/uv))
- Nebius Token Factory API key ([Sign up here](https://qrco.de/nebius_academy_token_factory))

### Installation

1. **Clone this repository:**
```bash
git clone https://github.com/dishantghai/github-repo-summarizer.git
cd github-repo-summarizer
```

**Or download the ZIP from GitHub:**
1. On the repository page, click **Code** → **Download ZIP**.
2. Unzip it and `cd` into the extracted folder (e.g., `github-repo-summarizer-main`).

**If you already have the project folder (e.g., from a submitted ZIP):**
Just `cd` into the existing `github-repo-summarizer` directory and continue with the steps below.

2. **Install uv (if not already installed):**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
# Or on Windows: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

3. **Create virtual environment and install dependencies:**
```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```
Alternatively, you can install from `pyproject.toml`:
```bash
uv sync
```

4. **Configure environment variables:**
```bash
cp .env.example .env
```

Edit `.env` and add your Nebius API key:
```
NEBIUS_API_KEY=your_nebius_api_key_here
```

### Running the Server

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Or if virtual environment is already activated:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The server will start at `http://localhost:8000`

## Usage

### API Endpoint

**POST /summarize**

Request:
```bash
curl -X POST http://localhost:8000/summarize \
  -H "Content-Type: application/json" \
  -d '{"github_url": "https://github.com/psf/requests"}'
```

Response:
```json
{
  "summary": "Requests is a popular Python library for making HTTP requests. It provides a simple and elegant API for sending HTTP/1.1 requests with various methods like GET, POST, PUT, DELETE, etc.",
  "technologies": ["Python", "urllib3", "certifi", "idna", "charset_normalizer"],
  "structure": "The project follows a standard Python package layout with the main source code in src/requests/, tests in tests/, and documentation in docs/."
}
```

### Error Responses

```json
{
  "status": "error",
  "message": "Repository not found or is private"
}
```

### Interactive API Documentation

Visit `http://localhost:8000/docs` for Swagger UI documentation.

## Model Choice

**Model:** `meta-llama/Llama-3.3-70B-Instruct`

**Rationale:** This model was chosen for its:
- Strong code understanding and analysis capabilities
- Excellent instruction-following for producing structured JSON output
- Good balance between performance and cost-effectiveness
- Large context window support (up to 128K tokens)

You can override the Nebius model by setting `NEBIUS_MODEL` in `.env`. If `OPENAI_API_KEY` is set and `NEBIUS_API_KEY` is not, the service uses OpenAI as a fallback (default model: `gpt-4o-mini`).

## Repository Processing Strategy

### What Gets Analyzed

The system intelligently selects the most informative files based on priority:

1. **Documentation** (Priority 1): `README.md`, `CONTRIBUTING.md`
2. **Package Configuration** (Priority 2): `package.json`, `pyproject.toml`, `Cargo.toml`, etc.
3. **Dependencies** (Priority 3): `requirements.txt`, `Pipfile`
4. **Infrastructure** (Priority 4): `Dockerfile`, CI/CD configs, `Makefile`
5. **Configuration** (Priority 5): `.env.example`, `tsconfig.json`, `webpack.config.js`
6. **Entry Points** (Priority 6): `main.py`, `index.js`, `app.py`
7. **Source Files** (Priority 7): Files in `src/`, `lib/`, `app/` directories

### What Gets Excluded

The following are automatically filtered out to save context space:

- **Binary files**: Images, videos, fonts, executables
- **Lock files**: `package-lock.json`, `yarn.lock`, `Pipfile.lock`, `poetry.lock`
- **Dependencies**: `node_modules/`, `vendor/`, `.venv/`
- **Build artifacts**: `dist/`, `build/`, `target/`
- **Minified files**: `*.min.js`, `*.min.css`, `*.map`
- **Cache directories**: `__pycache__/`, `.pytest_cache/`, `.mypy_cache/`

### Context Management

- **Token Budget**: ~12,000 tokens maximum to fit LLM context limits
- **File Limits**: Maximum 15 files analyzed per repository
- **Smart Truncation**: Large files are truncated at 3,000 characters; additional truncation may occur when nearing the token budget
- **Tree Structure**: Directory tree limited to 100 lines for overview

Note: Large repositories are sampled within these limits rather than fully analyzed.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `NEBIUS_API_KEY` | Yes* | API key from Nebius Token Factory |
| `NEBIUS_MODEL` | No | Override Nebius model name |
| `OPENAI_API_KEY` | No | Alternative: OpenAI API key |
| `GITHUB_TOKEN` | No | GitHub PAT for higher rate limits (5000/hr vs 60/hr) |

*Either `NEBIUS_API_KEY` or `OPENAI_API_KEY` is required.

## Error Handling

The API returns appropriate HTTP status codes:

| Status | Description |
|--------|-------------|
| `200` | Success - summary generated |
| `400` | Invalid request (bad URL format, empty repository) |
| `404` | Repository not found or is private |
| `422` | Validation error (missing or invalid fields) |
| `502` | LLM service error |
| `503` | Service unavailable (GitHub rate limit) |
| `504` | Request timeout |

## Development

### Running Tests

```bash
pytest tests/ -v
```

Additional scripts:
- `test_manual.py` runs a live GitHub API integration check (requires network access).
- `test_models.py` probes Nebius model names (requires a valid `NEBIUS_API_KEY`).

### Project Structure

```
github-repo-summarizer/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration and environment variables
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py        # POST /summarize endpoint
│   ├── services/
│   │   ├── __init__.py
│   │   ├── github_service.py    # GitHub API interactions
│   │   ├── content_processor.py # File filtering and context building
│   │   └── llm_service.py       # Nebius/LLM API integration
│   └── models/
│       ├── __init__.py
│       └── schemas.py       # Pydantic request/response models
├── tests/
│   ├── __init__.py
│   └── test_api.py          # API and unit tests
├── pyproject.toml           # Project configuration
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variable template
├── .gitignore
└── README.md
```

## Health Endpoints

- `GET /` basic service status
- `GET /health` LLM/GitHub token configuration status

## License

MIT

## Support

For issues or questions, contact: support.academy@nebius.com
