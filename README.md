# Agentic Package Installer

An intelligent multi-agent package installer that uses **LangGraph** and **MCP (Model Context Protocol)** to help you set up Python projects with smart package recommendations.

## Features

- Uses an LLM to analyze your project and suggest better package alternatives
- Searches similar projects on GitHub to discover popular packages used in production
- Automatically creates and manages virtual environments using uv
- MCP Servers

## Architecture

This project showcases a multi-agent system built with LangGraph:

```
┌─────────────────────────────────────────────────────────┐
│                   Supervisor                            │
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



- **GitHub MCP Server**: Searches repositories, fetches requirements.txt/pyproject.toml files, and analyzes dependencies
- **PyPI MCP Server**: Fetches package information, descriptions, and latest stable versions


## Usage

### Interactive Mode

Run:
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
📦 Project name: Data Project
📝 Project description: A project to practice data wrangling and visualization
📁 Project location: ../DataProject
📚 Packages: numpy pandas
```

3. **Review recommendations**:
The tool will:
- Analyze your project description
- Search GitHub for similar projects
- Suggest better alternatives only if they exist
- Provide package descriptions for all suggestions

4. **Approve or reject suggestions**:
```
 Additional suggested packages:
  matplotlib
  Why: Useful for plotting graphs

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
```
