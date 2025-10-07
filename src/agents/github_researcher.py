"""GitHub research agent for analyzing similar repositories."""

from typing import List, Dict, Any
from ..mcp_servers.github_server import GitHubMCPServer


class GitHubResearchAgent:
    """Agent that researches GitHub repositories for package insights."""

    def __init__(self, github_token: str = None):
        self.name = "GitHubResearchAgent"
        self.github_server = GitHubMCPServer(github_token)

    def research_similar_projects(
        self,
        project_description: str,
        max_repos: int = 5
    ) -> Dict[str, Any]:
        """
        Research similar GitHub projects and analyze their dependencies.

        Args:
            project_description: Description of the user's project
            max_repos: Maximum number of repositories to analyze

        Returns:
            Dictionary with popular packages and analysis
        """
        try:
            # Search for similar repositories
            repos = self.github_server.search_repositories(
                query=project_description,
                language="Python",
                max_results=max_repos
            )

            if not repos:
                return {
                    "success": False,
                    "error": "No similar repositories found",
                    "packages": [],
                    "repos_analyzed": 0
                }

            # Analyze popular packages from these repositories
            popular_packages = self.github_server.get_popular_packages_from_repos(
                repos=repos,
                top_n=15
            )

            # Filter out common base packages that are usually already handled
            common_base = {"pip", "setuptools", "wheel", "python"}
            filtered_packages = [
                pkg for pkg in popular_packages
                if pkg["package"].lower() not in common_base
            ]

            return {
                "success": True,
                "packages": filtered_packages,
                "repos_analyzed": len(repos),
                "sample_repos": [
                    {
                        "name": repo.name,
                        "stars": repo.stars,
                        "description": repo.description
                    }
                    for repo in repos[:3]
                ],
                "message": f"Analyzed {len(repos)} similar repositories"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to research GitHub projects: {str(e)}",
                "packages": [],
                "repos_analyzed": 0
            }

    def get_packages_from_description(
        self,
        project_description: str
    ) -> List[str]:
        """
        Extract potential package names from similar GitHub projects.

        Args:
            project_description: Description of the user's project

        Returns:
            List of package names
        """
        result = self.research_similar_projects(project_description)

        if result["success"]:
            return [pkg["package"] for pkg in result["packages"]]
        return []
