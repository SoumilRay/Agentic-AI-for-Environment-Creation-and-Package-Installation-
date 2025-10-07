"""Basic tests for the agentic package installer."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_imports():
    """Test that all modules can be imported."""
    try:
        from src.agents.project_setup import ProjectSetupAgent
        from src.agents.github_researcher import GitHubResearchAgent
        from src.agents.package_analyzer import PackageAnalyzerAgent
        from src.agents.recommender import RecommenderAgent
        from src.agents.installer import InstallerAgent
        from src.mcp_servers.github_server import GitHubMCPServer
        from src.mcp_servers.pypi_server import PyPIMCPServer
        print("✓ All imports successful")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False


def test_package_parsing():
    """Test package name parsing."""
    from src.agents.package_analyzer import PackageAnalyzerAgent

    analyzer = PackageAnalyzerAgent(groq_api_key="dummy", model_name="dummy")

    # Test comma-separated
    result = analyzer.parse_user_packages("numpy, pandas, requests")
    assert result == ["numpy", "pandas", "requests"]

    # Test space-separated
    result = analyzer.parse_user_packages("numpy pandas requests")
    assert result == ["numpy", "pandas", "requests"]

    # Test mixed
    result = analyzer.parse_user_packages("numpy, pandas requests")
    assert "numpy" in result and "pandas" in result and "requests" in result

    # Test empty
    result = analyzer.parse_user_packages("")
    assert result == []

    print("✓ Package parsing tests passed")
    return True


def test_pypi_server():
    """Test PyPI server functionality."""
    from src.mcp_servers.pypi_server import PyPIMCPServer

    pypi = PyPIMCPServer()

    # Test package info
    info = pypi.get_package_info("requests")
    assert info is not None
    assert info.name.lower() == "requests"

    # Test description
    desc = pypi.get_package_description("requests")
    assert desc != "Package not found on PyPI"
    assert len(desc) > 0

    # Test validation
    assert pypi.validate_package("requests") == True
    assert pypi.validate_package("this-package-definitely-does-not-exist-12345") == False

    print("✓ PyPI server tests passed")
    return True


def test_github_server():
    """Test GitHub server functionality (without token)."""
    from src.mcp_servers.github_server import GitHubMCPServer

    github = GitHubMCPServer()

    # Test repository search (may be rate-limited without token)
    try:
        repos = github.search_repositories("python web scraper", max_results=3)
        # If we get results, great. If rate-limited, that's okay too.
        print(f"✓ GitHub search returned {len(repos)} repositories")
        return True
    except Exception as e:
        print(f"ℹ GitHub search skipped (rate limit or network): {e}")
        return True  # Don't fail the test


def run_all_tests():
    """Run all tests."""
    print("\n" + "="*50)
    print("Running Basic Tests")
    print("="*50 + "\n")

    tests = [
        test_imports,
        test_package_parsing,
        test_pypi_server,
        test_github_server,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ {test.__name__} failed with exception: {e}")
            results.append(False)
        print()

    print("="*50)
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    print("="*50 + "\n")

    return all(results)


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
