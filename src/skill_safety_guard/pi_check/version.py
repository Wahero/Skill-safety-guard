"""Pi Agent 版本 CVE 檢測（V-03 + F-005）

已知 Pi Agent CVEs：
- CVE-2026-54326: < 0.82.0  - 權限升級漏洞
- CVE-2026-54327: < 0.85.0  - 任意文件讀取漏洞
"""
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List


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
        return {
            "available": True,
            "version": version_str,
            "parsed": _parse_version(version_str),
            "error": "",
        }
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


def check_pi_version() -> Dict:
    """執行 Pi 版本 CVE 檢查（F-005）

    返回：
    {
        "pi_available": bool,
        "version": str,
        "vulnerabilities": [{cve_id, severity, description, remediation}],
        "clean": bool
    }
    """
    info = get_pi_version()
    vulnerabilities = []

    if info["available"]:
        for cve in KNOWN_CVES:
            if _is_below(info["parsed"], cve["affected_below"]):
                vulnerabilities.append(cve)

    return {
        "pi_available": info["available"],
        "version": info["version"],
        "vulnerabilities": vulnerabilities,
        "clean": len(vulnerabilities) == 0,
        "error": info["error"],
    }