"""PyPI MCP Server for fetching package information."""

import requests
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class PackageInfo:
    """Represents PyPI package information."""
    name: str
    version: str
    summary: str
    description: str
    author: str
    home_page: str
    license: str


class PyPIMCPServer:
    """MCP Server for interacting with PyPI API."""

    def __init__(self):
        self.base_url = "https://pypi.org/pypi"

    def get_package_info(self, package_name: str) -> Optional[PackageInfo]:
        """
        Fetch package information from PyPI.

        Args:
            package_name: Name of the package

        Returns:
            PackageInfo object or None if not found
        """
        url = f"{self.base_url}/{package_name}/json"

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            info = data.get("info", {})
            package_info = PackageInfo(
                name=info.get("name", package_name),
                version=info.get("version", ""),
                summary=info.get("summary", ""),
                description=info.get("description", "")[:500],  # Limit description length
                author=info.get("author", ""),
                home_page=info.get("home_page", ""),
                license=info.get("license", "")
            )

            return package_info
        except Exception as e:
            # Silently fail - package doesn't exist on PyPI
            return None

    def get_latest_stable_version(self, package_name: str) -> Optional[str]:
        """
        Get the latest stable version of a package.

        Args:
            package_name: Name of the package

        Returns:
            Version string or None if not found
        """
        url = f"{self.base_url}/{package_name}/json"

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Get the latest non-pre-release version
            version = data.get("info", {}).get("version", "")
            return version
        except Exception as e:
            print(f"Error fetching version for {package_name}: {e}")
            return None

    def search_packages(self, query: str, max_results: int = 5) -> list[Dict[str, str]]:
        """
        Search for packages on PyPI.

        Args:
            query: Search query
            max_results: Maximum number of results

        Returns:
            List of package dictionaries with name and description
        """
        # Note: PyPI removed their search API, so we'll use a simple approach
        # For a production system, consider using alternatives like:
        # - PyPI's XML-RPC API
        # - Third-party search services
        # - Scraping the search page (not recommended)

        # For now, return empty list as PyPI search API is deprecated
        # In a real implementation, you might use warehouse search or alternatives
        return []

    def get_package_description(self, package_name: str) -> str:
        """
        Get a concise description of a package.

        Args:
            package_name: Name of the package

        Returns:
            Package summary/description
        """
        package_info = self.get_package_info(package_name)
        if package_info:
            # Return summary if available, otherwise truncated description
            if package_info.summary:
                return package_info.summary
            elif package_info.description:
                # Return first 200 chars of description
                desc = package_info.description.replace("\n", " ").strip()
                return desc[:200] + "..." if len(desc) > 200 else desc
            else:
                return "No description available"
        return "Package not found on PyPI"

    def validate_package(self, package_name: str) -> bool:
        """
        Check if a package exists on PyPI.

        Args:
            package_name: Name of the package

        Returns:
            True if package exists, False otherwise
        """
        url = f"{self.base_url}/{package_name}/json"

        try:
            response = requests.get(url, timeout=10)
            return response.status_code == 200
        except Exception:
            return False

    def get_multiple_package_info(
        self,
        package_names: list[str]
    ) -> Dict[str, Optional[PackageInfo]]:
        """
        Fetch information for multiple packages.

        Args:
            package_names: List of package names

        Returns:
            Dictionary mapping package names to PackageInfo objects
        """
        results = {}
        for package_name in package_names:
            results[package_name] = self.get_package_info(package_name)
        return results
