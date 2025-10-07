"""Recommendation agent that combines LLM and GitHub analysis."""

from typing import List, Dict, Any
from .package_analyzer import PackageAnalyzerAgent
from .github_researcher import GitHubResearchAgent
from ..mcp_servers.pypi_server import PyPIMCPServer


class RecommenderAgent:
    """Agent that combines multiple sources to make package recommendations."""

    def __init__(
        self,
        groq_api_key: str,
        github_token: str = None,
        model_name: str = "llama-3.3-70b-versatile"
    ):
        self.name = "RecommenderAgent"
        self.package_analyzer = PackageAnalyzerAgent(groq_api_key, model_name)
        self.github_researcher = GitHubResearchAgent(github_token)
        self.pypi_server = PyPIMCPServer()

    def generate_recommendations(
        self,
        user_packages: List[str],
        project_description: str = None
    ) -> Dict[str, Any]:
        """
        Generate package recommendations combining LLM and GitHub analysis.

        Args:
            user_packages: List of packages specified by user
            project_description: Optional project description

        Returns:
            Dictionary with comprehensive recommendations
        """
        github_packages = []

        # Only do GitHub research if project description is provided
        if project_description and project_description.strip():
            github_result = self.github_researcher.research_similar_projects(
                project_description=project_description,
                max_repos=5
            )

            if github_result["success"]:
                github_packages = [pkg["package"] for pkg in github_result["packages"]]

        # Analyze with LLM
        llm_analysis = self.package_analyzer.analyze_with_llm(
            user_packages=user_packages,
            project_description=project_description or "",
            github_packages=github_packages
        )

        if not llm_analysis["success"]:
            # Fallback: just use user packages
            return {
                "success": True,
                "final_packages": user_packages,
                "has_suggestions": False,
                "approved_packages": user_packages,
                "alternatives": {},
                "additional": {},
                "error": llm_analysis.get("error")
            }

        # Parse LLM recommendations
        parsed = self.package_analyzer.parse_llm_recommendations(
            llm_response=llm_analysis["analysis"],
            user_packages=user_packages
        )

        # Check if there are any actual suggestions
        has_alternatives = len(parsed["alternative_suggestions"]) > 0
        has_additional = len(parsed["additional_packages"]) > 0
        has_suggestions = has_alternatives or has_additional

        # If no suggestions, just return user packages
        if not has_suggestions:
            return {
                "success": True,
                "final_packages": user_packages,
                "has_suggestions": False,
                "approved_packages": user_packages,
                "alternatives": {},
                "additional": {},
                "message": "No better alternatives found. Proceeding with your packages."
            }

        # Get descriptions for suggested packages
        all_suggested_packages = []

        # Collect alternative packages
        for alt_info in parsed["alternative_suggestions"].values():
            all_suggested_packages.append(alt_info["alternative"])

        # Collect additional packages
        all_suggested_packages.extend(parsed["additional_packages"].keys())

        # Fetch descriptions
        descriptions = self.package_analyzer.get_package_descriptions(all_suggested_packages)

        # Build structured response
        alternatives_with_desc = {}
        for original, alt_info in parsed["alternative_suggestions"].items():
            alt_pkg = alt_info["alternative"]
            alternatives_with_desc[original] = {
                "alternative": alt_pkg,
                "reason": alt_info["reason"],
                "description": descriptions.get(alt_pkg, "No description available")
            }

        additional_with_desc = {}
        for pkg, reason in parsed["additional_packages"].items():
            additional_with_desc[pkg] = {
                "reason": reason,
                "description": descriptions.get(pkg, "No description available")
            }

        return {
            "success": True,
            "has_suggestions": True,
            "approved_packages": parsed["approved_packages"],
            "alternatives": alternatives_with_desc,
            "additional": additional_with_desc,
            "github_insights": {
                "packages_found": github_packages[:5] if github_packages else [],
                "repos_analyzed": github_result.get("repos_analyzed", 0) if project_description else 0
            }
        }

    def build_final_package_list(
        self,
        recommendations: Dict[str, Any],
        user_choices: Dict[str, bool]
    ) -> List[str]:
        """
        Build final package list based on user choices.

        Args:
            recommendations: Output from generate_recommendations
            user_choices: Dictionary mapping package names to user's choice (True/False)

        Returns:
            List of final packages to install
        """
        final_packages = []

        # Add approved packages (no changes)
        final_packages.extend(recommendations["approved_packages"])

        # Handle alternatives
        for original, alt_info in recommendations["alternatives"].items():
            alt_pkg = alt_info["alternative"]
            # Check if user chose the alternative
            if user_choices.get(alt_pkg, False):
                final_packages.append(alt_pkg)
            else:
                # Keep original
                if original not in final_packages:
                    final_packages.append(original)

        # Handle additional packages
        for pkg in recommendations["additional"].keys():
            if user_choices.get(pkg, False):
                final_packages.append(pkg)

        # Remove duplicates while preserving order
        seen = set()
        unique_packages = []
        for pkg in final_packages:
            if pkg not in seen:
                seen.add(pkg)
                unique_packages.append(pkg)

        return unique_packages
