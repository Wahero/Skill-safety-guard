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
    fp_reason: str = ""  # 非空 = 判定為誤報，內容為誤報原因


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

    # ------------------------------------------------------------------
    # 統一 Finding 構建與逐行檢測（P1-2 / P1-3）
    # ------------------------------------------------------------------

    def _make_finding(
        self,
        rule: Dict,
        file_path: Path,
        line_number: int,
        matched_text: str,
        context_line: str = "",
    ) -> Finding:
        """統一 Finding 構建（P1-3）

        所有檢測器子類通過此方法生成 Finding，消除重複代碼。
        matched_text 截斷 ≤100 字符，context_line 截斷 ≤200 字符。
        """
        mt = matched_text or ""
        return Finding(
            rule_id=rule.get("id", ""),
            rule_name=rule.get("name", ""),
            severity=rule.get("severity", "medium"),
            confidence=rule.get("confidence", "medium"),
            category=rule.get("category", self.category),
            description=rule.get("description", ""),
            remediation=rule.get("remediation", ""),
            file_path=str(file_path),
            line_number=line_number,
            matched_text=mt[:100] + ("..." if len(mt) > 100 else ""),
            context_line=(context_line or "")[:200],
        )

    def _detect_lines(self, file_path: Path, content: str) -> List[Finding]:
        """標準逐行正則檢測（P1-2 統一遍歷）

        credentials / shell / installed_extensions / prompt_injection 共用此邏輯。
        需要特殊處理的子類（paths 的 FP 判定、critical_paths 的多行模式、
        unicode 的字符格式化）應覆寫 detect_file 並直接呼叫 _make_finding。
        """
        findings: List[Finding] = []
        for rule, pattern in self._iter_compiled_rules():
            for line_no, line in enumerate(content.splitlines(), start=1):
                if line_no > 5000:
                    break
                for match in pattern.finditer(line):
                    findings.append(self._make_finding(
                        rule, file_path, line_no,
                        match.group(0), line.strip(),
                    ))
        return findings

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

    def detect_directory(self, directory: Path, include_self: bool = False) -> DetectionResult:
        """檢測整個目錄

        include_self=True 時包含本工具自身（skill-safety-guard）目錄；
        預設 False 跳過自身，避免掃描時掃到自己產生大量誤報。
        """
        result = DetectionResult(category=self.category)
        files = self._collect_files(directory, include_self=include_self)
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

    def _collect_files(self, directory: Path, include_self: bool = False) -> List[Path]:
        """收集目錄下所有應掃描的文件

        include_self=False（預設）時跳過本工具自身目錄（skill-safety-guard），
        避免掃描時掃到自己產生大量誤報；True 時包含自身。
        """
        files = []
        # 構建產物 / 依賴目錄（按目錄組件匹配，避免 substring 誤傷如 .github、dist.py）
        skip_dirs = {".git", "node_modules", "__pycache__", "venv", ".venv", "build", "dist"}
        # 本工具自身目錄：預設跳過（避免掃描時掃到自己），僅 --chk-myself 時包含
        # base.py 位於 <root>/src/skill_safety_guard/detectors/base.py → 向上 4 層為 <root>
        own_dir = Path(__file__).resolve().parent.parent.parent.parent
        root_res = directory.resolve()
        # 自身目錄是否位於掃描目標內（即掃描根是自身目錄的祖先）——此時才需跳過自身子树；
        # 若掃描根自身就是本工具目錄（或在其內部，如掃 tests/fixtures 樣本），不跳。
        own_is_subtree = False
        try:
            if root_res.is_relative_to(own_dir):
                # 掃描根在自身內部（掃自身 or tests/fixtures）→ 由 include_self 決定
                own_is_subtree = False
            elif own_dir.is_relative_to(root_res):
                # 自身目錄在掃描根內部（掃父目錄）→ 需跳過自身子树
                own_is_subtree = True
        except ValueError:
            pass
        # 當掃描目標本身就是 tests/fixtures（或其子目錄，如測試套件直接掃樣本）時不跳過 fixture
        scan_root = directory.resolve().as_posix()
        scanning_fixtures = "tests/fixtures" in scan_root

        for item in directory.rglob("*"):
            if not item.is_file():
                continue
            posix = item.as_posix()
            parts = posix.split("/")
            if any(bad in parts for bad in skip_dirs):
                continue
            # 跳過本工具自身目錄（僅當自身是掃描目標的子樹時，且未指定 --chk-myself）
            if not include_self and own_is_subtree:
                try:
                    if item.resolve().is_relative_to(own_dir):
                        continue
                except (ValueError, OSError):
                    pass
            # 測試 fixtures：僅在掃描整個倉庫時跳過；直接掃描 fixture 目錄時保留全部文件
            if "tests" in parts and "fixtures" in parts and not scanning_fixtures:
                continue
            # 只掃描文本文件
            if item.suffix in {
                ".md", ".txt", ".py", ".js", ".ts", ".sh", ".bash",
                ".json", ".yaml", ".yml", ".toml", ".cfg", ".ini",
                ".html", ".css", ".jsx", ".tsx", ".vue", ".go", ".rs",
                ".java", ".kt", ".rb", ".php",
                ".mjs", ".cjs",
            }:
                files.append(item)
        return files