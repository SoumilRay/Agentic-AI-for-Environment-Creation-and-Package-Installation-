"""Package analysis agent using LLM for intelligent recommendations."""

from typing import List, Dict, Any, Optional
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from ..mcp_servers.pypi_server import PyPIMCPServer


class PackageAnalyzerAgent:
    """Agent that analyzes packages and makes intelligent recommendations."""

    def __init__(self, groq_api_key: str = "dummy", model_name: str = "llama-3.3-70b-versatile"):
        self.name = "PackageAnalyzerAgent"
        self.llm = ChatGroq(
            groq_api_key=groq_api_key,
            model_name=model_name,
            temperature=0.3
        )
        self.pypi_server = PyPIMCPServer()

    def parse_user_packages(self, user_input: str) -> List[str]:
        """
        Parse package names from user input.

        Args:
            user_input: User's package list (comma-separated or space-separated)

        Returns:
            List of package names
        """
        if not user_input or user_input.strip() == "":
            return []

        # Split by commas or spaces
        packages = []
        for item in user_input.replace(",", " ").split():
            item = item.strip()
            if item:
                packages.append(item)

        return packages

    def analyze_with_llm(
        self,
        user_packages: List[str],
        project_description: str,
        github_packages: List[str]
    ) -> Dict[str, Any]:
        """
        Use LLM to analyze packages and suggest better alternatives if they exist.

        Args:
            user_packages: Packages mentioned by user
            project_description: Description of the project
            github_packages: Popular packages from GitHub research

        Returns:
            Dictionary with analysis and suggestions
        """
        try:
            system_prompt = """You are a Python package expert. Your job is to analyze a user's package requirements and ONLY suggest better alternatives if there are genuinely superior options.

Rules:
1. Do NOT suggest alternatives just for the sake of suggesting - only if there's a clear benefit
2. Consider: popularity, maintenance, performance, ease of use, and project fit
3. Be conservative - if the user's choice is reasonable, approve it
4. If suggesting alternatives, provide a brief (1-2 sentence) reason why
5. Each package name MUST be a single, valid PyPI package name - never use "or", "and", or list multiple packages together
6. Return your response in this EXACT format:

APPROVE: package1, package2
SUGGEST_ALTERNATIVES:
- package3: Better alternative is alternative_name because [brief reason]
ADDITIONAL:
- new_package: [brief reason why it's useful for this project]
- another_package: [brief reason]

IMPORTANT: Each line under ADDITIONAL must have exactly ONE package name, not multiple packages separated by "or" or "and".

If no alternatives or additions are needed, just list all packages under APPROVE."""

            user_prompt = f"""Project Description: {project_description if project_description else "Not provided"}

User's Requested Packages: {", ".join(user_packages) if user_packages else "None specified"}

Popular packages from similar GitHub projects: {", ".join(github_packages[:10]) if github_packages else "None found"}

Analyze the user's package choices and provide recommendations following the rules."""

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]

            response = self.llm.invoke(messages)
            return {
                "success": True,
                "analysis": response.content,
                "raw_response": response.content
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"LLM analysis failed: {str(e)}",
                "analysis": ""
            }

    def parse_llm_recommendations(
        self,
        llm_response: str,
        user_packages: List[str]
    ) -> Dict[str, Any]:
        """
        Parse LLM recommendations into structured format.

        Args:
            llm_response: Raw LLM response
            user_packages: Original user packages

        Returns:
            Dictionary with approved, alternatives, and additional packages
        """
        approved = []
        alternatives = {}
        additional = {}

        lines = llm_response.split("\n")
        current_section = None

        for line in lines:
            line = line.strip()

            if line.startswith("APPROVE:"):
                current_section = "approve"
                # Extract packages after "APPROVE:"
                packages_str = line.replace("APPROVE:", "").strip()
                if packages_str:
                    approved.extend([p.strip() for p in packages_str.split(",") if p.strip()])

            elif line.startswith("SUGGEST_ALTERNATIVES:"):
                current_section = "alternatives"

            elif line.startswith("ADDITIONAL:"):
                current_section = "additional"

            elif line.startswith("-") and line[1:].strip():
                content = line[1:].strip()

                if current_section == "alternatives":
                    # Parse format: "package: Better alternative is alt_name because reason"
                    if ":" in content:
                        parts = content.split(":", 1)
                        original_pkg = parts[0].strip()
                        reason = parts[1].strip()

                        # Extract alternative package name
                        if "Better alternative is" in reason:
                            alt_pkg = reason.split("Better alternative is")[1].split("because")[0].strip()
                            reason_text = reason.split("because")[1].strip() if "because" in reason else reason
                            alternatives[original_pkg] = {
                                "alternative": alt_pkg,
                                "reason": reason_text
                            }

                elif current_section == "additional":
                    # Parse format: "package_name: reason"
                    if ":" in content:
                        parts = content.split(":", 1)
                        pkg_name = parts[0].strip()
                        reason = parts[1].strip()

                        # Validate package name - reject if it contains "or", "and", or multiple words
                        if " or " in pkg_name.lower() or " and " in pkg_name.lower():
                            # Skip invalid package names with "or"/"and"
                            continue

                        # Only accept single-word package names (with hyphens/underscores allowed)
                        if " " in pkg_name:
                            # Skip multi-word package names
                            continue

                        additional[pkg_name] = reason

        # If no explicit structure found, assume all user packages are approved
        if not approved and not alternatives and not additional:
            approved = user_packages.copy()

        return {
            "approved_packages": approved,
            "alternative_suggestions": alternatives,
            "additional_packages": additional
        }

    def get_package_descriptions(self, packages: List[str]) -> Dict[str, str]:
        """
        Get descriptions for a list of packages from PyPI.

        Args:
            packages: List of package names

        Returns:
            Dictionary mapping package names to descriptions
        """
        descriptions = {}
        for package in packages:
            desc = self.pypi_server.get_package_description(package)
            descriptions[package] = desc
        return descriptions
