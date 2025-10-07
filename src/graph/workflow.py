"""LangGraph workflow orchestrating the multi-agent system."""

from typing import TypedDict, Annotated, List, Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """State shared across all agents in the workflow."""
    # User inputs
    project_name: str
    project_description: str
    project_location: str
    user_packages: List[str]

    # Project setup results
    project_path: str
    venv_path: str
    setup_success: bool
    setup_error: str

    # Analysis results
    github_packages: List[str]
    recommendations: Dict[str, Any]
    has_suggestions: bool

    # User decisions
    user_approved_packages: List[str]

    # Installation results
    installed_packages: List[str]
    failed_packages: List[Dict[str, str]]
    installation_success: bool

    # Workflow control
    messages: Annotated[List[str], add_messages]
    next_step: str


class PackageInstallerWorkflow:
    """LangGraph workflow for the agentic package installer."""

    def __init__(
        self,
        groq_api_key: str,
        github_token: str = None,
        model_name: str = "llama-3.3-70b-versatile"
    ):
        from ..agents.project_setup import ProjectSetupAgent
        from ..agents.github_researcher import GitHubResearchAgent
        from ..agents.recommender import RecommenderAgent
        from ..agents.installer import InstallerAgent

        self.project_setup_agent = ProjectSetupAgent()
        self.github_researcher = GitHubResearchAgent(github_token)
        self.recommender = RecommenderAgent(groq_api_key, github_token, model_name)
        self.installer = InstallerAgent()

        self.workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("setup_project", self.setup_project_node)
        workflow.add_node("analyze_packages", self.analyze_packages_node)
        workflow.add_node("install_packages", self.install_packages_node)

        # Define edges
        workflow.set_entry_point("setup_project")

        # After setup, always go to analysis
        workflow.add_edge("setup_project", "analyze_packages")

        # After analysis, go to installation
        workflow.add_edge("analyze_packages", "install_packages")

        # After installation, end
        workflow.add_edge("install_packages", END)

        return workflow.compile()

    def setup_project_node(self, state: AgentState) -> AgentState:
        """Node: Set up project folder and virtual environment."""
        result = self.project_setup_agent.setup_project(
            project_name=state["project_name"],
            location=state.get("project_location")
        )

        state["project_path"] = result.get("project_path", "")
        state["venv_path"] = result.get("venv_path", "")
        state["setup_success"] = result["success"]
        state["setup_error"] = result.get("error", "")

        if result["success"]:
            state["messages"].append(f"{result['message']}")
        else:
            state["messages"].append(f"Setup failed: {result.get('error')}")

        return state

    def analyze_packages_node(self, state: AgentState) -> AgentState:
        """Node: Analyze packages and generate recommendations."""
        if not state["setup_success"]:
            state["has_suggestions"] = False
            state["recommendations"] = {}
            state["user_approved_packages"] = state["user_packages"]
            return state

        # Generate recommendations
        recommendations = self.recommender.generate_recommendations(
            user_packages=state["user_packages"],
            project_description=state.get("project_description")
        )

        state["recommendations"] = recommendations
        state["has_suggestions"] = recommendations.get("has_suggestions", False)

        # Store for later use
        state["messages"].append(f"Package analysis complete")

        return state

    def install_packages_node(self, state: AgentState) -> AgentState:
        """Node: Install approved packages."""
        if not state["setup_success"]:
            state["installation_success"] = False
            return state

        packages_to_install = state["user_approved_packages"]

        if not packages_to_install:
            state["installation_success"] = True
            state["installed_packages"] = []
            state["failed_packages"] = []
            state["messages"].append("No packages to install")
            return state

        # Install packages
        result = self.installer.install_and_save(
            packages=packages_to_install,
            project_path=state["project_path"],
            venv_path=state["venv_path"]
        )

        state["installed_packages"] = result["installed_packages"]
        state["failed_packages"] = result["failed_packages"]
        state["installation_success"] = result["success"]

        if result["success"]:
            state["messages"].append(f"✓ {result['message']}")
            if result.get("requirements_generated"):
                state["messages"].append(f"Generated requirements.txt")
        else:
            state["messages"].append(f"Installation issues occurred")

        return state

    def run(self, initial_state: Dict[str, Any]) -> AgentState:
        """
        Run the workflow with initial state.

        Args:
            initial_state: Initial state dictionary

        Returns:
            Final state after workflow completion
        """
        # Initialize messages list if not present
        if "messages" not in initial_state:
            initial_state["messages"] = []

        # Run the workflow
        final_state = self.workflow.invoke(initial_state)

        return final_state
