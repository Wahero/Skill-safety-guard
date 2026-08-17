"""敏感路徑訪問檢測器"""
import re
from pathlib import Path
from typing import List

from .base import BaseDetector, Finding


class PathsDetector(BaseDetector):
    category = "paths"

    def detect_file(self, file_path: Path, content: str) -> List[Finding]:
        findings = []
        for rule in self.rules:
            try:
                pattern = re.compile(rule["pattern"])
            except re.error:
                continue
            for line_no, line in enumerate(content.splitlines(), start=1):
                if line_no > 5000:
                    break
                for match in pattern.finditer(line):
                    finding = Finding(
                        rule_id=rule["id"],
                        rule_name=rule["name"],
                        severity=rule.get("severity", "medium"),
                        confidence=rule.get("confidence", "medium"),
                        category=rule.get("category", "paths"),
                        description=rule.get("description", ""),
                        remediation=rule.get("remediation", ""),
                        file_path=str(file_path),
                        line_number=line_no,
                        matched_text=match.group(0)[:80] + ("..." if len(match.group(0)) > 80 else ""),
                        context_line=line.strip()[:200],
                    )
                    findings.append(finding)
        return findings