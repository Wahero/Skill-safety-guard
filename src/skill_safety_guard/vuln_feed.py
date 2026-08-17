"""漏洞情報管理（每日更新能力）

三層架構：
- Layer 1: 內置基線（vulnerabilities.json，隨倉庫更新）
- Layer 2: 遠程漏洞源（GitHub raw 拉取最新）
- Layer 3: OSV.dev 實時查詢（Google 開源漏洞庫，零日覆蓋）

使用方式：
- `safety-check --update-vulns`：手動更新漏洞庫
- 每次掃描自動 TTL 檢查（24 小時內靜默，過期提示更新）
- `--osv`：強制 OSV.dev 實時查詢
"""
import json
import os
import time
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional

# 內置漏洞庫路徑（隨倉庫更新）
BUILTIN_VULNS = Path(__file__).resolve().parent.parent.parent / "rules" / "vulnerabilities.json"

# 遠程漏洞源（GitHub raw，可更新）
REMOTE_FEED_URL = "https://raw.githubusercontent.com/Wahero/Skill-safety-guard/main/rules/vulnerabilities.json"

# 本地緩存
CACHE_DIR = Path.home() / ".skill-safety-guard"
LOCAL_VULNS_CACHE = CACHE_DIR / "vulnerabilities_cache.json"
UPDATE_META = CACHE_DIR / "vuln_update_meta.json"

# TTL
VULN_TTL_SECONDS = 24 * 3600  # 24 小時

# OSV.dev API
OSV_QUERY_URL = "https://api.osv.dev/v1/query"


# ============ 漏洞庫加載 ============

def load_vulnerabilities() -> Dict:
    """加載漏洞庫（優先本地緩存，其次內置）"""
    # 1. 本地緩存（用戶更新過的最新版）
    if LOCAL_VULNS_CACHE.exists():
        try:
            return json.loads(LOCAL_VULNS_CACHE.read_text(encoding="utf-8"))
        except Exception:
            pass

    # 2. 內置（隨倉庫）
    if BUILTIN_VULNS.exists():
        try:
            return json.loads(BUILTIN_VULNS.read_text(encoding="utf-8"))
        except Exception:
            pass

    # 3. 兜底：內置硬編碼
    return {
        "_source": "builtin-fallback",
        "vulnerabilities": [
            {
                "cve_id": "CVE-2026-54326",
                "package": "pi",
                "affected_below": "0.82.0",
                "severity": "high",
                "description": "權限升級漏洞",
                "remediation": "升級 Pi 至 0.82.0+",
                "source": "builtin",
            },
            {
                "cve_id": "CVE-2026-54327",
                "package": "pi",
                "affected_below": "0.85.0",
                "severity": "critical",
                "description": "任意文件讀取漏洞",
                "remediation": "升級 Pi 至 0.85.0+",
                "source": "builtin",
            },
        ],
    }


def get_all_cves() -> List[Dict]:
    """獲取所有 CVE 列表"""
    data = load_vulnerabilities()
    return data.get("vulnerabilities", [])


def get_vuln_source_info() -> Dict:
    """獲取漏洞庫狀態"""
    data = load_vulnerabilities()
    return {
        "source": data.get("_source_repo", "unknown"),
        "last_updated": data.get("_last_updated", "unknown"),
        "count": len(data.get("vulnerabilities", [])),
        "schema": data.get("_schema_version", "unknown"),
    }


# ============ 遠程更新 ============

def fetch_remote_feed() -> Optional[Dict]:
    """從 GitHub 拉取最新漏洞庫"""
    try:
        req = urllib.request.Request(REMOTE_FEED_URL, headers={"User-Agent": "skill-safety-guard"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data
    except Exception:
        return None


def update_vulnerabilities(force: bool = False) -> Dict:
    """更新漏洞庫（Layer 2）

    返回更新結果
    """
    # 檢查是否需要更新（TTL）
    if not force:
        meta = _read_update_meta()
        if meta and time.time() - meta.get("last_update", 0) < VULN_TTL_SECONDS:
            return {
                "updated": False,
                "reason": "在 TTL 有效期內（24h），使用緩存",
                "next_check": meta.get("last_update", 0) + VULN_TTL_SECONDS,
            }

    data = fetch_remote_feed()
    if data is None:
        return {
            "updated": False,
            "reason": "拉取遠程源失敗（網絡/離線）",
            "fallback": "使用內置漏洞庫",
        }

    # 保存到本地緩存
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    LOCAL_VULNS_CACHE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    # 更新 meta
    _write_update_meta()

    return {
        "updated": True,
        "count": len(data.get("vulnerabilities", [])),
        "source": data.get("_source_repo", "remote"),
        "last_updated": data.get("_last_updated", "now"),
    }


def _read_update_meta() -> Optional[Dict]:
    try:
        if UPDATE_META.exists():
            return json.loads(UPDATE_META.read_text(encoding="utf-8"))
    except Exception:
        pass
    return None


def _write_update_meta() -> None:
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        UPDATE_META.write_text(json.dumps({"last_update": time.time()}), encoding="utf-8")
    except Exception:
        pass


# ============ OSV.dev 實時查詢 ============

def query_osv(package: str, version: str) -> List[Dict]:
    """Layer 3: 查詢 OSV.dev 獲取該包+版本的漏洞

    返回：匹配的漏洞列表
    """
    # 解析版本
    parsed = _parse_simple_version(version)
    if parsed is None:
        return []

    payload = {"package": {"name": package}, "version": version}

    try:
        req = urllib.request.Request(
            OSV_QUERY_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "User-Agent": "skill-safety-guard"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            vulns = result.get("vulns", [])

        # 轉為內部格式
        findings = []
        for v in vulns:
            findings.append({
                "cve_id": v.get("id", "OSV-unknown"),
                "package": package,
                "severity": _osv_severity(v),
                "confidence": "high",
                "description": (v.get("summary") or v.get("details") or "")[:200],
                "remediation": "升級至修復版本",
                "source": "OSV",
                "published": v.get("published", ""),
            })
        return findings
    except Exception:
        return []


def _parse_simple_version(version: str) -> Optional[tuple]:
    """簡單版本解析"""
    import re

    match = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", version)
    if not match:
        return None
    return (
        int(match.group(1)),
        int(match.group(2)),
        int(match.group(3)) if match.group(3) else 0,
    )


def _osv_severity(vuln: Dict) -> str:
    """OSV 嚴重度映射"""
    for ref in vuln.get("severity", []):
        score = ref.get("score", "")
        if score.startswith("CVSS"):
            try:
                val = float(score.split(":")[-1])
                if val >= 9.0:
                    return "critical"
                if val >= 7.0:
                    return "high"
                if val >= 4.0:
                    return "medium"
                return "low"
            except Exception:
                pass
    return "medium"


# ============ 組合檢查 ============

def check_version_against_vulns(version_str: str) -> Dict:
    """檢查版本是否命中漏洞（Layer 1+2 內置+遠程）"""
    parsed = _parse_simple_version(version_str)
    if parsed is None:
        return {"vulnerabilities": [], "clean": True}

    vulnerabilities = []
    all_cves = get_all_cves()

    for cve in all_cves:
        # affected_below 形式
        if "affected_below" in cve:
            threshold = _parse_simple_version(cve["affected_below"])
            if threshold and parsed < threshold:
                vulnerabilities.append(cve)
        # affected_versions 形式（列表）
        elif "affected_versions" in cve:
            for v_range in cve.get("affected_versions", []):
                if v_range.startswith("<"):
                    threshold = _parse_simple_version(v_range[1:])
                    if threshold and parsed < threshold:
                        vulnerabilities.append(cve)
                        break

    return {
        "vulnerabilities": vulnerabilities,
        "clean": len(vulnerabilities) == 0,
        "checked_count": len(all_cves),
    }