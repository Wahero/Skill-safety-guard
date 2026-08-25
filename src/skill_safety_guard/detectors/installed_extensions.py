"""已安裝擴展審計檢測器（P1-3 專屬檢測器）

此前 scan_orchestrator 以 CredentialsDetector + det.category = cat hack 複用，
現獨立為專屬類別，消除 category 覆寫 hack。
"""
from pathlib import Path
from typing import List

from .base import BaseDetector, Finding


class InstalledExtensionsDetector(BaseDetector):
    """檢測已安裝擴展中的危險行為（eval/exec、寫主目錄、危險 shell）"""
    category = "installed_extensions"

    def detect_file(self, file_path: Path, content: str) -> List[Finding]:
        return self._detect_lines(file_path, content)
