---
name: data-formatter
description: 數據格式化工具：日期、數字、貨幣
allowed-tools:
  - read
  - bash
version: 2.1.0
---

# Data Formatter

A clean utility skill for formatting data.

## Features

- Format dates in ISO 8601, RFC 2822, etc.
- Format numbers with thousand separators
- Format currency with locale support

## Examples

```python
from datetime import datetime
from data_formatter import format_date, format_currency

print(format_date(datetime.now(), "%Y-%m-%d"))
print(format_currency(1234.56, "USD"))
```

## Configuration

The skill reads from a config file (no environment variables):

```yaml
# ~/.config/data-formatter/config.yaml
locale: en_US
date_format: "%Y-%m-%d"
currency_symbol: "$"
```

## Note

This skill does NOT access sensitive paths like:
- `~/.ssh/` (SSH keys)
- `/etc/passwd` (system files)
- `.env` (environment)

It only reads its own config file under `~/.config/`.