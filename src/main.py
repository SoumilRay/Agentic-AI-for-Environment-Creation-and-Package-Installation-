"""Main CLI interface for the Agentic Package Installer."""

import os
import sys
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table
from dotenv import load_dotenv

from .graph.workflow import PackageInstallerWorkflow
from .agents.package_analyzer import PackageAnalyzerAgent

# Load environment variables
load_dotenv()

app = typer.Typer(
    name="agentic-installer",
    help="An intelligent multi-agent package installer using LangGraph and MCP"
)
console = Console()


def print_banner():
    """Print welcome banner."""
    banner = """
    ╔═══════════════════════════════════════════════════╗
    ║      Agentic Package Installer                    ║
    ║      Powered by LangGraph & MCP                   ║
    ╚═══════════════════════════════════════════════════╝
    """
    console.print(banner, style="bold cyan")


def get_api_keys():
    """Get API keys from environment or prompt user."""
    groq_api_key = os.getenv("GROQ_API_KEY")
    github_token = os.getenv("GITHUB_TOKEN")

    if not groq_api_key:
        console.print("GROQ_API_KEY not found in environment")
        groq_api_key = Prompt.ask("Enter your Groq API key", password=True)

    if not github_token:
        console.print("GitHub token not found (optional)")
        if Confirm.ask("Do you want to provide a GitHub token?"):
            github_token = Prompt.ask("Enter your GitHub token", password=True)

    return groq_api_key, github_token


def collect_user_input() -> dict:
    """Collect input from user interactively."""

    # Project name (mandatory)
    project_name = Prompt.ask("Project name (required)")
    while not project_name.strip():
        console.print("[red]Project name is required![/red]")
        project_name = Prompt.ask("Project name (required)")

    # Project description (optional)
    console.print("\nProject description (optional - helps with package recommendations)")
    project_description = Prompt.ask("Description", default="")

    # Project location (optional)
    console.print("\nProject location (optional - default: current directory)")
    project_location = Prompt.ask("Location", default="")

    # User packages (optional)
    console.print("\nPackages to install (optional - comma or space separated)")
    console.print("[dim]Example: numpy pandas seaborn[/dim]")
    packages_input = Prompt.ask("Packages", default="")

    # Parse packages
    analyzer = PackageAnalyzerAgent()
    user_packages = analyzer.parse_user_packages(packages_input)

    return {
        "project_name": project_name.strip(),
        "project_description": project_description.strip(),
        "project_location": project_location.strip() if project_location.strip() else None,
        "user_packages": user_packages
    }


def display_recommendations(recommendations: dict):
    """Display package recommendations to user."""
    console.print("\n[bold cyan]═══ Package Analysis Results ═══[/bold cyan]\n")

    # Approved packages (no changes)
    if recommendations.get("approved_packages"):
        console.print("[bold green]✓ Approved packages (no changes needed):[/bold green]")
        for pkg in recommendations["approved_packages"]:
            console.print(f"  • {pkg}")
        console.print()

    # Alternative suggestions
    if recommendations.get("alternatives"):
        console.print("Alternative suggestions:")
        for original, alt_info in recommendations["alternatives"].items():
            alt_pkg = alt_info["alternative"]
            reason = alt_info["reason"]
            desc = alt_info["description"]

            console.print(f"\n  [dim]Instead of:[/dim] [red]{original}[/red]")
            console.print(f"  [dim]Consider:[/dim] [green]{alt_pkg}[/green]")
            console.print(f"  [dim]Reason:[/dim] {reason}")
            console.print(f"  [dim]Description:[/dim] {desc}")
        console.print()

    # Additional packages
    if recommendations.get("additional"):
        console.print("[bold blue]➕ Additional suggested packages:[/bold blue]")
        for pkg, pkg_info in recommendations["additional"].items():
            reason = pkg_info["reason"]
            desc = pkg_info["description"]

            console.print(f"\n  [green]{pkg}[/green]")
            console.print(f"  [dim]Why:[/dim] {reason}")
            console.print(f"  [dim]Description:[/dim] {desc}")
        console.print()


def get_user_choices(recommendations: dict) -> dict:
    """Get user's choices for suggested packages."""
    choices = {}

    console.print("\n[bold]Select packages to install:[/bold]\n")

    # Ask about alternatives
    if recommendations.get("alternatives"):
        console.print("[yellow]Alternative Suggestions:[/yellow]")
        for original, alt_info in recommendations["alternatives"].items():
            alt_pkg = alt_info["alternative"]
            question = f"Use [green]{alt_pkg}[/green] instead of [red]{original}[/red]?"
            choices[alt_pkg] = Confirm.ask(question, default=True)

    # Ask about additional packages
    if recommendations.get("additional"):
        console.print("\n[blue]Additional Packages:[/blue]")
        for pkg in recommendations["additional"].keys():
            question = f"Install [green]{pkg}[/green]?"
            choices[pkg] = Confirm.ask(question, default=True)

    return choices


def build_final_package_list(recommendations: dict, choices: dict, user_packages: list) -> list:
    """Build final package list based on user choices."""
    final_packages = []

    # Add approved packages
    final_packages.extend(recommendations.get("approved_packages", []))

    # Handle alternatives
    for original, alt_info in recommendations.get("alternatives", {}).items():
        alt_pkg = alt_info["alternative"]
        if choices.get(alt_pkg, False):
            final_packages.append(alt_pkg)
        else:
            if original not in final_packages:
                final_packages.append(original)

    # Handle additional packages
    for pkg in recommendations.get("additional", {}).keys():
        if choices.get(pkg, False):
            final_packages.append(pkg)

    # If no packages selected and user had packages, use user's original list
    if not final_packages and user_packages:
        final_packages = user_packages

    # Remove duplicates
    seen = set()
    unique_packages = []
    for pkg in final_packages:
        if pkg not in seen:
            seen.add(pkg)
            unique_packages.append(pkg)

    return unique_packages


def display_results(state: dict):
    """Display final results."""
    console.print("\n[bold cyan]═══ Installation Complete ═══[/bold cyan]\n")

    # Project info
    console.print(f"[bold]Project:[/bold] {state['project_name']}")
    console.print(f"[bold]Location:[/bold] {state['project_path']}")
    console.print(f"[bold]Virtual Environment:[/bold] {state['venv_path']}\n")

    # Installed packages
    if state["installed_packages"]:
        console.print("[bold green]✓ Successfully installed packages:[/bold green]")
        for pkg in state["installed_packages"]:
            console.print(f"  • {pkg}")
        console.print()

    # Failed packages
    if state["failed_packages"]:
        console.print("[bold red]✗ Failed to install:[/bold red]")
        for fail in state["failed_packages"]:
            console.print(f"  • {fail['package']}: {fail['error']}")
        console.print()

    # Next steps
    console.print("[bold]Next steps:[/bold]")
    console.print(f"  1. cd {state['project_path']}")
    console.print(f"  2. source .venv/bin/activate")
    console.print("  3. Start coding! 🚀\n")


@app.command()
def install(
    project_name: Optional[str] = typer.Option(None, "--name", "-n", help="Project name"),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="Project description"),
    location: Optional[str] = typer.Option(None, "--location", "-l", help="Project location"),
    packages: Optional[str] = typer.Option(None, "--packages", "-p", help="Packages to install (comma-separated)")
):
    """
    Install packages intelligently using multi-agent system.
    """
    print_banner()

    # Get API keys
    groq_api_key, github_token = get_api_keys()

    # Collect user input
    if not project_name:
        user_input = collect_user_input()
    else:
        # Use command-line arguments
        analyzer = PackageAnalyzerAgent(groq_api_key="dummy", model_name="dummy")
        user_packages = analyzer.parse_user_packages(packages or "")

        user_input = {
            "project_name": project_name,
            "project_description": description or "",
            "project_location": location,
            "user_packages": user_packages
        }

    # Initialize workflow
    console.print("\nInitializing workflow...")
    model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    workflow = PackageInstallerWorkflow(
        groq_api_key=groq_api_key,
        github_token=github_token,
        model_name=model_name
    )

    # Prepare initial state
    initial_state = {
        "project_name": user_input["project_name"],
        "project_description": user_input["project_description"],
        "project_location": user_input["project_location"],
        "user_packages": user_input["user_packages"],
        "user_approved_packages": [],  # Initialize empty
        "messages": []
    }

    # Run setup and analysis manually (not full workflow)
    console.print("\nSetting up project...")

    # Step 1: Setup project
    state = workflow.setup_project_node(initial_state)

    # Step 2: Analyze packages
    state = workflow.analyze_packages_node(state)

    # Check if setup succeeded
    if not state.get("setup_success"):
        console.print(f"\n[bold red]Setup failed:[/bold red] {state.get('setup_error')}")
        sys.exit(1)

    console.print("Project setup complete![/green]")

    # Display recommendations if any
    if state.get("has_suggestions"):
        display_recommendations(state["recommendations"])

        # Get user choices
        choices = get_user_choices(state["recommendations"])

        # Build final package list
        final_packages = build_final_package_list(
            state["recommendations"],
            choices,
            user_input["user_packages"]
        )
    else:
        if state["recommendations"].get("message"):
            console.print(f"\n[dim]{state['recommendations']['message']}[/dim]")
        final_packages = user_input["user_packages"]

    # Update state with final packages
    state["user_approved_packages"] = final_packages

    # Show what will be installed
    if final_packages:
        console.print("\n[bold]Installing packages:[/bold]")
        for pkg in final_packages:
            console.print(f"  • {pkg}")
        console.print()

        # Install packages
        with console.status("[bold green]Installing packages...", spinner="dots"):
            # Run installer node directly
            state = workflow.install_packages_node(state)

        # Display results
        display_results(state)

        # Exit with appropriate code
        if state["installation_success"]:
            sys.exit(0)
        else:
            sys.exit(1)
    else:
        console.print("\n[yellow]ℹ No packages to install[/yellow]")
        console.print(f"\n[bold]Project created at:[/bold] {state['project_path']}\n")
        sys.exit(0)


@app.command()
def version():
    """Show version information."""
    console.print("[bold]Agentic Package Installer[/bold]")
    console.print("Version: 0.1.0")
    console.print("Powered by: LangGraph, MCP, Groq")


if __name__ == "__main__":
    app()
