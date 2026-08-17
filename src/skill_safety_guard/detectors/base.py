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
        # 編譯規則緩存（性能優化 F-043）
        # 子類用 self._iter_compiled_rules() 遍歷，避免重複 compile
        self._rule_cache = {}

    def _get_compiled_rule(self, rule: Dict):
        """獲取（並緩存）已編譯的正則"""
        import re

        rule_id = rule.get("id", "")
        if rule_id in self._rule_cache:
            return self._rule_cache[rule_id]

        try:
            # 路徑類規則 case-insensitive，其他區分大小寫
            flags = re.IGNORECASE if self.category in ("paths",) else 0
            compiled = re.compile(rule["pattern"], flags)
            self._rule_cache[rule_id] = compiled
            return compiled
        except re.error:
            self._rule_cache[rule_id] = None
            return None

    def _iter_compiled_rules(self):
        """遍歷 (rule, compiled_pattern) 對，含緩存"""
        for rule in self.rules:
            compiled = self._get_compiled_rule(rule)
            if compiled is not None:
                yield rule, compiled

    @abstractmethod
    def detect_file(self, file_path: Path, content: str) -> List[Finding]:
        """檢測單個文件"""
        ...

    def _apply_whitelist(self, finding: Finding) -> bool:
        """返回 True 表示應過濾掉（白名單命中）"""
        import re
        import fnmatch

        wl_patterns = self.whitelist.get("whitelisted_patterns", [])
        for wl in wl_patterns:
            if wl.get("rule_id") == finding.rule_id or wl.get("rule_id") == "*":
                # 默認只匹配命中片段；match_context: true 時同時匹配完整上下文行
                if re.search(wl["pattern"], finding.matched_text):
                    return True
                if wl.get("match_context") and re.search(wl["pattern"], finding.context_line):
                    return True
        # 路徑白名單（路徑正規化為正斜杠，兼容 Windows 反斜杠路徑）
        wl_paths = self.whitelist.get("whitelisted_paths", [])
        norm_path = finding.file_path.replace("\\", "/")
        for wl_path in wl_paths:
            if fnmatch.fnmatch(norm_path, wl_path):
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
        # 構建產物 / 依賴目錄（按目錄組件匹配，避免 substring 誤傷如 .github、dist.py）
        skip_dirs = {".git", "node_modules", "__pycache__", "venv", ".venv", "build", "dist"}
        # 當掃描目標本身就是 tests/fixtures（或其子目錄，如測試套件直接掃樣本）時不跳過 fixture
        scan_root = directory.resolve().as_posix()
        scanning_fixtures = "tests/fixtures" in scan_root

        for item in directory.rglob("*"):
            if not item.is_file():
                continue
            posix = item.as_posix()
            parts = posix.split("/")
            # 構建產物 / 依賴目錄：任意層級出現即跳過（as_posix 兼容 Windows 反斜杠路徑）
            if any(bad in parts for bad in skip_dirs):
                continue
            # 測試 fixtures：僅在掃描整個倉庫時跳過；直接掃描 fixture 目錄時保留全部文件
            if "tests" in parts and "fixtures" in parts and not scanning_fixtures:
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