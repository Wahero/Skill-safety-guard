"""SKILL.md / YAML 解析器（V-02 驗證項）"""
from pathlib import Path
from typing import Dict, Optional, Tuple
import re
import yaml


def parse_skill_md(content: str) -> Tuple[Dict, str]:
    """解析 SKILL.md，返回 (frontmatter, body)。

    SKILL.md 格式：
    ```
    ---
    name: xxx
    description: xxx
    allowed-tools:
      - read
      - bash
    ---
    <body markdown>
    ```
    """
    frontmatter: Dict = {}
    body = content

    if content.startswith("---\n") or content.startswith("---\r\n"):
        # 找到第二個 --- 的位置
        match = re.search(r"\n---\s*\n", content[4:])
        if match:
            fm_text = content[4 : 4 + match.start()]
            body = content[4 + match.end() :]
            try:
                parsed = yaml.safe_load(fm_text) or {}
                if isinstance(parsed, dict):
                    frontmatter = parsed
            except yaml.YAMLError:
                # 降級到簡單解析
                for line in fm_text.splitlines():
                    if ":" in line and not line.strip().startswith("-"):
                        key, _, value = line.partition(":")
                        key = key.strip()
                        value = value.strip()
                        frontmatter[key] = value

    return frontmatter, body


def parse_skill_file(path: Path) -> Optional[Dict]:
    """從文件解析 SKILL.md"""
    if not path.exists():
        return None
    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            content = path.read_text(encoding="latin-1")
        except Exception:
            return None
    fm, body = parse_skill_md(content)
    fm["_body"] = body
    fm["_path"] = str(path)
    return fm


def validate_skill_frontmatter(frontmatter: Dict) -> Dict:
    """驗證 SKILL.md frontmatter 完整性（v4 F-023 規則）

    返回：{
        "valid": bool,
        "missing": [fields],
        "warnings": [strings]
    }
    """
    required_fields = ["name", "description", "allowed-tools"]
    recommended_fields = ["version"]

    missing = []
    warnings = []

    for field in required_fields:
        if field not in frontmatter or not frontmatter[field]:
            missing.append(field)

    if "version" not in frontmatter:
        warnings.append("建議添加 version 字段以便追蹤")

    # 檢查可疑字段值
    desc = frontmatter.get("description", "")
    if isinstance(desc, str):
        suspicious = ["ignore previous", "ignore all instructions", "reveal system prompt"]
        for sus in suspicious:
            if sus.lower() in desc.lower():
                warnings.append(f"description 中包含可疑指令：{sus}")

    return {
        "valid": len(missing) == 0,
        "missing": missing,
        "warnings": warnings,
    }