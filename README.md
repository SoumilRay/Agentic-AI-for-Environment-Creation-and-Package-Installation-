# 🤖 Agentic Package Installer

An intelligent multi-agent package installer that uses **LangGraph** and **MCP (Model Context Protocol)** to help you set up Python projects with smart package recommendations.

## ✨ Features

- 🎯 **Intelligent Package Analysis**: Uses LLM (via Groq) to analyze your project and suggest better package alternatives
- 🔍 **GitHub Research**: Searches similar projects on GitHub to discover popular packages used in production
- 🎨 **Interactive CLI**: Beautiful, user-friendly command-line interface with rich formatting
- 📦 **Automatic Virtual Environment**: Creates and manages virtual environments using `uv`
- 🤝 **MCP Integration**: Demonstrates modern AI architecture using Model Context Protocol
- 🚀 **Smart Recommendations**: Only suggests alternatives when there are genuinely better options
- 📝 **Package Descriptions**: Provides detailed descriptions for all suggested packages

## 🏗️ Architecture

This project showcases a multi-agent system built with LangGraph:

```
┌─────────────────────────────────────────────────────────┐
│                   Supervisor (LangGraph)                 │
└───────┬─────────────────────────────────────────────────┘
        │
        ├──► Project Setup Agent
        │    └─ Creates folder & virtual environment
        │
        ├──► Package Analyzer Agent
        │    └─ LLM-powered package analysis
        │
        ├──► GitHub Research Agent (MCP)
        │    └─ Searches similar repos & analyzes dependencies
        │
        ├──► Recommender Agent
        │    └─ Combines LLM + GitHub insights
        │
        └──► Installation Agent
             └─ Installs packages with uv
```

### MCP Integration

This project demonstrates **Model Context Protocol** usage:

- **GitHub MCP Server**: Searches repositories, fetches requirements.txt/pyproject.toml files, and analyzes dependencies
- **PyPI MCP Server**: Fetches package information, descriptions, and latest stable versions

MCP provides a standardized way for the LLM to interact with external tools (GitHub API, PyPI API) without hardcoding API logic, making the system more extensible and maintainable.

## 🚀 Installation

### Prerequisites

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) package manager
- Groq API key (get one at [console.groq.com](https://console.groq.com))
- GitHub token (optional but recommended)

### Setup

1. Clone the repository:
```bash
git clone <your-repo-url>
cd AgenticPkgInstaller
```

2. Create virtual environment and install dependencies:
```bash
uv venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your API keys
```

4. Add your API keys to `.env`:
```env
GROQ_API_KEY=your_groq_api_key_here
GITHUB_TOKEN=your_github_token_here  # Optional but recommended
GROQ_MODEL=llama-3.3-70b-versatile
```

## 📖 Usage

### Interactive Mode (Recommended)

Simply run:
```bash
python -m src.main install
```

The tool will interactively ask you for:
- Project name (required)
- Project description (optional - helps with recommendations)
- Project location (optional - defaults to current directory)
- Packages to install (optional - comma or space separated)

### Command-Line Mode

```bash
python -m src.main install \
  --name "my-ml-project" \
  --description "Machine learning project for image classification" \
  --location "./projects" \
  --packages "numpy pandas scikit-learn"
```

### Example Workflow

1. **Start the tool**:
```bash
python -m src.main install
```

2. **Provide project details**:
```
📦 Project name: my-web-scraper
📝 Project description: Web scraper for e-commerce price monitoring
📁 Project location: (leave empty for current directory)
📚 Packages: requests beautifulsoup4
```

3. **Review recommendations**:
The tool will:
- Analyze your project description
- Search GitHub for similar projects
- Suggest better alternatives if they exist
- Provide package descriptions for all suggestions

4. **Approve or reject suggestions**:
```
💡 Alternative suggestions:
  Instead of: beautifulsoup4
  Consider: scrapy
  Reason: More robust framework with built-in features
  Description: A high-level web crawling and scraping framework

Use scrapy instead of beautifulsoup4? [Y/n]:

➕ Additional suggested packages:
  selenium
  Why: Useful for scraping JavaScript-heavy sites
  Description: Browser automation tool

Install selenium? [Y/n]:
```

5. **Installation completes**:
```
✓ Successfully installed packages:
  • requests
  • scrapy
  • selenium

Next steps:
  1. cd ./my-web-scraper
  2. source .venv/bin/activate
  3. Start coding! 🚀
```



## 🧪 Project Structure

```
AgenticPkgInstaller/
├── src/
│   ├── agents/              # Individual agent implementations
│   │   ├── project_setup.py
│   │   ├── package_analyzer.py
│   │   ├── github_researcher.py
│   │   ├── recommender.py
│   │   └── installer.py
│   ├── mcp_servers/         # MCP server implementations
│   │   ├── github_server.py
│   │   └── pypi_server.py
│   ├── graph/               # LangGraph workflow
│   │   └── workflow.py
│   └── main.py              # CLI interface
├── tests/                   # Test files
├── .env.example            # Example environment variables
├── pyproject.toml          # Project configuration
└── README.md
```


## 🎓 Learning Outcomes

This project demonstrates:
- Multi-agent system design with LangGraph
- Model Context Protocol (MCP) integration
- LLM-powered analysis and recommendations
- GitHub API interaction
- PyPI API usage
- Virtual environment management
- CLI development with Python
- Async programming patterns
- Error handling and user experience design

## 🚀 Future Enhancements

Potential improvements:
- Support for other package managers (pip, poetry, conda)
- Dependency conflict detection
- Package security vulnerability scanning
- Cost estimation before installation
- Export to different formats (poetry, conda env)
- Web interface
- Package version compatibility checking