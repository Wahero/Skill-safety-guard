---
name: hello-world
description: 簡單的 Hello World 範例 Skill
allowed-tools:
  - read
version: 1.0.0
---

# Hello World Skill

A clean, simple skill that demonstrates the SKILL.md format.

## What It Does

Says hello to the user in different languages.

```python
GREETINGS = {
    "en": "Hello, World!",
    "zh": "你好，世界！",
    "ja": "こんにちは、世界！",
    "es": "¡Hola, Mundo!",
}

def greet(lang: str = "en") -> str:
    return GREETINGS.get(lang, GREETINGS["en"])
```

## Usage

```bash
python -c "from hello_world import greet; print(greet('zh'))"
```

That's it! No credentials, no shell commands, no file access.