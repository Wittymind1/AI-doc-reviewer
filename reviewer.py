"""
AI-Doc-Reviewer: Automated Code Review and Documentation Assistant.
Fetches Pull Request diffs from GitHub, analyzes code quality and missing
documentation using the Gemini API, and posts structured review comments.
"""

import logging
import os
import sys
from typing import Any, Dict, List

import yaml
from github import Auth, Github
from google import genai
from google.genai import types

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def load_config(config_path: str = "config.yml") -> Dict[str, Any]:
    """Load reviewer configuration settings from a YAML file."""
    default_config: Dict[str, Any] = {
        "model": "gemini-2.5-flash",
        "temperature": 0.2,
        "max_patch_chars": 12000,
        "supported_extensions": [".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs", ".java"],
        "excluded_paths": ["venv/", "node_modules/", "dist/", "build/", ".git/"],
        "review_focus": [
            "Code bugs and edge cases",
            "Security vulnerabilities",
            "Missing or incomplete docstrings and inline documentation",
            "Performance and readability improvements",
        ],
    }

    if not os.path.exists(config_path):
        logger.warning("Configuration file not found. Using default settings.")
        return default_config

    with open(config_path, "r", encoding="utf-8") as file:
        user_config = yaml.safe_load(file) or {}
        default_config.update(user_config)
        return default_config


def should_review_file(filename: str, config: Dict[str, Any]) -> bool:
    """Check whether a modified file should be included in the AI review."""
    for excluded in config.get("excluded_paths", []):
        if filename.startswith(excluded) or f"/{excluded}" in filename:
            return False

    extensions: List[str] = config.get("supported_extensions", [])
    return any(filename.endswith(ext) for ext in extensions)


def collect_pr_diffs(repo: Any, pr_number: int, config: Dict[str, Any]) -> str:
    """Retrieve and format code diffs from a GitHub Pull Request."""
    pull_request = repo.get_pull(pr_number)
    files = pull_request.get_files()
    collected_diffs: List[str] = []
    max_chars: int = config.get("max_patch_chars", 12000)
    current_chars = 0

    for pr_file in files:
        if not should_review_file(pr_file.filename, config):
            logger.info("Skipping excluded or unsupported file: %s", pr_file.filename)
            continue

        if not pr_file.patch:
            continue

        file_section = (
            f"File: {pr_file.filename} (Status: {pr_file.status})\n"
            f"Diff:\n{pr_file.patch}\n\n"
        )

        if current_chars + len(file_section) > max_chars:
            logger.warning("Diff size limit reached. Truncating remaining files.")
            break

        collected_diffs.append(file_section)
        current_chars += len(file_section)

    return "".join(collected_diffs)


def generate_ai_review(diff_content: str, config: Dict[str, Any], api_key: str) -> str:
    """Send the pull request diff to the Gemini model for code and doc analysis."""
    client = genai.Client(api_key=api_key)
    focus_points = "\n".join(f"- {item}" for item in config.get("review_focus", []))

    system_instruction = (
        "You are AI-Doc-Reviewer, a senior open-source maintainer and code auditor. "
        "Analyze the provided GitHub Pull Request diff and produce a clear, constructive "
        "review organized into three sections:\n"
        "1. Summary of Changes: A concise overview of what the pull request accomplishes.\n"
        "2. Code Quality & Security Findings: Specific bugs, edge cases, or improvements "
        "referenced by file name.\n"
        "3. Generated Documentation: Ready-to-use docstrings or README updates for any "
        "undocumented functions, classes, or modules found in the diff.\n\n"
        f"Prioritize the following review areas:\n{focus_points}"
    )

    prompt = f"Review the following Pull Request code diffs:\n\n{diff_content}"

    response = client.models.generate_content(
        model=config.get("model", "gemini-2.5-flash"),
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=config.get("temperature", 0.2),
        ),
    )

    return response.text or "No review comments generated."


def post_review_comment(repo: Any, pr_number: int, review_body: str) -> None:
    """Publish the AI review findings as a comment on the Pull Request."""
    pull_request = repo.get_pull(pr_number)
    header = "## AI-Doc-Reviewer Automated Report\n\n"
    footer = "\n\n*Generated automatically by AI-Doc-Reviewer.*"
    pull_request.create_issue_comment(f"{header}{review_body}{footer}")
    logger.info("Successfully posted AI review to Pull Request #%d.", pr_number)


def main() -> None:
    """Main execution entrypoint for the GitHub Actions workflow."""
    github_token = os.getenv("GITHUB_TOKEN")
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    repo_name = os.getenv("GITHUB_REPOSITORY")
    pr_number_str = os.getenv("PR_NUMBER")

    if not all([github_token, gemini_api_key, repo_name, pr_number_str]):
        logger.error(
            "Missing required environment variables: GITHUB_TOKEN, GEMINI_API_KEY, "
            "GITHUB_REPOSITORY, or PR_NUMBER."
        )
        sys.exit(1)

    pr_number = int(pr_number_str)  # type: ignore[arg-type]
    config = load_config()

    auth = Auth.Token(github_token)  # type: ignore[arg-type]
    gh_client = Github(auth=auth)
    repo = gh_client.get_repo(repo_name)  # type: ignore[arg-type]

    logger.info("Fetching diffs for %s PR #%d...", repo_name, pr_number)
    diff_content = collect_pr_diffs(repo, pr_number, config)

    if not diff_content.strip():
        logger.info("No eligible code changes found for review. Exiting cleanly.")
        return

    logger.info("Running AI code and documentation analysis...")
    review_report = generate_ai_review(diff_content, config, gemini_api_key)  # type: ignore[arg-type]

    post_review_comment(repo, pr_number, review_report)


if __name__ == "__main__":
    main()
