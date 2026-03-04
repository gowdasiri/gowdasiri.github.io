# projects-repo

Starter scaffold intended to become its **own standalone Git repository**.

## What's included

- `src/`: source code directory
- `tests/`: test files
- `.gitignore`: common ignores for Python, Node, and editor artifacts
- `LICENSE`: MIT license template
- `init-standalone-repo.sh`: one-command repo initialization

## Create a standalone repo from this scaffold

```bash
cp -R projects-repo <your-new-repo-name>
cd <your-new-repo-name>
./init-standalone-repo.sh
```

This script:

1. Initializes a new Git repository
2. Renames the default branch to `main`
3. Creates the first commit

## Optional: connect to GitHub

```bash
git remote add origin <your-github-repo-url>
git push -u origin main
```
