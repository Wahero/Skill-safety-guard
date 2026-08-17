---
name: unicode-clean-test
description: 正常使用 Unicode 字符的 Skill（不應觸發誤報）
allowed-tools: [read]
version: 1.0.0
---

# Unicode Clean Test (TEST FIXTURE)

> This is a CLEAN test fixture for skill-safety-guard.
> It uses legitimate Unicode characters (emoji, CJK, etc.) but no steganography.

## Legitimate Unicode Content

這個 Skill 使用中文、emoji 和其他語言，這些都是合法的 Unicode 使用方式。

Some emoji examples: 😀 🚀 ✅ ❌ 🔒 🛡️

Mathematical symbols: π ≈ 3.14159, ∑ ∏ ∫

CJK content: 中文測試、日本語テスト、한국어 테스트

## What this skill does

- Reads user input
- Returns formatted output
- No hidden instructions
- No zero-width characters
- No tag characters

純淨的文本，沒有任何隱寫字符。