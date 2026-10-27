# 🐙 GitHub & Git Commands Guide — Paper Radar

A comprehensive, systematic reference of Git and GitHub commands used in the **Paper Radar** project, complete with practical use cases, simple explanations, and exact syntax.

---

## 📑 Table of Contents
1. [Initial Repository Setup & GitHub Link](#1-initial-repository-setup--github-link)
2. [Everyday Workflow Commands](#2-everyday-workflow-commands)
3. [Branching & Collaboration](#3-branching--collaboration)
4. [Syncing with GitHub (Push & Pull)](#4-syncing-with-github-push--pull)
5. [Inspection & History](#5-inspection--history)
6. [Undoing Changes & Troubleshooting](#6-undoing-changes--troubleshooting)
7. [Commands Executed for this Project](#7-commands-executed-for-this-project)

---

## 1. Initial Repository Setup & GitHub Link

These commands are run once when turning a local folder into a Git repository and linking it to a remote GitHub repository.

### `git init`
* **Explanation:** Initializes a brand-new, empty local Git repository in the current folder. It creates a hidden `.git` folder that tracks all history and changes.
* **Use Case:** First-time setup before you can commit files.
```bash
git init
```

### `git branch -M main`
* **Explanation:** Renames the default branch from `master` to `main` (modern standard naming across GitHub).
* **Use Case:** Ensuring consistency with GitHub's default `main` branch.
```bash
git branch -M main
```

### `git remote add origin <URL>`
* **Explanation:** Connects your local repository to a remote repository hosted on GitHub, giving it the shorthand name `origin`.
* **Use Case:** Telling Git where to push code online.
```bash
git remote add origin https://github.com/SachinSingh201/PaperRadar.git
```

### `git remote -v`
* **Explanation:** Lists all configured remote connections and their URLs (fetch and push).
* **Use Case:** Verifying that your repository points to the correct GitHub URL.
```bash
git remote -v
```

---

## 2. Everyday Workflow Commands

Used daily when making edits, adding features, or fixing bugs.

### `git status`
* **Explanation:** Shows the current state of your working directory. Displays tracked, modified, staged, and untracked files.
* **Use Case:** Run this before and after any staging or commit to check what is about to be saved.
```bash
git status
```

### `git add <files>` / `git add .`
* **Explanation:** Moves changes from the working directory into the "staging area" (preparing them for the snapshot).
* **Use Case:** 
  - `git add .` stages all new, modified, and deleted files in the directory.
  - `git add README.md` stages only a specific file.
```bash
git add .
```

### `git commit -m "<message>"`
* **Explanation:** Takes a permanent snapshot of all staged files and records it in Git history with an explanatory message.
* **Use Case:** Saving a logical checkpoint of your progress (e.g., after updating project name or adding a feature).
```bash
git commit -m "feat: initial commit of Paper Radar project"
```

### `git diff`
* **Explanation:** Displays line-by-line differences between your current files and the last committed version.
* **Use Case:** Reviewing your exact code modifications before staging them.
```bash
git diff
```

---

## 3. Syncing with GitHub (Push & Pull)

Used to synchronize your local machine with GitHub's cloud servers.

### `git push -u origin main`
* **Explanation:** Uploads your local commits to the `main` branch on GitHub. The `-u` (or `--set-upstream`) flag links your local `main` to `origin/main` so future pushes only require `git push`.
* **Use Case:** Publishing your local code to GitHub for the first time.
```bash
git push -u origin main
```

### `git push`
* **Explanation:** Uploads subsequent commits to the upstream branch after the link is established.
* **Use Case:** Sharing new commits with GitHub after your initial push.
```bash
git push
```

### `git pull origin main`
* **Explanation:** Downloads and merges updates from the remote GitHub repository into your local branch.
* **Use Case:** Pulling changes made by teammates or through the GitHub web UI before starting new work.
```bash
git pull origin main
```

### `git clone <URL>`
* **Explanation:** Copies an entire remote repository from GitHub to your local machine, including all commit history and branches.
* **Use Case:** Setting up the project on a new computer.
```bash
git clone https://github.com/SachinSingh201/PaperRadar.git
```

---

## 4. Branching & Collaboration

Used to isolate new experimental features or bug fixes without affecting the stable `main` branch.

### `git checkout -b <branch-name>` / `git switch -c <branch-name>`
* **Explanation:** Creates a new branch and immediately switches your working directory to it.
* **Use Case:** Developing a new feature (e.g., adding a new paper source).
```bash
git checkout -b feature/arxiv-categories
```

### `git branch`
* **Explanation:** Lists all local branches and highlights the currently active branch with an asterisk (*).
* **Use Case:** Checking which branch you are currently working on.
```bash
git branch
```

### `git checkout main` / `git switch main`
* **Explanation:** Switches your working directory back to the `main` branch.
* **Use Case:** Returning to stable code after finishing work on a feature branch.
```bash
git switch main
```

### `git merge <branch-name>`
* **Explanation:** Integrates commits from the specified branch into your current active branch.
* **Use Case:** Merging a completed and tested feature branch into `main`.
```bash
git merge feature/arxiv-categories
```

---

## 5. Inspection & History

Used to examine project history, authors, and past commits.

### `git log --oneline --graph --decorate`
* **Explanation:** Displays a compact, visual history of recent commits with their unique hashes and commit messages.
* **Use Case:** Reviewing recent project progress and milestones.
```bash
git log --oneline -n 10
```

### `git show <commit-hash>`
* **Explanation:** Shows detailed metadata and file diffs for a specific commit.
* **Use Case:** Investigating what changes were introduced in a specific commit.
```bash
git show HEAD
```

---

## 6. Undoing Changes & Troubleshooting

Used when things go wrong and you need to restore or discard changes safely.

### `git restore <file>`
* **Explanation:** Discards uncommitted changes in your working directory, reverting the file back to the last commit.
* **Use Case:** Undoing accidental edits to a file.
```bash
git restore config/settings.yaml
```

### `git restore --staged <file>`
* **Explanation:** Unstages a file from the staging area without modifying its content in your working directory.
* **Use Case:** If you ran `git add` on a file you didn't mean to commit yet.
```bash
git restore --staged .env
```

### `git stash` & `git stash pop`
* **Explanation:** Temporarily shelves (stashes) your uncommitted working directory changes so you have a clean slate, and later reapplies them.
* **Use Case:** When you need to pull latest code or switch branches without committing unfinished work.
```bash
git stash
git pull origin main
git stash pop
```

---

## 7. Commands Executed for this Project

The exact sequence of commands executed to initialize and publish **Paper Radar**:

```bash
# 1. Initialize local repository
git init

# 2. Rename default branch to main
git branch -M main

# 3. Add GitHub remote
git remote add origin https://github.com/SachinSingh201/PaperRadar.git

# 4. Check status to ensure .env and unwanted files are excluded
git status

# 5. Stage all tracked project files
git add .

# 6. Commit all files with a descriptive message
git commit -m "Initial commit: Paper Radar - AI research intelligence pipeline & static site"

# 7. Push to GitHub repository
git push -u origin main
```
