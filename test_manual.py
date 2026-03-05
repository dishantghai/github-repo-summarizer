#!/usr/bin/env python3
"""
Manual test script to verify the GitHub Repository Summarizer implementation.
This script tests various scenarios to ensure all evaluation criteria are met.
"""

import asyncio
import sys
from app.services.github_service import (
    parse_github_url,
    fetch_repo_metadata,
    fetch_repo_tree,
)
from app.services.content_processor import (
    build_context,
    prioritize_files,
    should_ignore_file,
)
from app.config import settings


async def test_github_api():
    """Test GitHub API integration without LLM"""
    print("=" * 80)
    print("Testing GitHub API Integration")
    print("=" * 80)
    
    test_repos = [
        "https://github.com/psf/requests",
        "https://github.com/pallets/flask",
    ]
    
    for repo_url in test_repos:
        print(f"\n📦 Testing: {repo_url}")
        
        try:
            # Parse URL
            owner, repo = parse_github_url(repo_url)
            print(f"  ✓ Parsed: {owner}/{repo}")
            
            # Fetch metadata
            metadata = await fetch_repo_metadata(owner, repo)
            print(f"  ✓ Language: {metadata['language']}")
            print(f"  ✓ Description: {metadata['description'][:80]}...")
            print(f"  ✓ Default branch: {metadata['default_branch']}")
            
            # Fetch tree
            tree_items = await fetch_repo_tree(owner, repo, metadata['default_branch'])
            print(f"  ✓ Tree items: {len(tree_items)}")
            
            # Prioritize files
            prioritized = prioritize_files(tree_items)
            print(f"  ✓ Prioritized files: {len(prioritized)}")
            
            # Show top 5 priority files
            print("  📄 Top priority files:")
            for i, file in enumerate(prioritized[:5]):
                print(f"     {i+1}. {file['path']} (priority: {file['priority']})")
            
            # Build context
            context = await build_context(
                owner, repo, metadata['default_branch'], tree_items, metadata
            )
            print(f"  ✓ Context built: {len(context)} characters")
            print(f"  ✓ Estimated tokens: ~{len(context) // 4}")
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            return False
    
    return True


def test_file_filtering():
    """Test file filtering logic"""
    print("\n" + "=" * 80)
    print("Testing File Filtering Logic")
    print("=" * 80)
    
    test_cases = [
        # Should be ignored
        ("node_modules/package.json", True),
        ("package-lock.json", True),
        ("yarn.lock", True),
        ("dist/bundle.js", True),
        ("image.png", True),
        ("__pycache__/module.pyc", True),
        (".venv/lib/python.py", True),
        ("build/output.js", True),
        
        # Should NOT be ignored
        ("README.md", False),
        ("package.json", False),
        ("src/main.py", False),
        ("requirements.txt", False),
        ("Dockerfile", False),
    ]
    
    all_passed = True
    for path, should_ignore in test_cases:
        result = should_ignore_file(path)
        status = "✓" if result == should_ignore else "✗"
        if result != should_ignore:
            all_passed = False
        print(f"  {status} {path}: {'ignored' if result else 'included'}")
    
    return all_passed


def test_configuration():
    """Test configuration and environment setup"""
    print("\n" + "=" * 80)
    print("Testing Configuration")
    print("=" * 80)
    
    print(f"  API Key configured: {'✓' if settings.NEBIUS_API_KEY else '✗'}")
    print(f"  GitHub token: {'✓' if settings.GITHUB_TOKEN else '○ (optional)'}")
    print(f"  Max context tokens: {settings.MAX_CONTEXT_TOKENS}")
    print(f"  Max files to fetch: {settings.MAX_FILES_TO_FETCH}")
    print(f"  Model: {settings.NEBIUS_MODEL}")
    
    if not settings.NEBIUS_API_KEY and not settings.OPENAI_API_KEY:
        print("\n  ⚠️  Warning: No LLM API key configured!")
        print("     Set NEBIUS_API_KEY in .env file to test LLM integration")
        return False
    
    return True


async def main():
    """Run all tests"""
    print("\n🚀 GitHub Repository Summarizer - Manual Test Suite\n")
    
    results = {
        "Configuration": test_configuration(),
        "File Filtering": test_file_filtering(),
    }
    
    # Only test GitHub API if configuration is valid
    if results["Configuration"]:
        results["GitHub API"] = await test_github_api()
    else:
        results["GitHub API"] = None
    
    # Print summary
    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)
    
    for test_name, result in results.items():
        if result is None:
            status = "⊘ SKIPPED"
        elif result:
            status = "✓ PASSED"
        else:
            status = "✗ FAILED"
        print(f"  {status}: {test_name}")
    
    # Overall result
    passed = all(r for r in results.values() if r is not None)
    print("\n" + "=" * 80)
    if passed:
        print("✅ All tests PASSED!")
    else:
        print("❌ Some tests FAILED")
    print("=" * 80 + "\n")
    
    return 0 if passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
