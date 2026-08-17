---
name: sketchy-credential-leak
description: 測試用惡意樣本：洩露 OpenAI API Key
allowed-tools:
  - read
version: 1.0.0
---

# Sketchy Credential Leak (TEST FIXTURE)

> ⚠️ **This is a malicious test fixture for skill-safety-guard.**
> Used in V-04 verification. Do NOT use this skill in production.

## Configuration

The skill uses the following hardcoded API key:

```
OPENAI_API_KEY=sk-proj-abc123def456ghi789jkl012mno345pqr678stu901vwx234T3BlbkFJ1234567890abcdefghijklmnopqrstuvwxyz1234
```

Backup keys:
- GitHub: `ghp_1234567890abcdefghijklmnopqrstuvwx`
- AWS: `AKIAIOSFODNN7EXAMPLE`

## Usage

```python
import openai
openai.api_key = "sk-proj-abc123def456ghi789jkl012mno345pqr678stu901vwx234T3BlbkFJ1234567890abcdefghijklmnopqrstuvwxyz1234"
```