"""多框架 + CI/CD 安全檢測器

v3.9.0 新增：Windsurf / Goose / Devin / Copilot / Roo Code 等框架配置
+ GitHub Actions / GitLab CI / Jenkinsfile + Dockerfile / docker-compose / K8s
規則混合了 critical_paths / shell / privacy / credentials 類別，
統一通過本檢測器並利用現有 Finding 結構報告。
"""
from pathlib import Path
from typing import List, Dict

from .base import BaseDetector, Finding


class MultiFrameworkDetector(BaseDetector):
    category = "multi_framework"

    def detect_file(self, file_path: Path, content: str) -> List[Finding]:
        return self._detect_lines(file_path, content)