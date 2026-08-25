"""憑證洩露檢測器"""
from pathlib import Path
from typing import List

from .base import BaseDetector, Finding


class CredentialsDetector(BaseDetector):
    category = "credentials"

    def detect_file(self, file_path: Path, content: str) -> List[Finding]:
        return self._detect_lines(file_path, content)
