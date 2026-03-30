# GitHub Input Validator

A Python-based validation suite that runs as a **GitHub Actions workflow**, checking:

| Check | Trigger |
|---|---|
| ✅ Commit messages | Every `push` |
| ✅ Branch names | Every `push` |
| ✅ PR titles | `pull_request` open/edit/sync |
| ✅ Issue fields | `issues` open/edit |
| ✅ Code/file content | `pull_request` (changed files) |

---

## Setup

1. Copy `.github/workflows/validate.yml` and `scripts/validate.py` into your repo.
2. Customize the rules at the top of `scripts/validate.py`.
3. Push — the workflow runs automatically.

---

## Rules (all configurable in `scripts/validate.py`)

### Commit Messages
Follows [Conventional Commits](https://www.conventionalcommits.org/):
```
feat(auth): add OAuth2 login support
fix: handle null pointer in user service
docs: update API reference
```
**Types:** `feat` | `fix` | `docs` | `style` | `refactor` | `perf` | `test` | `chore` | `ci` | `build` | `revert`

### Branch Names
```
feature/user-authentication
bugfix/fix-login-redirect
hotfix/critical-null-error
```
Format: `type/description` — lowercase, hyphens only.

### PR Titles
Same Conventional Commits format as commit messages.

### Issue Fields
- Title: 10–150 chars, not generic (e.g. not just "bug" or "help")
- Body: minimum 30 chars

### Code / File Content
Scans changed files for:
- Debug statements (`console.log`, `print("DEBUG`)
- Untracked TODOs/FIXMEs (must reference `#issue-number`)
- Hardcoded secrets (`password =`, `api_key =`, `secret =`)
- Forbidden file types (`.env`, `.pem`, `.key`, etc.)
- Files over 500 KB

---

## Local Usage

```bash
# Validate a commit message
python scripts/validate.py commit "feat(auth): add login page"

# Validate a branch name
python scripts/validate.py branch "feature/user-login"

# Validate a PR title
python scripts/validate.py pr "fix(api): handle 404 errors gracefully"

# Validate an issue
python scripts/validate.py issue "Login fails on mobile" --body "Steps to reproduce..."

# Validate specific files
python scripts/validate.py code src/auth.py src/utils.py
```
