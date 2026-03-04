#!/usr/bin/env bash
set -euo pipefail

if [ -d .git ]; then
  echo "This directory is already a Git repository."
  exit 1
fi

git init

git add .
git commit -m "Initial commit"

git branch -M main

echo "Standalone repository initialized on branch 'main'."
echo "Next (optional): git remote add origin <repo-url> && git push -u origin main"
