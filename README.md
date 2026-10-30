# AI-Doc-Reviewer

An AI-powered assistant designed to automate pull request code reviews and generate missing documentation, helping open-source maintainers manage contributions efficiently.

## Overview

Open-source maintainers spend hours reviewing repetitive pull requests, checking for missing docstrings, and catching common security or performance pitfalls. **AI-Doc-Reviewer** integrates directly with GitHub Actions and the Gemini API to analyze code diffs automatically whenever a pull request is opened or updated.

## Key Features

* **Automated Diff Analysis:** Inspects modified files in every pull request for logic bugs, security vulnerabilities, and performance bottlenecks.
* **Docstring & Documentation Generation:** Identifies undocumented functions, classes, and modules, outputting ready-to-commit docstrings in Google style.
* **Configurable Review Rules:** Customize ignored directories, file extensions, temperature settings, and review strictness through **config.yml**.
* **Zero-Friction CI/CD:** Runs automatically via GitHub Actions and posts structured markdown feedback directly as a pull request comment.

## Architecture

1. **Trigger:** A contributor opens or updates a pull request on GitHub.
2. **Diff Extraction:** The Python engine fetches the modified file diffs via the GitHub REST API while filtering out lockfiles and binary assets.
3. **AI Evaluation:** The filtered code changes are analyzed using the Gemini model against maintainability, security, and documentation standards.
4. **Feedback Delivery:** The assistant posts an actionable, line-referenced review summary and generated docstrings directly to the pull request thread.

## Quick Start

### Prerequisites

* Python 3.10 or higher
* A GitHub Personal Access Token (or the default **GITHUB_TOKEN** in GitHub Actions)
* A Gemini API Key stored in your repository secrets as **GEMINI_API_KEY**

### Local Installation

Clone the repository and install the required dependencies:

git clone https://github.com/Wittymind1/AI-doc-reviewer.git
cd AI-doc-reviewer
pip install -r requirements.txt

### Running Locally

Export your environment variables and run the script against a target pull request:

export GITHUB_TOKEN="your_github_token"
export GEMINI_API_KEY="your_gemini_api_key"
export GITHUB_REPOSITORY="Wittymind1/AI-doc-reviewer"
export PR_NUMBER="1"

python reviewer.py

## GitHub Actions Setup

1. Navigate to your repository **Settings** tab, select **Secrets and variables**, and tap **Actions**.
2. Add a new repository secret named **GEMINI_API_KEY** containing your API key.
3. Ensure **Read and write permissions** are enabled under **Workflow permissions** in your Actions settings so the bot can post pull request comments.

## License

Distributed under the MIT License. See the **LICENSE** file for complete details.
