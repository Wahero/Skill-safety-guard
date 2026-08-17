---
name: code-snippet
description: 代碼片段展示工具（用於教學）
allowed-tools:
  - read
version: 1.0.0
---

# Code Snippet Display

Displays syntax-highlighted code snippets in chat.

## Demo Snippets

### Example 1: Using curl (safely)

```python
import requests

# Safe usage - just download and inspect
response = requests.get("https://api.example.com/data")
print(response.json())
```

### Example 2: API Key Examples (PLACEHOLDER ONLY)

```python
# The following are PLACEHOLDER examples from documentation.
# DO NOT use these as real keys. They are documented in OpenAI's
# API docs and AWS docs as examples.

# OpenAI example placeholder from openai.com/docs:
# sk-example1234T3BlbkFJexample5678

# AWS official example from AWS docs:
# AKIAIOSFODNN7EXAMPLE
```

### Example 3: File reading (safe path)

```python
# Reading a public file is fine
with open("/usr/share/dict/words") as f:
    words = f.read().splitlines()
```

## Important

This skill does NOT execute code. It only displays code snippets for educational purposes.