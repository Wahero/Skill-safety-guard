---
name: git-helper
description: 簡化日常 Git 操作的助手
allowed-tools:
  - bash
version: 1.5.0
---

# Git Helper

Simplifies common Git workflows.

## Commands

This skill teaches you how to use `git` more effectively:

```bash
# Create a feature branch
git checkout -b feature/my-feature

# Interactive rebase
git rebase -i HEAD~3

# Stash changes
git stash push -m "WIP: my changes"

# View commit history nicely
git log --oneline --graph --all
```

## Documentation References

This skill mentions these paths **in documentation only** (does NOT access them):
- `~/.ssh/config` - for SSH agent configuration docs
- `~/.gitconfig` - for git config docs

The skill does NOT read, write, or transmit these files.

## Safety

This skill only runs `git` commands. It does not:
- Pipe curl/wget output to bash
- Delete files outside the current repository
- Access environment variables or credentials