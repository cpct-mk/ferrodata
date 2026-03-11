#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./publish_to_github.sh <github-username> <repo-name>
# Example:
#   ./publish_to_github.sh yourname ferrodata

if [[ $# -ne 2 ]]; then
  echo "Usage: $0 <github-username> <repo-name>"
  exit 1
fi

USERNAME="$1"
REPO="$2"

# 1) Create local git repo if needed
if [[ ! -d .git ]]; then
  git init
fi

# 2) Commit
if ! git config user.name >/dev/null; then
  echo "Git user.name is not set. Run: git config --global user.name \"Your Name\""
  exit 1
fi
if ! git config user.email >/dev/null; then
  echo "Git user.email is not set. Run: git config --global user.email \"you@example.com\""
  exit 1
fi

git add .
git commit -m "Initial ferrodata project" || true

# 3) Ensure remote exists
REMOTE_URL="https://github.com/${USERNAME}/${REPO}.git"
if git remote get-url origin >/dev/null 2>&1; then
  git remote set-url origin "$REMOTE_URL"
else
  git remote add origin "$REMOTE_URL"
fi

# 4) Push
BRANCH="main"
git branch -M "$BRANCH"

echo "If the GitHub repo does not exist yet, create it first in the web UI:"
echo "  https://github.com/new"
echo "Name: ${REPO}"
echo
git push -u origin "$BRANCH"
