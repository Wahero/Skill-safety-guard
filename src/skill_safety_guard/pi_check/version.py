"""Pi Agent 版本 CVE 檢測（V-03 + F-005）

已知 Pi Agent CVEs：
- CVE-2026-54326: < 0.82.0  - 權限升級漏洞
- CVE-2026-54327: < 0.85.0  - 任意文件讀取漏洞
"""
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional


# 已知漏洞數據庫（v0.1.0）
# 格式：[(cve_id, affected_below, severity, description), ...]
KNOWN_CVES = [
    {
        "cve_id": "CVE-2026-54326",
        "affected_below": "0.82.0",
        "severity": "high",
        "description": "權限升級漏洞：skill 聲明的 allowed-tools 邊界可被繞過",
        "remediation": "升級 Pi 至 0.82.0 或更高版本",
    },
    {
        "cve_id": "CVE-2026-54327",
        "affected_below": "0.85.0",
        "severity": "critical",
        "description": "任意文件讀取漏洞：特定 SKILL.md frontmatter 可觸發讀取系統任意文件",
        "remediation": "升級 Pi 至 0.85.0 或更高版本",
    },
]


def _parse_version(version_str: str) -> tuple:
    """解析版本號為 (major, minor, patch) 元組"""
    match = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", version_str)
    if not match:
        return (0, 0, 0)
    return (
        int(match.group(1)),
        int(match.group(2)),
        int(match.group(3)) if match.group(3) else 0,
    )


def _is_below(current: tuple, threshold_str: str) -> bool:
    """判斷 current 是否低於 threshold"""
    threshold = _parse_version(threshold_str)
    return current < threshold


def get_pi_version() -> Dict:
    """獲取 Pi 版本信息

    返回：
    {
        "available": bool,
        "version": str,
        "parsed": tuple,
        "error": str
    }
    """
    # 緩存（性能優化 F-043）：避免每次掃描都調用 pi --version
    cached = _read_version_cache()
    if cached:
        return cached

    # Windows 下需使用 shell=True 才能解析 .CMD 擴展名
    # Linux/Mac 直接執行二進制
    use_shell = sys.platform.startswith("win")

    try:
        result = subprocess.run(
            ["pi", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            shell=use_shell,
        )
        output = (result.stdout + result.stderr).strip()
        version_str = output.split("\n")[0] if output else ""
        info = {
            "available": True,
            "version": version_str,
            "parsed": _parse_version(version_str),
            "error": "",
        }
        _write_version_cache(info)
        return info
    except FileNotFoundError:
        return {
            "available": False,
            "version": "",
            "parsed": (0, 0, 0),
            "error": "pi 命令未找到。請確保 Pi 已正確安裝並在 PATH 中",
        }
    except subprocess.TimeoutExpired:
        return {
            "available": False,
            "version": "",
            "parsed": (0, 0, 0),
            "error": "pi --version 超時",
        }
    except Exception as e:
        return {
            "available": False,
            "version": "",
            "parsed": (0, 0, 0),
            "error": str(e),
        }


def _version_cache_path() -> Path:
    """版本緩存文件路徑"""
    cache_dir = Path.home() / ".skill-safety-guard"
    return cache_dir / "pi_version.json"


def _read_version_cache() -> Optional[Dict]:
    """讀取版本緩存（1 小時內有效）"""
    try:
        cache_path = _version_cache_path()
        if not cache_path.exists():
            return None
        import json as _json
        data = _json.loads(cache_path.read_text(encoding="utf-8"))
        # 檢查是否過期（1 小時）
        if time.time() - data.get("cached_at", 0) > 3600:
            return None
        return {
            "available": data.get("available", False),
            "version": data.get("version", ""),
            "parsed": tuple(data.get("parsed", [0, 0, 0])),
            "error": data.get("error", ""),
        }
    except Exception:
        return None


def _write_version_cache(info: Dict) -> None:
    """寫入版本緩存"""
    try:
        import json as _json
        cache_path = _version_cache_path()
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "available": info.get("available", False),
            "version": info.get("version", ""),
            "parsed": list(info.get("parsed", (0, 0, 0))),
            "error": info.get("error", ""),
            "cached_at": time.time(),
        }
        cache_path.write_text(_json.dumps(data), encoding="utf-8")
    except Exception:
        pass


def check_pi_version(use_osv: bool = False) -> Dict:
    """執行 Pi 版本 CVE 檢查（F-005 + 每日漏洞情報）

    使用三層漏洞情報源：
    - Layer 1/2: 內置 + 遠程漏洞庫（vuln_feed）
    - Layer 3: OSV.dev 實時查詢（可選，--osv）

    返回：
    {
        "pi_available": bool,
        "version": str,
        "vulnerabilities": [{cve_id, severity, description, remediation}],
        "clean": bool,
        "vuln_source": str,
        "osv_checked": bool
    }
    """
    info = get_pi_version()
    vulnerabilities = []
    osv_checked = False

    if info["available"]:
        # Layer 1+2: 內置 + 遠程漏洞庫
        from ..vuln_feed import check_version_against_vulns, get_vuln_source_info

        result = check_version_against_vulns(info["version"])
        vulnerabilities = result["vulnerabilities"]

        # Layer 3: OSV.dev 實時查詢（可選）
        if use_osv:
            from ..vuln_feed import query_osv

            # 查詢 pi 和 pi-coding-agent 包
            for pkg in ["pi", "@earendil-works/pi-coding-agent"]:
                osv_findings = query_osv(pkg, info["version"])
                # 去重（按 cve_id）
                existing_ids = {v.get("cve_id") for v in vulnerabilities}
                for f in osv_findings:
                    if f["cve_id"] not in existing_ids:
                        vulnerabilities.append(f)
                        existing_ids.add(f["cve_id"])
            osv_checked = True

    source_info = {}
    try:
        from ..vuln_feed import get_vuln_source_info
        source_info = get_vuln_source_info()
    except Exception:
        pass

    return {
        "pi_available": info["available"],
        "version": info["version"],
        "vulnerabilities": vulnerabilities,
        "clean": len(vulnerabilities) == 0,
        "error": info["error"],
        "vuln_source": source_info.get("source", "builtin"),
        "vuln_count": source_info.get("count", len(KNOWN_CVES)),
        "osv_checked": osv_checked,
    }