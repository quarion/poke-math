# PokeMath Tools

This directory contains various utility tools for the PokeMath project.

Each tool is self-documented with usage instructions in its source code or in a dedicated README file.

## Running Tools

Most tools can be run directly from the command line. For example:

```bash
# Run a Python tool
python tool_name.py [arguments]

# Run a PowerShell script
./script_name.ps1 [arguments]
```

## Prerequisites

The required dependencies for all tools are included in the project's `requirements.txt` file. Make sure to install them with:

```bash
pip install -r requirements.txt
```

`get_pr_comments.py` uses the GitHub CLI instead of reading a personal access
token from `.env`. Authenticate once through the operating-system credential
store, then run the helper normally:

```powershell
gh auth login
python tools/get_pr_comments.py --pr 1
```
