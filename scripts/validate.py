#!/usr/bin/env python3
"""
GitHub Input Validation Script
Validates: commit messages, PR titles & branch names, issue fields, code/file content
"""

import os
import re
import sys
import json
import argparse
from pathlib import Path


# ─────────────────────────────────────────────
# CONFIGURATION — edit these to fit your rules
# ─────────────────────────────────────────────

COMMIT_RULES = {
    # Conventional Commits: type(scope): description
    "pattern": r"^(feat|fix|docs|style|refactor|perf|test|chore|ci|build|revert)(\(.+\))?: .{1,100}$",
    "min_length": 10,
    "max_length": 100,
    "forbidden_prefixes": ["WIP", "wip", "TEMP", "temp", "fixup!", "squash!"],
}

BRANCH_RULES = {
    # e.g. feature/my-feature, bugfix/issue-123, hotfix/critical-bug
    "pattern": r"^(feature|bugfix|hotfix|release|chore|docs|refactor)/[a-z0-9][a-z0-9\-]{1,60}[a-z0-9]$",
    "protected": ["main", "master", "develop", "staging", "production"],
    "max_length": 70,
}

PR_TITLE_RULES = {
    # Same as conventional commits or a plain descriptive title
    "pattern": r"^(feat|fix|docs|style|refactor|perf|test|chore|ci|build|revert)(\(.+\))?: .{5,100}$",
    "min_length": 10,
    "max_length": 120,
    "forbidden_words": ["test pr", "asdf", "temp", "wip"],
}

ISSUE_RULES = {
    "title_min_length": 10,
    "title_max_length": 150,
    "body_min_length": 30,
    "required_sections": [],      # e.g. ["## Steps to Reproduce", "## Expected Behavior"]
    "forbidden_titles": ["bug", "issue", "problem", "help", "question"],
}

CODE_RULES = {
    "forbidden_patterns": [
        (r"console\.log\(", "Remove debug console.log() statements"),
        (r"print\(f?['\"]DEBUG", "Remove debug print statements"),
        (r"TODO(?!.*#\d+)", "TODOs must reference an issue number, e.g. TODO #123"),
        (r"FIXME(?!.*#\d+)", "FIXMEs must reference an issue number, e.g. FIXME #123"),
        (r"(?i)password\s*=\s*['\"][^'\"]+['\"]", "Possible hardcoded password detected"),
        (r"(?i)api_key\s*=\s*['\"][^'\"]+['\"]", "Possible hardcoded API key detected"),
        (r"(?i)secret\s*=\s*['\"][^'\"]+['\"]", "Possible hardcoded secret detected"),
    ],
    "max_file_size_kb": 500,
    "forbidden_extensions": [".env", ".pem", ".key", ".p12", ".pfx"],
    "check_extensions": [".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rb", ".sh"],
}


# ─────────────────────────────────────────────
# ANSI COLORS
# ─────────────────────────────────────────────

GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

def ok(msg):    print(f"  {GREEN}✔{RESET}  {msg}")
def fail(msg):  print(f"  {RED}✘{RESET}  {msg}")
def warn(msg):  print(f"  {YELLOW}⚠{RESET}  {msg}")
def info(msg):  print(f"  {CYAN}ℹ{RESET}  {msg}")
def header(msg):print(f"\n{BOLD}{CYAN}{'─'*50}{RESET}\n{BOLD}  {msg}{RESET}\n{'─'*50}")


# ─────────────────────────────────────────────
# VALIDATORS
# ─────────────────────────────────────────────

def validate_commit_message(message: str) -> bool:
    header("Commit Message Validation")
    errors = []
    message = message.strip()

    if len(message) < COMMIT_RULES["min_length"]:
        errors.append(f"Too short ({len(message)} chars). Minimum: {COMMIT_RULES['min_length']}")

    if len(message) > COMMIT_RULES["max_length"]:
        errors.append(f"Too long ({len(message)} chars). Maximum: {COMMIT_RULES['max_length']}")

    if not re.match(COMMIT_RULES["pattern"], message):
        errors.append(
            "Does not follow Conventional Commits format.\n"
            "       Expected: type(scope): description\n"
            "       Types: feat|fix|docs|style|refactor|perf|test|chore|ci|build|revert\n"
            f'       Got: "{message}"'
        )

    for prefix in COMMIT_RULES["forbidden_prefixes"]:
        if message.startswith(prefix):
            errors.append(f'Forbidden prefix "{prefix}". Do not commit WIP/temp work.')

    info(f'Commit: "{message}"')
    if errors:
        for e in errors: fail(e)
        return False
    ok("Commit message is valid.")
    return True


def validate_branch_name(branch: str) -> bool:
    header("Branch Name Validation")
    errors = []
    branch = branch.strip()

    if branch in BRANCH_RULES["protected"]:
        ok(f'"{branch}" is a protected branch — skipping format check.')
        return True

    if len(branch) > BRANCH_RULES["max_length"]:
        errors.append(f"Too long ({len(branch)} chars). Maximum: {BRANCH_RULES['max_length']}")

    if not re.match(BRANCH_RULES["pattern"], branch):
        errors.append(
            "Branch name does not follow naming convention.\n"
            "       Expected: type/description (lowercase, hyphens only)\n"
            "       Types: feature|bugfix|hotfix|release|chore|docs|refactor\n"
            f'       Got: "{branch}"'
        )

    if re.search(r"[A-Z_\s]", branch):
        errors.append("Branch name must be lowercase with hyphens only (no underscores or spaces).")

    info(f'Branch: "{branch}"')
    if errors:
        for e in errors: fail(e)
        return False
    ok("Branch name is valid.")
    return True


def validate_pr_title(title: str) -> bool:
    header("PR Title Validation")
    errors = []
    title = title.strip()

    if len(title) < PR_TITLE_RULES["min_length"]:
        errors.append(f"Too short ({len(title)} chars). Minimum: {PR_TITLE_RULES['min_length']}")

    if len(title) > PR_TITLE_RULES["max_length"]:
        errors.append(f"Too long ({len(title)} chars). Maximum: {PR_TITLE_RULES['max_length']}")

    if not re.match(PR_TITLE_RULES["pattern"], title, re.IGNORECASE):
        errors.append(
            "PR title does not follow the required format.\n"
            "       Expected: type(scope): description\n"
            f'       Got: "{title}"'
        )

    for word in PR_TITLE_RULES["forbidden_words"]:
        if word.lower() in title.lower():
            errors.append(f'Forbidden phrase "{word}" found in PR title.')

    info(f'PR Title: "{title}"')
    if errors:
        for e in errors: fail(e)
        return False
    ok("PR title is valid.")
    return True


def validate_issue(title: str, body: str) -> bool:
    header("Issue Fields Validation")
    errors = []
    title = title.strip()
    body  = (body or "").strip()

    # Title checks
    if len(title) < ISSUE_RULES["title_min_length"]:
        errors.append(f"Title too short ({len(title)} chars). Minimum: {ISSUE_RULES['title_min_length']}")

    if len(title) > ISSUE_RULES["title_max_length"]:
        errors.append(f"Title too long ({len(title)} chars). Maximum: {ISSUE_RULES['title_max_length']}")

    for forbidden in ISSUE_RULES["forbidden_titles"]:
        if title.lower().strip() == forbidden.lower():
            errors.append(f'Issue title "{title}" is too generic. Please be more descriptive.')

    # Body checks
    if len(body) < ISSUE_RULES["body_min_length"]:
        errors.append(
            f"Issue body too short ({len(body)} chars). "
            f"Minimum: {ISSUE_RULES['body_min_length']} chars. Please describe the issue in detail."
        )

    for section in ISSUE_RULES["required_sections"]:
        if section not in body:
            errors.append(f'Required section missing from issue body: "{section}"')

    info(f'Issue title: "{title}"')
    info(f"Issue body:  {len(body)} chars")
    if errors:
        for e in errors: fail(e)
        return False
    ok("Issue fields are valid.")
    return True


def validate_code_files(paths: list[str]) -> bool:
    header("Code / File Content Validation")
    all_ok = True

    if not paths:
        warn("No file paths provided for code validation.")
        return True

    for filepath in paths:
        path = Path(filepath)
        file_errors = []

        # Check forbidden extensions (e.g. .env, .pem)
        if path.suffix in CODE_RULES["forbidden_extensions"]:
            fail(f"{filepath}: Forbidden file type '{path.suffix}' — do not commit sensitive files.")
            all_ok = False
            continue

        # Check file size
        if path.exists():
            size_kb = path.stat().st_size / 1024
            if size_kb > CODE_RULES["max_file_size_kb"]:
                file_errors.append(
                    f"File too large ({size_kb:.1f} KB). "
                    f"Maximum: {CODE_RULES['max_file_size_kb']} KB"
                )

        # Only scan whitelisted extensions for code patterns
        if path.suffix not in CODE_RULES["check_extensions"]:
            ok(f"{filepath}: skipped (extension not in scan list)")
            continue

        if not path.exists():
            warn(f"{filepath}: file not found, skipping.")
            continue

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            warn(f"{filepath}: could not read file — {e}")
            continue

        for line_num, line in enumerate(content.splitlines(), 1):
            for pattern, message in CODE_RULES["forbidden_patterns"]:
                if re.search(pattern, line):
                    file_errors.append(f"Line {line_num}: {message}")

        if file_errors:
            fail(f"{filepath}:")
            for e in file_errors:
                print(f"       {RED}→{RESET} {e}")
            all_ok = False
        else:
            ok(f"{filepath}: clean")

    return all_ok


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="GitHub input validator — commit, branch, PR, issue, code"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # commit
    p_commit = subparsers.add_parser("commit", help="Validate a commit message")
    p_commit.add_argument("message", help="The commit message string")

    # branch
    p_branch = subparsers.add_parser("branch", help="Validate a branch name")
    p_branch.add_argument("name", help="The branch name")

    # pr
    p_pr = subparsers.add_parser("pr", help="Validate a PR title")
    p_pr.add_argument("title", help="The PR title string")

    # issue
    p_issue = subparsers.add_parser("issue", help="Validate issue fields")
    p_issue.add_argument("title", help="Issue title")
    p_issue.add_argument("--body", default="", help="Issue body (optional)")
    p_issue.add_argument("--body-file", help="Path to a file containing the issue body")

    # code
    p_code = subparsers.add_parser("code", help="Validate code/file content")
    p_code.add_argument("files", nargs="*", help="File paths to validate")
    p_code.add_argument("--from-env", action="store_true",
                        help="Read file list from CHANGED_FILES env var (space-separated)")

    # all — run all checks using env vars (for GitHub Actions)
    subparsers.add_parser("all", help="Run all checks using GitHub Actions env vars")

    args = parser.parse_args()

    results = []

    if args.command == "commit":
        results.append(validate_commit_message(args.message))

    elif args.command == "branch":
        results.append(validate_branch_name(args.name))

    elif args.command == "pr":
        results.append(validate_pr_title(args.title))

    elif args.command == "issue":
        body = args.body
        if args.body_file:
            body = Path(args.body_file).read_text(encoding="utf-8")
        results.append(validate_issue(args.title, body))

    elif args.command == "code":
        files = args.files
        if args.from_env:
            env_files = os.environ.get("CHANGED_FILES", "")
            files = [f for f in env_files.split() if f]
        results.append(validate_code_files(files))

    elif args.command == "all":
        print(f"\n{BOLD}{'═'*50}")
        print("  GitHub Input Validator — Full Suite")
        print(f"{'═'*50}{RESET}")

        commit_msg = os.environ.get("COMMIT_MESSAGE", "")
        branch     = os.environ.get("BRANCH_NAME", "")
        pr_title   = os.environ.get("PR_TITLE", "")
        issue_title= os.environ.get("ISSUE_TITLE", "")
        issue_body = os.environ.get("ISSUE_BODY", "")
        changed    = os.environ.get("CHANGED_FILES", "")
        files      = [f for f in changed.split() if f]

        if commit_msg: results.append(validate_commit_message(commit_msg))
        else:          warn("COMMIT_MESSAGE not set — skipping commit validation.")

        if branch:     results.append(validate_branch_name(branch))
        else:          warn("BRANCH_NAME not set — skipping branch validation.")

        if pr_title:   results.append(validate_pr_title(pr_title))
        else:          warn("PR_TITLE not set — skipping PR title validation.")

        if issue_title:results.append(validate_issue(issue_title, issue_body))
        else:          warn("ISSUE_TITLE not set — skipping issue validation.")

        if files:      results.append(validate_code_files(files))
        else:          warn("CHANGED_FILES not set — skipping code validation.")

    # ── Summary ──
    passed = results.count(True)
    failed = results.count(False)
    total  = len(results)

    print(f"\n{BOLD}{'─'*50}{RESET}")
    if failed == 0:
        print(f"{GREEN}{BOLD}  ✔ All {total} check(s) passed.{RESET}")
    else:
        print(f"{RED}{BOLD}  ✘ {failed}/{total} check(s) failed.{RESET}")
    print(f"{'─'*50}\n")

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
