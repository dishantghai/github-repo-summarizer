#!/usr/bin/env python3
"""
Test script to find the correct Nebius model name.
"""

import asyncio
import os
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

# Common model name variations to try
MODEL_VARIATIONS = [
    "meta-llama/Llama-3.3-70B-Instruct",
    "meta-llama/Llama-3.1-70B-Instruct",
    "meta-llama/Meta-Llama-3.1-70B-Instruct",
    "meta-llama/Llama-3-70B-Instruct",
    "Llama-3.3-70B-Instruct",
    "Llama-3.1-70B-Instruct",
    "llama-3.3-70b-instruct",
    "llama-3.1-70b-instruct",
]


async def test_model(model_name: str, api_key: str) -> bool:
    """Test if a model name works"""
    client = AsyncOpenAI(
        api_key=api_key,
        base_url="https://api.studio.nebius.com/v1"
    )
    
    try:
        response = await client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "user", "content": "Say 'test' in JSON format: {\"result\": \"test\"}"}
            ],
            max_tokens=50,
            timeout=10
        )
        return True
    except Exception as e:
        error_str = str(e)
        if "404" in error_str or "does not exist" in error_str:
            return False
        elif "401" in error_str or "authentication" in error_str.lower():
            print(f"⚠️  Authentication error - check your API key")
            return None
        else:
            print(f"⚠️  Error with {model_name}: {e}")
            return None


async def main():
    api_key = os.getenv("NEBIUS_API_KEY")
    
    if not api_key or api_key == "placeholder_key_for_testing":
        print("❌ Please set a valid NEBIUS_API_KEY in .env file")
        return
    
    print("🔍 Testing Nebius model names...\n")
    
    for model in MODEL_VARIATIONS:
        print(f"Testing: {model}...", end=" ")
        result = await test_model(model, api_key)
        
        if result is True:
            print(f"✅ WORKS!")
            print(f"\n🎯 Use this model: {model}")
            print(f"\nAdd to your .env file:")
            print(f"NEBIUS_MODEL={model}")
            return
        elif result is False:
            print("❌ Not found")
        else:
            print("⚠️  Error (see above)")
    
    print("\n❌ None of the common model names worked.")
    print("\nPlease check Nebius documentation for available models:")
    print("https://docs.nebius.com/ or your Nebius dashboard")


if __name__ == "__main__":
    asyncio.run(main())
