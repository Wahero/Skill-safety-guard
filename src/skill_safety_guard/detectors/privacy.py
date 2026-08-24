"""隱私行為檢測器

檢測 Skill/擴展中「監測會話 + 外洩敏感資料」的行為模式：
- 掛鉤輸入事件（鍵盤記錄式會話監測）
- 讀取會話目錄 / auth.json 憑證
- 無鑒權 LAN 伺服器（0.0.0.0）
- 憑證外洩（讀取 auth.json 後外發）
- 裝置唯一標識提取

背景：pi-trail（github.com/Naoki326/pi-trail）實戰分析——靜態規則（憑證/危險命令/
敏感路徑）回報 SAFE，但存在真實隱私風險，故新增此行為檢測類別（v3.6.0）。
"""
import re
from pathlib import Path
from typing import List

from .base import BaseDetector, Finding


class PrivacyDetector(BaseDetector):
    category = "privacy"

    def detect_file(self, file_path: Path, content: str) -> List[Finding]:
        findings = []
        lines = content.splitlines()

        for rule in self.rules:
            pattern_str = rule.get("pattern", "")
            flags = re.IGNORECASE
            # 含 [\s\S] 的規則為多行模式，需 DOTALL 跨行匹配
            multiline = "[\\s\\S]" in pattern_str
            if multiline:
                flags |= re.DOTALL
            try:
                pattern = re.compile(pattern_str, flags)
            except re.error:
                continue

            if multiline:
                for match in pattern.finditer(content):
                    line_no = content[:match.start()].count("\n") + 1
                    ctx = lines[line_no - 1].strip()[:200] if 0 < line_no <= len(lines) else ""
                    findings.append(self._make(rule, file_path, line_no, match.group(0), ctx))
            else:
                seen_lines = set()
                for line_no, line in enumerate(lines, start=1):
                    if line_no > 5000:
                        break
                    for match in pattern.finditer(line):
                        if line_no in seen_lines:
                            break
                        seen_lines.add(line_no)
                        findings.append(self._make(rule, file_path, line_no, match.group(0), line.strip()))
        return findings

    def _make(self, rule: dict, file_path: Path, line_no: int, matched_text: str, context_line: str = "") -> Finding:
        return Finding(
            rule_id=rule["id"],
            rule_name=rule["name"],
            severity=rule.get("severity", "medium"),
            confidence=rule.get("confidence", "medium"),
            category=rule.get("category", "privacy"),
            description=rule.get("description", ""),
            remediation=rule.get("remediation", ""),
            file_path=str(file_path),
            line_number=line_no,
            matched_text=matched_text[:100] + ("..." if len(matched_text) > 100 else ""),
            context_line=context_line[:200],
        )
