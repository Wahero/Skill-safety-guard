"""敏感路徑訪問檢測器"""
import re
from pathlib import Path
from typing import List

from .base import BaseDetector, Finding

# 環境變數讀取模式（非 .env 檔案訪問，屬誤報）
ENV_READ_PATTERNS = [
    re.compile(r"os\.environ\.get\s*\("),
    re.compile(r"os\.getenv\s*\("),
    re.compile(r"environ\s*\[.*\]"),
    re.compile(r"os\.environ\s*\("),
    re.compile(r"getenv\s*\("),
]


class PathsDetector(BaseDetector):
    category = "paths"

    def detect_file(self, file_path: Path, content: str) -> List[Finding]:
        findings = []
        for rule, pattern in self._iter_compiled_rules():
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
                    # 誤報判定：env 規則命中但實際是讀取環境變數（非 .env 檔案）
                    if rule["id"] == "path-env-file":
                        if any(p.search(line) for p in ENV_READ_PATTERNS):
                            finding.fp_reason = (
                                "命中「.env file access」但實際是透過 os.environ.get()/os.getenv() "
                                "讀取環境變數取得 API 憑證——這是安全做法（憑證不寫入原始碼），非訪問 .env 檔案，判定為誤報"
                            )
                            finding.severity = "low"
                            finding.confidence = "low"
                    findings.append(finding)
        return findings