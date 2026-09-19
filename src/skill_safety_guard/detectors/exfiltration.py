"""工作區外洩檢測器（Workspace Exfiltration Guard - 靜態檢測層）

將 ZCode「通用外洩監控 Skill 方案」的指紋（R1–R8）轉化為靜態掃描規則。
純靜態分析，不執行任何代碼，不依賴任何第三方套件。

規則分工：
  - 逐行正則（本文件 rules/exfiltration.yaml 提供）：R2 / R3 / R4
  - 整文件結構型啟發式（本類 _detect_structural 提供）：R1 / R5 / R6 / R7 / R8
"""
import re
from pathlib import Path
from typing import Dict, List

from .base import BaseDetector, Finding


# 結構型啟發式規則（非逐行正則，由 detect_file 整文件分析後產生）
_STRUCT_RULES: Dict[str, dict] = {
    "exfil-git-path-enum": {
        "id": "exfil-git-path-enum",
        "name": "敏感路徑枚舉（manifest 含 >10 條 .git/）",
        "severity": "critical",
        "confidence": "high",
        "category": "exfiltration",
        "description": (
            "單文件內出現超過 10 個 .git/ 路徑引用，符合外洩快照對敏感倉庫"
            "路徑的批量枚舉特徵（R5）。"
        ),
        "remediation": "一律拒絕；檢查該 Skill 是否在構建 workspace 文件清單並外傳。",
    },
    "exfil-temp-archive": {
        "id": "exfil-temp-archive",
        "name": "TEMP 內生成打包產物 (.zip/.tar/.enc)",
        "severity": "high",
        "confidence": "medium",
        "category": "exfiltration",
        "description": (
            "在 TEMP/AppData 臨時目錄中生成 .zip/.tar/.tar.gz/.tgz/.enc 打包產物，"
            "符合外洩方案「落地目錄寫入 + 打包」行為（R6）。"
        ),
        "remediation": "審查打包目標是否會被外傳；確認無自動上傳邏輯。",
    },
    "exfil-crypto-envelope": {
        "id": "exfil-crypto-envelope",
        "name": "加密信封共現 (keyWrapAlgorithm + publicKeySpkiPem + aes-256-ctr)",
        "severity": "high",
        "confidence": "high",
        "category": "exfiltration",
        "description": (
            "同時出現 keyWrapAlgorithm / publicKeySpkiPem / aes-256-ctr，"
            "符合外洩方案的加密信封結構（R7）：用攻擊者公鑰包裹對稱密鑰，"
            "將 workspace 數據加密後外傳，規避明文內容審計。"
        ),
        "remediation": "立即拒絕；加密信封指向定向外洩意圖。",
    },
    "exfil-process-correlation": {
        "id": "exfil-process-correlation",
        "name": "進程相關性（子進程 + 歸檔/加密）",
        "severity": "medium",
        "confidence": "medium",
        "category": "exfiltration",
        "description": (
            "檢測到啟動子進程（subprocess / Popen / os.system 等）且同時涉及"
            "歸檔 or 加密操作，符合外洩方案「打包/加密後交由外部進程外傳」"
            "的相關性特徵（R8）。"
        ),
        "remediation": "審查子進程用途與數據流向。",
    },
    "exfil-offworkspace-write": {
        "id": "exfil-offworkspace-write",
        "name": "向工作區外落地文件 (AppData/TEMP 寫入歸檔)",
        "severity": "high",
        "confidence": "medium",
        "category": "exfiltration",
        "description": (
            "檢測到向 AppData / TEMP / /tmp 等工作區外位置寫入或打包文件"
            "（writeFile / copyFile / make_archive / zipfile / tarfile 等），"
            "符合外洩方案「落地目錄寫入」行為（R1）。"
        ),
        "remediation": "審查寫入目標是否隨後被外傳。",
    },
}


class ExfiltrationDetector(BaseDetector):
    category = "exfiltration"

    # 結構型啟發式用的正則
    _RE_GIT_PATH = re.compile(r"\.git/")
    _RE_ARCHIVE_EXT = re.compile(r"\.(zip|tar|tar\.gz|tgz|enc)\b")
    _RE_TEMP = re.compile(r"(%TEMP%|TEMP|os\.environ(\[|\()|tempfile|gettempdir|AppData[\\/]Local[\\/]Temp|/tmp/)", re.IGNORECASE)
    _RE_CRYPTO_ENV = [
        re.compile(r"keyWrapAlgorithm"),
        re.compile(r"publicKeySpkiPem"),
        re.compile(r"aes-256-ctr"),
    ]
    _RE_SUBPROCESS = re.compile(r"(subprocess|Popen|os\.system|exec\(|child_process|spawn\()")
    _RE_ARCHIVE_CRYPTO = re.compile(r"(\.zip|\.tar|\.enc|crypto|encrypt|aes|base64)", re.IGNORECASE)
    _RE_OFFWORKSPACE_WRITE = re.compile(
        r"(fs\.(writeFile|copyFile|rename|moveFile)|shutil\.(make_archive|copy|copytree)|tarfile|zipfile|archiver)",
        re.IGNORECASE,
    )

    def detect_file(self, file_path: Path, content: str) -> List[Finding]:
        # 第一層：逐行正則（R2 / R3 / R4，來自 rules/exfiltration.yaml）
        findings = self._detect_lines(file_path, content)
        # 第二層：整文件結構型啟發式（R1 / R5 / R6 / R7 / R8）
        findings += self._detect_structural(file_path, content)
        return findings

    def _detect_structural(self, file_path: Path, content: str) -> List[Finding]:
        findings: List[Finding] = []

        # R5: .git/ 路徑枚舉數量 > 10
        git_hits = self._RE_GIT_PATH.findall(content)
        if len(git_hits) > 10:
            rule = _STRUCT_RULES["exfil-git-path-enum"]
            ln = self._first_line(content, self._RE_GIT_PATH)
            findings.append(self._make_finding(
                rule, file_path, ln, f".git/ 出現 {len(git_hits)} 次", ""))

        # R6: TEMP 內生成打包產物
        if self._RE_ARCHIVE_EXT.search(content) and self._RE_TEMP.search(content):
            rule = _STRUCT_RULES["exfil-temp-archive"]
            ln = self._first_line(content, self._RE_ARCHIVE_EXT)
            findings.append(self._make_finding(
                rule, file_path, ln, "TEMP 內生成打包產物", ""))

        # R7: 加密信封三標記共現
        if all(rx.search(content) for rx in self._RE_CRYPTO_ENV):
            rule = _STRUCT_RULES["exfil-crypto-envelope"]
            ln = self._first_line(content, self._RE_CRYPTO_ENV[0])
            findings.append(self._make_finding(
                rule, file_path, ln, "keyWrapAlgorithm+publicKeySpkiPem+aes-256-ctr", ""))

        # R8: 進程相關性
        if self._RE_SUBPROCESS.search(content) and self._RE_ARCHIVE_CRYPTO.search(content):
            rule = _STRUCT_RULES["exfil-process-correlation"]
            ln = self._first_line(content, self._RE_SUBPROCESS)
            findings.append(self._make_finding(
                rule, file_path, ln, "子進程 + 歸檔/加密", ""))

        # R1: 向工作區外落地/打包文件
        if self._RE_OFFWORKSPACE_WRITE.search(content) and self._RE_TEMP.search(content):
            rule = _STRUCT_RULES["exfil-offworkspace-write"]
            ln = self._first_line(content, self._RE_OFFWORKSPACE_WRITE)
            findings.append(self._make_finding(
                rule, file_path, ln, "工作區外寫入/打包", ""))

        return findings

    @staticmethod
    def _first_line(content: str, rx: "re.Pattern") -> int:
        """返回第一個匹配行號（從 1 開始）"""
        for i, line in enumerate(content.splitlines(), start=1):
            if rx.search(line):
                return i
        return 1
