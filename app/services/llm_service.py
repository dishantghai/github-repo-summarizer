import json
import re
from openai import AsyncOpenAI
from app.config import settings

SYSTEM_PROMPT = """You are a technical analyst specializing in code repository analysis. 
Your task is to analyze GitHub repositories and provide structured summaries.
Always respond with valid JSON only, no additional text or markdown formatting."""


def build_prompt(context: str) -> str:
    """
    Build the prompt for LLM analysis.
    
    Returns:
        Formatted prompt string
    """
    prompt = f"""Analyze this GitHub repository and provide a structured summary.

REPOSITORY CONTENTS:
{context}

Respond in this exact JSON format:
{{
  "summary": "A clear 2-3 sentence description of what this project does and its purpose",
  "technologies": ["list", "of", "main", "technologies", "frameworks", "languages"],
  "structure": "Brief description of how the project is organized (main directories and their purposes)"
}}

Rules:
- summary: Focus on WHAT the project does, not HOW it works internally. Be concise but informative.
- technologies: Include programming languages, frameworks, key libraries (max 10 items, most important first)
- structure: Describe the directory layout and organization concisely (2-3 sentences)
- Return ONLY valid JSON, no markdown formatting, no code blocks, no extra text

Respond now with only the JSON:"""

    return prompt


def parse_llm_response(response_text: str) -> dict:
    """
    Parse LLM response and extract JSON.
    
    Handles:
    - Plain JSON
    - JSON wrapped in markdown code blocks
    - Malformed responses
    
    Returns:
        Dict with summary, technologies, structure
    """
    # Remove markdown code blocks if present
    response_text = re.sub(r"^```json\s*", "", response_text.strip())
    response_text = re.sub(r"^```\s*", "", response_text)
    response_text = re.sub(r"\s*```$", "", response_text)
    response_text = response_text.strip()

    # Try to find JSON object in the response
    json_match = re.search(r"\{[\s\S]*\}", response_text)
    if json_match:
        response_text = json_match.group()

    try:
        data = json.loads(response_text)

        # Validate required fields
        required_fields = ["summary", "technologies", "structure"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

        # Validate types
        if not isinstance(data["summary"], str):
            raise ValueError("summary must be a string")
        if not isinstance(data["technologies"], list):
            # Try to convert if it's a string
            if isinstance(data["technologies"], str):
                data["technologies"] = [t.strip() for t in data["technologies"].split(",")]
            else:
                raise ValueError("technologies must be a list")
        if not isinstance(data["structure"], str):
            raise ValueError("structure must be a string")

        # Ensure technologies are strings and non-empty
        data["technologies"] = [str(tech).strip() for tech in data["technologies"] if tech]

        # Ensure summary and structure are non-empty
        if not data["summary"].strip():
            data["summary"] = "No summary available"
        if not data["structure"].strip():
            data["structure"] = "Standard project structure"

        return data

    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON response: {str(e)}")


async def call_llm(context: str) -> dict:
    """
    Call Nebius Token Factory API (OpenAI-compatible) with context.
    
    Returns:
        Parsed JSON response with summary, technologies, structure
    """
    # Determine which API to use
    if settings.NEBIUS_API_KEY:
        api_key = settings.NEBIUS_API_KEY
        base_url = settings.NEBIUS_BASE_URL
        model = settings.NEBIUS_MODEL
    elif settings.OPENAI_API_KEY:
        api_key = settings.OPENAI_API_KEY
        base_url = "https://api.openai.com/v1"
        model = "gpt-4o-mini"
    else:
        raise ValueError("No LLM API key configured. Set NEBIUS_API_KEY or OPENAI_API_KEY")

    client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    prompt = build_prompt(context)

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=1000,
        )

        response_text = response.choices[0].message.content.strip()

        parsed_response = parse_llm_response(response_text)

        return parsed_response

    except Exception as e:
        error_msg = str(e)
        if "rate limit" in error_msg.lower():
            raise ValueError("LLM API rate limit exceeded. Try again later.")
        elif "timeout" in error_msg.lower():
            raise ValueError("LLM request timeout. Try again.")
        elif "authentication" in error_msg.lower() or "api key" in error_msg.lower():
            raise ValueError("LLM API authentication failed. Check your API key.")
        else:
            raise ValueError(f"LLM API call failed: {error_msg}")
