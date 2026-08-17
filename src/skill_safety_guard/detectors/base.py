"""檢測器基類"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict


@dataclass
class Finding:
    """單個發現"""
    rule_id: str
    rule_name: str
    severity: str  # critical, high, medium, low
    confidence: str  # high, medium, low
    category: str
    description: str
    remediation: str
    file_path: str
    line_number: int
    matched_text: str
    context_line: str = ""


@dataclass
class DetectionResult:
    """單個檢測器的結果"""
    category: str
    findings: List[Finding] = field(default_factory=list)
    scanned_files: int = 0
    error: str = ""

    @property
    def has_findings(self) -> bool:
        return len(self.findings) > 0

    @property
    def critical_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "critical")

    @property
    def high_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "high")

    @property
    def medium_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "medium")

    @property
    def low_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "low")


class BaseDetector(ABC):
    """檢測器基類"""

    category: str = "base"

    def __init__(self, rules: List[Dict], whitelist: Dict = None):
        self.rules = rules
        self.whitelist = whitelist or {}

    @abstractmethod
    def detect_file(self, file_path: Path, content: str) -> List[Finding]:
        """檢測單個文件"""
        ...

    def _apply_whitelist(self, finding: Finding) -> bool:
        """返回 True 表示應過濾掉（白名單命中）"""
        wl_patterns = self.whitelist.get("whitelisted_patterns", [])
        for wl in wl_patterns:
            if wl.get("rule_id") == finding.rule_id or wl.get("rule_id") == "*":
                import re

                if re.search(wl["pattern"], finding.matched_text):
                    return True
        # 路徑白名單
        wl_paths = self.whitelist.get("whitelisted_paths", [])
        for wl_path in wl_paths:
            import fnmatch

            if fnmatch.fnmatch(finding.file_path, wl_path):
                return True
        return False

    def _apply_confidence_demotion(self, finding: Finding) -> Finding:
        """應用置信度降級"""
        demotions = self.whitelist.get("confidence_demotions", [])
        import re

        for dem in demotions:
            if dem.get("rule_id") == finding.rule_id:
                if re.search(dem["context"], finding.context_line):
                    finding.confidence = dem["new_confidence"]
        return finding

    def detect_directory(self, directory: Path) -> DetectionResult:
        """檢測整個目錄"""
        result = DetectionResult(category=self.category)
        files = self._collect_files(directory)
        result.scanned_files = len(files)

        for fp in files:
            try:
                content = fp.read_text(encoding="utf-8")
            except (UnicodeDecodeError, PermissionError):
                continue
            except Exception as e:
                result.error = f"讀取 {fp} 失敗: {e}"
                continue

            findings = self.detect_file(fp, content)
            for f in findings:
                if not self._apply_whitelist(f):
                    f = self._apply_confidence_demotion(f)
                    result.findings.append(f)

        return result

    def _collect_files(self, directory: Path) -> List[Path]:
        """收集目錄下所有應掃描的文件"""
        files = []
        skip_dirs = {".git", "node_modules", "__pycache__", "venv", ".venv", "build", "dist", "tests/fixtures"}

        for item in directory.rglob("*"):
            if not item.is_file():
                continue
            # 跳過測試 fixtures 和構建產物
            if any(skip in str(item) for skip in skip_dirs):
                continue
            # 只掃描文本文件
            if item.suffix in {
                ".md", ".txt", ".py", ".js", ".ts", ".sh", ".bash",
                ".json", ".yaml", ".yml", ".toml", ".cfg", ".ini",
                ".html", ".css", ".jsx", ".tsx", ".vue", ".go", ".rs",
                ".java", ".kt", ".rb", ".php",
            }:
                files.append(item)
        return files