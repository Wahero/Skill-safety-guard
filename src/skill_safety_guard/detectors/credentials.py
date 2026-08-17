"""憑證洩露檢測器"""
import re
from pathlib import Path
from typing import List

from .base import BaseDetector, Finding


class CredentialsDetector(BaseDetector):
    category = "credentials"

    def detect_file(self, file_path: Path, content: str) -> List[Finding]:
        findings = []
        for rule, pattern in self._iter_compiled_rules():
            for line_no, line in enumerate(content.splitlines(), start=1):
                if line_no > 5000:  # 性能保護
                    break
                for match in pattern.finditer(line):
                    finding = Finding(
                        rule_id=rule["id"],
                        rule_name=rule["name"],
                        severity=rule.get("severity", "medium"),
                        confidence=rule.get("confidence", "medium"),
                        category=rule.get("category", "credentials"),
                        description=rule.get("description", ""),
                        remediation=rule.get("remediation", ""),
                        file_path=str(file_path),
                        line_number=line_no,
                        matched_text=match.group(0)[:50] + ("..." if len(match.group(0)) > 50 else ""),
                        context_line=line.strip()[:200],
                    )
                    findings.append(finding)
        return findings