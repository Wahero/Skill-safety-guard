---
name: markdown-table
description: Markdown 表格生成助手
allowed-tools:
  - read
version: 3.0.0
---

# Markdown Table Generator

Generates Markdown tables from CSV / JSON / YAML data.

## Features

- Convert CSV to Markdown table
- Convert JSON array to Markdown table
- Sort columns
- Filter rows

## Example

```bash
# Safe example - just reading from a local file
markdown-table --input data.csv --output table.md
```

## Configuration

```yaml
# config.yaml
default_alignment: left
max_column_width: 50
```

## Safety Notes

This skill:
- ✅ Only reads files explicitly provided by the user
- ✅ Only writes Markdown files
- ❌ Does NOT read environment variables
- ❌ Does NOT access SSH keys
- ❌ Does NOT modify system files

The skill is designed to be **side-effect free**.