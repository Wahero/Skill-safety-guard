"""原生檔案刪除操作檢測器（Rust / Python / Go / PowerShell）

檢測非 Shell 層面的檔案/目錄刪除 API，補足 dangerous_shell.yaml
僅覆蓋 Shell 命令的盲區。
"""
from pathlib import Path
from typing import List

from .base import BaseDetector, Finding


class NativeFileOpsDetector(BaseDetector):
    category = "native_file_ops"

    def detect_file(self, file_path: Path, content: str) -> List[Finding]:
        return self._detect_lines(file_path, content)