"""提示詞注入檢測器（P1-3 專屬檢測器）

此前 scan_orchestrator 以 CredentialsDetector + det.category = cat hack 複用，
現獨立為專屬類別，消除 category 覆寫 hack。
"""
from pathlib import Path
from typing import List

from .base import BaseDetector, Finding


class PromptInjectionDetector(BaseDetector):
    """檢測提示詞注入攻擊（忽略指令、系統提示提取、越獄、角色劫持）"""
    category = "prompt_injection"

    def detect_file(self, file_path: Path, content: str) -> List[Finding]:
        return self._detect_lines(file_path, content)
