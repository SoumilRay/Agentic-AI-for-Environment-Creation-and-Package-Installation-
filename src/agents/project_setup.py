"""Project setup agent for creating directories and virtual environments."""

import os
import subprocess
from pathlib import Path
from typing import Dict, Any


class ProjectSetupAgent:
    """Agent responsible for setting up project structure and environment."""

    def __init__(self):
        self.name = "ProjectSetupAgent"

    def create_project_folder(self, project_name: str, location: str = None) -> Dict[str, Any]:
        """
        Create project folder in specified location.

        Args:
            project_name: Name of the project
            location: Path where project should be created (default: current directory)

        Returns:
            Dictionary with status and project path
        """
        try:
            # Determine project location
            if location:
                base_path = Path(location).resolve()
            else:
                base_path = Path.cwd()

            # Create project directory
            project_path = base_path / project_name

            if project_path.exists():
                return {
                    "success": False,
                    "error": f"Project folder '{project_name}' already exists at {base_path}",
                    "project_path": None
                }

            project_path.mkdir(parents=True, exist_ok=False)

            return {
                "success": True,
                "project_path": str(project_path),
                "message": f"Created project folder at {project_path}"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create project folder: {str(e)}",
                "project_path": None
            }

    def create_virtual_environment(self, project_path: str) -> Dict[str, Any]:
        """
        Create a virtual environment using uv in the project directory.

        Args:
            project_path: Path to the project directory

        Returns:
            Dictionary with status and venv path
        """
        try:
            project_dir = Path(project_path)
            venv_path = project_dir / ".venv"

            # Check if uv is available
            result = subprocess.run(
                ["uv", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return {
                    "success": False,
                    "error": "uv is not installed. Please install it first.",
                    "venv_path": None
                }

            # Create virtual environment using uv
            result = subprocess.run(
                ["uv", "venv", str(venv_path)],
                cwd=str(project_dir),
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                return {
                    "success": False,
                    "error": f"Failed to create virtual environment: {result.stderr}",
                    "venv_path": None
                }

            return {
                "success": True,
                "venv_path": str(venv_path),
                "message": f"Created virtual environment at {venv_path}",
                "activation_command": f"source {venv_path}/bin/activate" if os.name != "nt" else f"{venv_path}\\Scripts\\activate"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create virtual environment: {str(e)}",
                "venv_path": None
            }

    def setup_project(
        self,
        project_name: str,
        location: str = None
    ) -> Dict[str, Any]:
        """
        Complete project setup: create folder and virtual environment.

        Args:
            project_name: Name of the project
            location: Path where project should be created

        Returns:
            Dictionary with status and paths
        """
        # Step 1: Create project folder
        folder_result = self.create_project_folder(project_name, location)

        if not folder_result["success"]:
            return folder_result

        # Step 2: Create virtual environment
        venv_result = self.create_virtual_environment(folder_result["project_path"])

        return {
            "success": venv_result["success"],
            "project_path": folder_result["project_path"],
            "venv_path": venv_result.get("venv_path"),
            "activation_command": venv_result.get("activation_command"),
            "message": f"Project setup complete" if venv_result["success"] else "Project folder created but virtual environment failed",
            "error": venv_result.get("error")
        }
