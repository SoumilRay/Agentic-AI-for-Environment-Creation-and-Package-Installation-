"""Package installation agent using uv."""

import subprocess
from pathlib import Path
from typing import List, Dict, Any


class InstallerAgent:
    """Agent responsible for installing packages in the virtual environment."""

    def __init__(self):
        self.name = "InstallerAgent"

    def install_packages(
        self,
        packages: List[str],
        project_path: str,
        venv_path: str
    ) -> Dict[str, Any]:
        """
        Install packages using uv in the virtual environment.

        Args:
            packages: List of package names to install
            project_path: Path to the project directory
            venv_path: Path to the virtual environment

        Returns:
            Dictionary with installation status
        """
        if not packages:
            return {
                "success": True,
                "message": "No packages to install",
                "installed_packages": [],
                "failed_packages": []
            }

        installed = []
        failed = []

        try:
            # Use uv pip to install packages
            for package in packages:
                try:
                    # Install package using uv with the virtual environment
                    result = subprocess.run(
                        ["uv", "pip", "install", package, "--python", venv_path],
                        cwd=project_path,
                        capture_output=True,
                        text=True,
                        timeout=300  # 5 minutes timeout per package
                    )

                    if result.returncode == 0:
                        installed.append(package)
                    else:
                        failed.append({
                            "package": package,
                            "error": result.stderr
                        })

                except subprocess.TimeoutExpired:
                    failed.append({
                        "package": package,
                        "error": "Installation timeout (5 minutes exceeded)"
                    })
                except Exception as e:
                    failed.append({
                        "package": package,
                        "error": str(e)
                    })

            success = len(failed) == 0

            return {
                "success": success,
                "installed_packages": installed,
                "failed_packages": failed,
                "message": f"Successfully installed {len(installed)}/{len(packages)} packages"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Installation process failed: {str(e)}",
                "installed_packages": installed,
                "failed_packages": failed
            }

    def generate_requirements_file(
        self,
        packages: List[str],
        project_path: str
    ) -> Dict[str, Any]:
        """
        Generate requirements.txt file in the project directory.

        Args:
            packages: List of installed packages
            project_path: Path to the project directory

        Returns:
            Dictionary with status
        """
        try:
            requirements_path = Path(project_path) / "requirements.txt"

            # Write packages to requirements.txt
            with open(requirements_path, "w") as f:
                for package in packages:
                    f.write(f"{package}\n")

            return {
                "success": True,
                "requirements_path": str(requirements_path),
                "message": f"Generated requirements.txt with {len(packages)} packages"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to generate requirements.txt: {str(e)}"
            }

    def install_and_save(
        self,
        packages: List[str],
        project_path: str,
        venv_path: str
    ) -> Dict[str, Any]:
        """
        Install packages and generate requirements.txt.

        Args:
            packages: List of package names to install
            project_path: Path to the project directory
            venv_path: Path to the virtual environment

        Returns:
            Dictionary with complete installation status
        """
        # Install packages
        install_result = self.install_packages(packages, project_path, venv_path)

        # Generate requirements.txt only for successfully installed packages
        if install_result["installed_packages"]:
            req_result = self.generate_requirements_file(
                install_result["installed_packages"],
                project_path
            )
        else:
            req_result = {"success": False, "error": "No packages to save"}

        return {
            "success": install_result["success"],
            "installed_packages": install_result["installed_packages"],
            "failed_packages": install_result["failed_packages"],
            "requirements_generated": req_result.get("success", False),
            "requirements_path": req_result.get("requirements_path"),
            "message": install_result["message"]
        }
