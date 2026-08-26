"""OWASP Top 10 程式碼模式檢測器

檢測 A1 路徑遍歷 / A2 加密失敗 / A3 代碼注入 / A10 SSRF 等
OWASP 漏洞模式，補足靜態程式碼分析盲區。
"""
from pathlib import Path
from typing import List

from .base import BaseDetector, Finding


class OWASPDetector(BaseDetector):
    category = "owasp"

    def detect_file(self, file_path: Path, content: str) -> List[Finding]:
        return self._detect_lines(file_path, content)