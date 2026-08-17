"""關鍵系統參數修改檢測器

支援：
1. 標準正則匹配（單行）
2. 多行模式匹配（如「write + chmod +x」模式）
4. 函數名啟發式
"""
import re
from pathlib import Path
from typing import List

from .base import BaseDetector, Finding


class CriticalPathsDetector(BaseDetector):
    """檢測對關鍵系統參數（AI Agent 配置、Shell init 等）的修改/刪除"""
    category = "critical_paths"

    def detect_file(self, file_path: Path, content: str) -> List[Finding]:
        findings = []
        lines = content.splitlines()

        for rule in self.rules:
            try:
                # 多行模式需要 re.DOTALL
                flags = re.IGNORECASE | re.DOTALL if "[" in rule["pattern"] and "]" in rule["pattern"] else re.IGNORECASE
                pattern = re.compile(rule["pattern"], flags)
            except re.error:
                continue

            # 對每條規則應用
            if re.search(r"\[[\s\S]{0,200}?\][^{]*\{", rule["pattern"]):
                # 多行模式：跨行匹配
                for match in pattern.finditer(content):
                    line_no = content[:match.start()].count("\n") + 1
                    finding = self._make_finding(rule, file_path, line_no, match.group(0))
                    findings.append(finding)
            else:
                # 單行模式：逐行匹配
                seen_lines = set()
                for line_no, line in enumerate(lines, start=1):
                    if line_no > 5000:
                        break
                    for match in pattern.finditer(line):
                        if line_no in seen_lines:
                            break
                        seen_lines.add(line_no)
                        finding = self._make_finding(rule, file_path, line_no, match.group(0))
                        findings.append(finding)
                        break  # 一個規則在同一行只報一次

        return findings

    def _make_finding(self, rule: dict, file_path: Path, line_no: int, matched_text: str) -> Finding:
        return Finding(
            rule_id=rule["id"],
            rule_name=rule["name"],
            severity=rule.get("severity", "medium"),
            confidence=rule.get("confidence", "medium"),
            category=rule.get("category", "critical_paths"),
            description=rule.get("description", ""),
            remediation=rule.get("remediation", ""),
            file_path=str(file_path),
            line_number=line_no,
            matched_text=matched_text[:100] + ("..." if len(matched_text) > 100 else ""),
            context_line="",  # 跨行模式難以給單行上下文
        )