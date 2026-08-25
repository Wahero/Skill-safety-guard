"""危險 Shell 命令檢測器"""
from pathlib import Path
from typing import List

from .base import BaseDetector, Finding


class ShellDetector(BaseDetector):
    category = "shell"

    def detect_file(self, file_path: Path, content: str) -> List[Finding]:
        return self._detect_lines(file_path, content)
