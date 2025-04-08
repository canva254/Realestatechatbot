# Git Hooks Configuration

This project uses Git hooks to automate several development workflows.

## Installed Hooks

### post-commit
- **Purpose**: Automatically pushes commits to GitHub
- **Location**: `.git/hooks/post-commit`
- **Behavior**: Every time you make a commit, it will be automatically pushed to the remote repository

### pre-commit
- **Purpose**: Validates code before committing
- **Location**: `.git/hooks/pre-commit`
- **Behavior**: Checks Python files for syntax errors before allowing a commit

### post-merge
- **Purpose**: Automatically installs dependencies after pulling changes
- **Location**: `.git/hooks/post-merge`
- **Behavior**: When you pull changes that update dependencies.txt, it automatically installs the new requirements

## Setting Up Git Hooks in a New Clone

When you clone this repository, Git hooks are not automatically copied. To set them up:

1. Make all hook scripts executable:
   ```bash
   chmod +x .git/hooks/post-commit
   chmod +x .git/hooks/pre-commit
   chmod +x .git/hooks/post-merge
   ```

2. To disable automatic pushing temporarily:
   ```bash
   mv .git/hooks/post-commit .git/hooks/post-commit.disabled
   ```

3. To re-enable:
   ```bash
   mv .git/hooks/post-commit.disabled .git/hooks/post-commit
   chmod +x .git/hooks/post-commit
   ```

## Note

These Git hooks help maintain code quality and ensure the GitHub repository stays up-to-date with local changes.