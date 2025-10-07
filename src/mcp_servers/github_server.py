"""GitHub MCP Server for searching repositories and analyzing dependencies."""

import os
import requests
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class GitHubRepo:
    """Represents a GitHub repository."""
    name: str
    full_name: str
    description: Optional[str]
    stars: int
    url: str


class GitHubMCPServer:
    """MCP Server for interacting with GitHub API."""

    def __init__(self, github_token: Optional[str] = None):
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
        }
        if self.github_token:
            self.headers["Authorization"] = f"token {self.github_token}"

    def search_repositories(
        self,
        query: str,
        language: str = "Python",
        max_results: int = 10
    ) -> List[GitHubRepo]:
        """
        Search GitHub repositories based on query and language.

        Args:
            query: Search query (e.g., "machine learning web scraper")
            language: Programming language filter
            max_results: Maximum number of results to return

        Returns:
            List of GitHubRepo objects
        """
        search_query = f"{query} language:{language}"
        url = f"{self.base_url}/search/repositories"
        params = {
            "q": search_query,
            "sort": "stars",
            "order": "desc",
            "per_page": max_results
        }

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            repos = []
            for item in data.get("items", []):
                repo = GitHubRepo(
                    name=item["name"],
                    full_name=item["full_name"],
                    description=item.get("description"),
                    stars=item["stargazers_count"],
                    url=item["html_url"]
                )
                repos.append(repo)

            return repos
        except Exception as e:
            print(f"Error searching repositories: {e}")
            return []

    def get_requirements_file(self, repo_full_name: str) -> Optional[str]:
        """
        Fetch requirements.txt content from a repository.

        Args:
            repo_full_name: Full repository name (e.g., "owner/repo")

        Returns:
            Content of requirements.txt or None if not found
        """
        # Try common dependency file locations
        file_paths = [
            "requirements.txt",
            "requirements/requirements.txt",
            "requirements/base.txt",
            "requirements/production.txt"
        ]

        for file_path in file_paths:
            url = f"{self.base_url}/repos/{repo_full_name}/contents/{file_path}"
            try:
                response = requests.get(url, headers=self.headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    # GitHub returns base64 encoded content
                    import base64
                    content = base64.b64decode(data["content"]).decode("utf-8")
                    return content
            except Exception:
                continue

        return None

    def get_pyproject_toml(self, repo_full_name: str) -> Optional[str]:
        """
        Fetch pyproject.toml content from a repository.

        Args:
            repo_full_name: Full repository name (e.g., "owner/repo")

        Returns:
            Content of pyproject.toml or None if not found
        """
        url = f"{self.base_url}/repos/{repo_full_name}/contents/pyproject.toml"

        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                import base64
                content = base64.b64decode(data["content"]).decode("utf-8")
                return content
        except Exception:
            pass

        return None

    def analyze_repo_dependencies(self, repo_full_name: str) -> Dict[str, Any]:
        """
        Analyze dependencies from a GitHub repository.

        Args:
            repo_full_name: Full repository name (e.g., "owner/repo")

        Returns:
            Dictionary containing parsed dependencies
        """
        dependencies = {
            "requirements_txt": [],
            "pyproject_toml": [],
            "source": repo_full_name
        }

        # Try requirements.txt
        requirements = self.get_requirements_file(repo_full_name)
        if requirements:
            # Parse requirements.txt
            for line in requirements.splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    # Extract package name (before ==, >=, etc.)
                    package = line.split("==")[0].split(">=")[0].split("<=")[0].split("~=")[0].strip()
                    if package:
                        dependencies["requirements_txt"].append(package)

        # Try pyproject.toml
        pyproject = self.get_pyproject_toml(repo_full_name)
        if pyproject:
            # Simple parsing for dependencies in pyproject.toml
            import re
            # Look for dependencies array
            deps_match = re.search(r'dependencies\s*=\s*\[(.*?)\]', pyproject, re.DOTALL)
            if deps_match:
                deps_str = deps_match.group(1)
                # Extract package names from quoted strings
                packages = re.findall(r'"([^">=<~\s]+)', deps_str)
                dependencies["pyproject_toml"].extend(packages)

        return dependencies

    def get_popular_packages_from_repos(
        self,
        repos: List[GitHubRepo],
        top_n: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Analyze multiple repositories and return most popular packages.

        Args:
            repos: List of GitHubRepo objects to analyze
            top_n: Number of top packages to return

        Returns:
            List of dictionaries with package names and occurrence counts
        """
        package_count = {}

        for repo in repos:
            deps = self.analyze_repo_dependencies(repo.full_name)
            all_packages = set(deps["requirements_txt"] + deps["pyproject_toml"])

            for package in all_packages:
                package_count[package] = package_count.get(package, 0) + 1

        # Sort by occurrence count
        sorted_packages = sorted(
            package_count.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_n]

        return [
            {"package": pkg, "occurrences": count}
            for pkg, count in sorted_packages
        ]
