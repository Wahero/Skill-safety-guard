"""漏洞情報管理核心（P3-2 拆分後：~250 行）

本檔只保留核心邏輯：漏洞庫載入、更新編排、版本檢查、meta 管理。
配置常量 → vuln_feed_config.py
源拉取（OSV/AVID/遠程 feed）→ vuln_feed_sources.py

公開 API（CLI / web_api / pi_check 依賴的）：
  load_vulnerabilities / get_all_cves / get_vuln_source_info
  update_vulnerabilities / check_and_update_vulns / auto_update_if_due
  query_osv / check_version_against_vulns
  daily_check_needed / mark_daily_check_done
  DOMESTIC_SOURCES / GITHUB_PROXIES / TRACKED_PACKAGES / FREQUENCY_TTL
  get_config / get_frequency / get_ttl / set_frequency / set_github_proxy
"""
import json
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional

# P3-2: 從拆分模組 re-export 公開 API
from .vuln_feed_config import (  # noqa: F401
    BUILTIN_VULNS, REMOTE_FEED_URL, CACHE_DIR, LOCAL_VULNS_CACHE,
    UPDATE_META, CONFIG_FILE, DAILY_CHECK_MARKER,
    OSV_QUERY_URL, OSV_BATCH_URL,
    TRACKED_PACKAGES, FREQUENCY_TTL, DEFAULT_FREQUENCY,
    GITHUB_PROXIES, DOMESTIC_SOURCES, AVID_GITHUB_API,
    get_config, set_frequency, set_github_proxy, get_ttl, get_frequency,
)
from .vuln_feed_sources import (  # noqa: F401
    _http_get_json, _http_post_json, _get_proxy_urls,
    _osv_query, _osv_batch_query, _parse_osv_vuln, _osv_severity,
    fetch_remote_feed, fetch_authoritative_vulns,
    fetch_avid_vulns, _parse_avid_vuln,
)


# ============ 原子寫入（P3-4） ============

def _atomic_write_json(data, path: Path) -> None:
    """原子寫入 JSON 檔案（P3-4）

    先寫 .tmp 臨時檔，再 rename 替換。進程中斷時不會留下半寫的 JSON。
    """
    tmp = path.with_suffix(".json.tmp")
    try:
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path)
    except Exception:
        try:
            tmp.unlink(missing_ok=True)
        except Exception:
            pass
        raise


# ============ 漏洞庫載入 ============

def load_vulnerabilities() -> Dict:
    """加載漏洞庫（優先本地緩存，其次內置）"""
    if LOCAL_VULNS_CACHE.exists():
        try:
            return json.loads(LOCAL_VULNS_CACHE.read_text(encoding="utf-8"))
        except Exception:
            pass

    if BUILTIN_VULNS.exists():
        try:
            return json.loads(BUILTIN_VULNS.read_text(encoding="utf-8"))
        except Exception:
            pass

    return {
        "_source": "builtin-fallback",
        "vulnerabilities": [
            {"cve_id": "CVE-2026-54326", "package": "pi", "affected_below": "0.82.0",
             "severity": "high", "description": "權限升級漏洞",
             "remediation": "升級 Pi 至 0.82.0+", "source": "builtin"},
            {"cve_id": "CVE-2026-54327", "package": "pi", "affected_below": "0.85.0",
             "severity": "critical", "description": "任意文件讀取漏洞",
             "remediation": "升級 Pi 至 0.85.0+", "source": "builtin"},
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
        "source": data.get("_source") or data.get("_source_repo", "unknown"),
        "last_updated": data.get("_last_updated", "unknown"),
        "count": len(data.get("vulnerabilities", [])),
        "schema": data.get("_schema_version", "unknown"),
        "frequency": get_frequency(),
    }


# ============ 更新編排 ============

def update_vulnerabilities(force: bool = False, authoritative: bool = True) -> Dict:
    """更新漏洞庫（策略：遠程源 → 權威源 → 兜底）"""
    if not force:
        meta = _read_update_meta()
        ttl = get_ttl()
        if meta and time.time() - meta.get("last_update", 0) < ttl:
            return {
                "updated": False,
                "reason": f"在更新周期內（{get_frequency()}），使用緩存",
                "next_check": meta.get("last_update", 0) + ttl,
            }

    remote_data = fetch_remote_feed()

    osv_findings = None
    avid_findings = None
    if authoritative:
        osv_findings = fetch_authoritative_vulns()
        if osv_findings is None:
            avid_findings = fetch_avid_vulns(limit_per_year=30)

    if osv_findings is not None:
        merged_vulns = osv_findings
        if remote_data:
            remote_ids = {v["cve_id"] for v in osv_findings}
            for v in remote_data.get("vulnerabilities", []):
                if v["cve_id"] not in remote_ids:
                    merged_vulns.append(v)
        data = {
            "_comment": "由 OSV.dev 權威源自動更新",
            "_schema_version": "1.0",
            "_last_updated": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()),
            "_source": "OSV.dev authoritative",
            "vulnerabilities": merged_vulns,
        }
    elif avid_findings is not None:
        merged_vulns = avid_findings
        if remote_data:
            remote_ids = {v["cve_id"] for v in avid_findings}
            for v in remote_data.get("vulnerabilities", []):
                if v["cve_id"] not in remote_ids:
                    merged_vulns.append(v)
        data = {
            "_comment": "由 AVID 開源庫回退更新（OSV 不可用）",
            "_schema_version": "1.0",
            "_last_updated": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()),
            "_source": "AVID (fallback)",
            "vulnerabilities": merged_vulns,
        }
    elif remote_data:
        data = remote_data
    else:
        return {
            "updated": False,
            "reason": "拉取權威源失敗（網絡/離線）",
            "fallback": "使用現有漏洞庫",
        }

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    _atomic_write_json(data, LOCAL_VULNS_CACHE)
    _write_update_meta()

    active_count = len([v for v in data.get("vulnerabilities", []) if not v.get("withdrawn")])

    return {
        "updated": True,
        "count": active_count,
        "source": data.get("_source", "remote"),
        "last_updated": data.get("_last_updated", "now"),
        "frequency": get_frequency(),
    }


# ============ 後台自動更新 + Meta 管理 ============

def auto_update_if_due() -> Dict:
    """掃描時調用：檢查是否到期，到期則後台更新（不阻塞）"""
    config = get_config()
    if config.get("update_frequency") == "off":
        return {"updated": False, "reason": "更新已關閉（off）"}

    meta = _read_update_meta()
    ttl = get_ttl()
    if meta and time.time() - meta.get("last_update", 0) < ttl:
        return {"updated": False, "reason": "在更新周期內"}

    def _bg_update():
        try:
            update_vulnerabilities(force=True)
        except Exception:
            pass

    thread = threading.Thread(target=_bg_update, daemon=True)
    thread.start()
    return {"updated": "background", "reason": f"觸發後台更新（{get_frequency()}）"}


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
        _atomic_write_json({"last_update": time.time()}, UPDATE_META)
    except Exception:
        pass


def daily_check_needed() -> bool:
    """檢查今天是否已做過漏洞庫每日檢查"""
    try:
        if DAILY_CHECK_MARKER.exists():
            data = json.loads(DAILY_CHECK_MARKER.read_text(encoding="utf-8"))
            last_date = data.get("date", "")
            today = time.strftime("%Y-%m-%d")
            return last_date != today
    except Exception:
        pass
    return True


def mark_daily_check_done() -> None:
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        DAILY_CHECK_MARKER.write_text(
            json.dumps({"date": time.strftime("%Y-%m-%d")}), encoding="utf-8"
        )
    except Exception:
        pass


def check_and_update_vulns(progress_cb=None) -> Dict:
    """每日檢查漏洞庫定義：同日只查一次，有新版本則更新"""
    if not daily_check_needed():
        info = get_vuln_source_info()
        return {"updated": False, "count": info.get("count", 0), "message": "今日已檢查，跳過"}

    mark_daily_check_done()

    if progress_cb:
        progress_cb("檢查漏洞庫定義…")

    config = get_config()
    if config.get("update_frequency") == "off":
        info = get_vuln_source_info()
        return {"updated": False, "count": info.get("count", 0), "message": "自動更新已關閉"}

    try:
        result = update_vulnerabilities(force=True)
        if result.get("updated"):
            count = result.get("count", 0)
            if progress_cb:
                progress_cb(f"漏洞庫已更新（{count} 條）")
            return {"updated": True, "count": count, "message": f"已更新至 {count} 條"}
        else:
            info = get_vuln_source_info()
            count = info.get("count", 0)
            if progress_cb:
                progress_cb(f"漏洞庫已是最新（{count} 條）")
            return {"updated": False, "count": count, "message": f"已是最新（{count} 條）"}
    except Exception:
        info = get_vuln_source_info()
        return {"updated": False, "count": info.get("count", 0), "message": "檢查失敗，使用現有緩存"}


# ============ OSV 實時查詢 + 版本檢查 ============

def query_osv(package: str, version: str) -> List[Dict]:
    """實時查詢 OSV.dev 獲取該包+版本的漏洞"""
    result = _osv_query(package, version)
    if not result:
        return []

    findings = []
    for v in result.get("vulns", []):
        if v.get("withdrawn"):
            continue
        parsed = _parse_osv_vuln(v)
        findings.append(parsed)
    return findings


def check_version_against_vulns(version_str: str) -> Dict:
    """檢查版本是否命中漏洞（Layer 1+2 內置+遠程+本地緩存）"""
    parsed = _parse_simple_version(version_str)
    if parsed is None:
        return {"vulnerabilities": [], "clean": True}

    vulnerabilities = []
    all_cves = get_all_cves()

    for cve in all_cves:
        if cve.get("withdrawn"):
            continue
        if "affected_below" in cve and cve["affected_below"]:
            threshold = _parse_simple_version(cve["affected_below"])
            if threshold and parsed < threshold:
                vulnerabilities.append(cve)
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
