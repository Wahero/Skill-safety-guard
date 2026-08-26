"""漏洞情報管理（每日/每週自動更新，多源回退）

權威漏洞源（多源回退鏈）：
1. OSV.dev（主）：Google 維護，自動排除已撤銷 CVE，免費無 key
2. 國內源（中國用戶備選）：
   - CNNVD（中國信息安全測評中心）官方，但需註冊登錄 + 反爬，標記為需人工
   - CNVD（國家互聯網應急中心）官方，需註冊/證書，標記為需人工
   - GitHub NVD 鏡像（fkie-cad/nvd-json-data-feeds 等）可通過 ghproxy 等加速代理訪問
   - 自定義鏡像（用戶可在配置中指定）

更新機制（可配置頻率）：
- 默認每週更新（update_frequency: weekly）
- 可改 daily / weekly / monthly / off
- 每次掃描檢查 TTL，過期自動後台更新
- --update-vulns 手動強制更新

撤銷清理：
- OSV.dev 查詢自動排除已撤銷/拒絕的 CVE（官方行為）
- 本地更新時以權威源為準，被撤銷的漏洞自動從庫中消失
- 無需用戶手動核對

三層架構：
- Layer 1: 內置基線（vulnerabilities.json，隨倉庫發布）
- Layer 2: 遠程漏洞源（GitHub raw / 鏡像 拉取 + 自動更新）
- Layer 3: OSV.dev / 國內源 / GitHub Advisory 實時查詢
"""
import json
import os
import threading
import time
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional

# 內置漏洞庫路徑（隨倉庫更新）
BUILTIN_VULNS = Path(__file__).resolve().parent / "rules" / "vulnerabilities.json"

# 遠程漏洞源（GitHub raw，可更新）
REMOTE_FEED_URL = "https://raw.githubusercontent.com/Wahero/Skill-safety-guard/main/src/skill_safety_guard/rules/vulnerabilities.json"

# 本地緩存
CACHE_DIR = Path.home() / ".skill-safety-guard"
LOCAL_VULNS_CACHE = CACHE_DIR / "vulnerabilities_cache.json"
UPDATE_META = CACHE_DIR / "vuln_update_meta.json"
CONFIG_FILE = CACHE_DIR / "config.json"
DAILY_CHECK_MARKER = CACHE_DIR / "vuln_daily_check.json"

# OSV.dev API（權威源）
OSV_QUERY_URL = "https://api.osv.dev/v1/query"
OSV_BATCH_URL = "https://api.osv.dev/v1/querybatch"

# 追蹤的 Pi Agent 相關包
TRACKED_PACKAGES = [
    {"name": "pi", "type": "npm"},
    {"name": "@earendil-works/pi-coding-agent", "type": "npm"},
    {"name": "@earendil-works/pi-agent", "type": "npm"},
]

# 頻率 → TTL 秒數
FREQUENCY_TTL = {
    "daily": 24 * 3600,
    "weekly": 7 * 24 * 3600,
    "monthly": 30 * 24 * 3600,
    "off": float("inf"),
}
DEFAULT_FREQUENCY = "weekly"

# 國內加速代理（GitHub 被牆時的替代訪問方式）
# 用戶可在配置中自定義，例如：https://ghproxy.com/ 或 https://mirror.ghproxy.com/
GITHUB_PROXIES = [
    "https://ghproxy.net/",
    "https://mirror.ghproxy.com/",
    "https://gh-proxy.com/",
]

# 國內/替代漏洞源（可配置）
# CNNVD/CNVD 需註冊登錄，無法自動拉取；這裡作為「需人工」標記
DOMESTIC_SOURCES = {
    "cnnvd": {
        "name": "CNNVD 中國國家信息安全漏洞庫",
        "authority": "中國信息安全測評中心（國家級）",
        "url": "https://www.cnnvd.org.cn",
        "access": "需註冊登錄 + 反爬，建議人工查詢",
        "auto_usable": False,
    },
    "cnvd": {
        "name": "CNVD 國家信息安全漏洞共享平台",
        "authority": "國家互聯網應急中心（CNCERT）",
        "url": "https://www.cnvd.org.cn",
        "access": "需註冊/證書申請，建議人工查詢",
        "auto_usable": False,
    },
    "caivd": {
        "name": "CAIVD 中國人工智能漏洞庫（AIVD）",
        "authority": "工信部主導、信通院（CAICT）建設（國家級）",
        "url": "https://ai.nvdb.org.cn",
        "access": "免註冊訪問，但數據前端渲染，無公開 JSON API（建議人工查詢）",
        "auto_usable": False,
    },
    "avid": {
        "name": "AVID AI 漏洞庫（國際開源）",
        "authority": "開源社區（avidml.org，GitHub 可訪問）",
        "url": "https://avidml.org",
        "access": "結構化 JSON（AVID-YYYY-VNNN），可通過 GitHub API 自動拉取",
        "auto_usable": True,
    },
    "nvd_github_mirror": {
        "name": "NVD JSON 數據饋送鏡像（GitHub）",
        "authority": "社區維護（fkie-cad）",
        "url": "https://github.com/fkie-cad/nvd-json-data-feeds",
        "access": "鏡像存在但 CPE 匹配太複雜，暫未實作自動查詢",
        "auto_usable": False,
    },
}


# ============ 配置 ============

def get_config() -> Dict:
    """讀取配置"""
    try:
        if CONFIG_FILE.exists():
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {"update_frequency": DEFAULT_FREQUENCY}


def set_frequency(frequency: str) -> Dict:
    """設置更新頻率（daily/weekly/monthly/off）"""
    if frequency not in FREQUENCY_TTL:
        return {"ok": False, "error": f"無效頻率: {frequency}（可選: daily/weekly/monthly/off）"}

    config = get_config()
    config["update_frequency"] = frequency
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"ok": True, "frequency": frequency}


def set_github_proxy(proxy_url: str) -> Dict:
    """設置 GitHub 加速代理（國內用戶用）

    存儲到配置，更新漏洞庫時優先使用該代理
    """
    if not proxy_url.startswith("http"):
        return {"ok": False, "error": f"無效代理 URL: {proxy_url}（需以 http:// 或 https:// 開頭）"}

    config = get_config()
    proxies = config.get("github_proxies", [])
    # 去重 + 加到最前（優先使用）
    proxies = [p for p in proxies if p != proxy_url]
    proxies.insert(0, proxy_url)
    config["github_proxies"] = proxies
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"ok": True, "proxies": proxies}


def get_ttl() -> int:
    """獲取當前頻率的 TTL"""
    config = get_config()
    freq = config.get("update_frequency", DEFAULT_FREQUENCY)
    return FREQUENCY_TTL.get(freq, FREQUENCY_TTL[DEFAULT_FREQUENCY])


def get_frequency() -> str:
    config = get_config()
    return config.get("update_frequency", DEFAULT_FREQUENCY)


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
        # 兼容：OSV 更新寫 _source，遠程源寫 _source_repo
        "source": data.get("_source") or data.get("_source_repo", "unknown"),
        "last_updated": data.get("_last_updated", "unknown"),
        "count": len(data.get("vulnerabilities", [])),
        "schema": data.get("_schema_version", "unknown"),
        "frequency": get_frequency(),
    }


# ============ 權威源拉取（OSV.dev + GitHub Advisory） ============

def _osv_query(package: str, version: Optional[str] = None, ecosystem: str = "npm") -> Optional[Dict]:
    """查詢 OSV.dev（權威源，自動排除 withdrawn）

    注意：OSV.dev 的 query 必須包含 ecosystem 字段，否則返回 400 invalid query。

    返回：(data, source_name)
    """
    # 帶 ecosystem 的包查詢（OSV 要求）
    payload = {"package": {"name": package, "ecosystem": ecosystem}}
    if version:
        payload["version"] = version

    result = _http_post_json(OSV_QUERY_URL, payload, timeout=15)
    if result is not None:
        return result

    # OSV 失敗 → 不再回退到 NVD 鏡像（P3-3：未實作，始終返回 None）
    return None


def _osv_batch_query(packages: List[Dict]) -> Optional[Dict]:
    """OSV batch 查詢多個包（更高效）"""
    payload = {"queries": [{"package": {"name": p["name"]}} for p in packages]}
    try:
        req = urllib.request.Request(
            OSV_BATCH_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "User-Agent": "skill-safety-guard"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


def _parse_osv_vuln(v: Dict) -> Dict:
    """將 OSV 漏洞轉為內部格式"""
    # 嚴重度
    severity = _osv_severity(v)

    # 影響版本
    affected_versions = []
    affected_below = None
    for affected in v.get("affected", []):
        for rng in affected.get("ranges", []):
            if rng.get("type") == "SEMVER":
                for event in rng.get("events", []):
                    if "introduced" in event and event["introduced"] == "0":
                        pass
                    if "fixed" in event:
                        affected_below = event["fixed"]
                        affected_versions.append(f"<{event['fixed']}")

    # 優先取 CVE ID
    aliases = v.get("aliases", [])
    cve_id = v.get("id", "OSV-unknown")
    for alias in aliases:
        if alias.startswith("CVE-"):
            cve_id = alias
            break

    return {
        "cve_id": cve_id,
        "osv_id": v.get("id", ""),
        "package": "pi-coding-agent",
        "affected_below": affected_below,
        "affected_versions": affected_versions if affected_versions else None,
        "severity": severity,
        "confidence": "high",
        "description": (v.get("summary") or v.get("details") or "")[:200],
        "remediation": f"升級至 {affected_below}+" if affected_below else "升級至修復版本",
        "source": "OSV",
        "published": v.get("published", ""),
        "withdrawn": v.get("withdrawn"),  # OSV 查詢通常已排除 withdrawn
    }


def _osv_severity(vuln: Dict) -> str:
    """OSV 嚴重度映射（CVSS 評分）"""
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


# ============ 遠程更新 ============

def _http_get_json(url: str, timeout: int = 15) -> Optional[Dict]:
    """GET JSON，帶 UA 和超時"""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 skill-safety-guard"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


def _http_post_json(url: str, payload: Dict, timeout: int = 20) -> Optional[Dict]:
    """POST JSON，帶 UA 和超時"""
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 skill-safety-guard"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


def _get_proxy_urls(base_url: str) -> List[str]:
    """生成訪問 GitHub raw 的 URL 列表（直連 + 加速代理）

    依序嘗試：直連 → 各代理
    """
    config = get_config()
    custom_proxies = config.get("github_proxies", [])
    proxies = list(custom_proxies) + GITHUB_PROXIES
    urls = [base_url]
    for proxy in proxies:
        # proxy 可能是完整 URL 或只是前綴
        proxy = proxy.rstrip("/") + "/"
        urls.append(proxy + base_url)
    return urls


def fetch_remote_feed() -> Optional[Dict]:
    """從 GitHub 拉取最新漏洞庫（Layer 2，含國內加速代理回退）"""
    for url in _get_proxy_urls(REMOTE_FEED_URL):
        data = _http_get_json(url, timeout=10)
        if data is not None and isinstance(data, dict) and "vulnerabilities" in data:
            return data
    return None


def fetch_authoritative_vulns() -> Optional[List[Dict]]:
    """從權威源（OSV.dev）拉取 Pi 相關漏洞（Layer 3）

    返回：最新漏洞列表（自動排除已撤銷 CVE）
    """
    findings = []
    for pkg in TRACKED_PACKAGES:
        result = _osv_query(pkg["name"], ecosystem=pkg.get("type", "npm"))
        if not result:
            continue
        for v in result.get("vulns", []):
            # OSV 已排除 withdrawn，這裡雙重檢查
            if v.get("withdrawn"):
                continue
            parsed = _parse_osv_vuln(v)
            if parsed["cve_id"] != "OSV-unknown" or True:
                # 去重
                if not any(f["cve_id"] == parsed["cve_id"] for f in findings):
                    findings.append(parsed)
    return findings or None


# ============ AVID（AI 漏洞庫，國際開源） ============

AVID_GITHUB_API = "https://api.github.com/repos/avidml/avid-db"


def fetch_avid_vulns(limit_per_year: int = 50) -> Optional[List[Dict]]:
    """從 AVID 開源 AI 漏洞庫拉取漏洞（通過 GitHub API）

    AVID 格式：AVID-YYYY-VNNN.json，含 metadata/problemtype/description
    可用於 OSV 不可用時的 AI 漏洞補充來源。

    注意：AVID 是 AI 系統漏洞（非僅 Pi Agent），過濾保留 AI 相關。
    """
    findings = []

    try:
        # 獲取年份目錄
        req = urllib.request.Request(
            f"{AVID_GITHUB_API}/contents/vulnerabilities",
            headers={"User-Agent": "Mozilla/5.0 skill-safety-guard"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            years = json.loads(resp.read().decode())
    except Exception:
        return None

    for year_item in years:
        year = year_item.get("name", "")
        if not year.isdigit():
            continue
        try:
            req = urllib.request.Request(
                f"{AVID_GITHUB_API}/contents/vulnerabilities/{year}",
                headers={"User-Agent": "Mozilla/5.0 skill-safety-guard"},
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                vuln_files = json.loads(resp.read().decode())
        except Exception:
            continue

        count = 0
        for vf in vuln_files:
            if count >= limit_per_year:
                break
            name = vf.get("name", "")
            if not name.endswith(".json"):
                continue
            try:
                req = urllib.request.Request(
                    f"{AVID_GITHUB_API}/contents/vulnerabilities/{year}/{name}",
                    headers={"User-Agent": "Mozilla/5.0 skill-safety-guard", "Accept": "application/vnd.github.v3.raw"},
                )
                with urllib.request.urlopen(req, timeout=15) as resp:
                    raw = json.loads(resp.read().decode())
            except Exception:
                continue

            count += 1
            parsed = _parse_avid_vuln(raw, name)
            if parsed:
                findings.append(parsed)

    return findings or None


def _parse_avid_vuln(data: Dict, filename: str) -> Optional[Dict]:
    """解析 AVID 漏洞 JSON 為內部格式"""
    try:
        metadata = data.get("metadata", {})
        vuln_id = metadata.get("vuln_id") or filename.replace(".json", "")

        # 描述
        desc = data.get("description", {})
        if isinstance(desc, dict):
            desc_text = desc.get("value", "")
        elif isinstance(desc, list):
            desc_text = "; ".join(d.get("value", "") for d in desc if isinstance(d, dict))
        else:
            desc_text = str(desc)

        # 問題類型
        problemtype = data.get("problemtype", {})
        if isinstance(problemtype, dict):
            ptype = problemtype.get("type") or problemtype.get("classof") or "ai-vulnerability"
        else:
            ptype = "ai-vulnerability"

        # 影響的產品
        affects = data.get("affects", {})
        affected_name = ""
        if isinstance(affects, dict):
            developer = affects.get("developer", {})
            if isinstance(developer, dict):
                affected_name = developer.get("name", "")

        return {
            "cve_id": vuln_id,  # AVID-YYYY-VNNN
            "package": affected_name or "ai-system",
            "severity": "medium",  # AVID 無標準嚴重度評分
            "confidence": "medium",
            "description": f"[AVID] {ptype}: {desc_text[:180]}",
            "remediation": "查看 AVID 詳情: https://avidml.org/database/{vuln_id}",
            "source": "AVID",
            "published": data.get("published_date", ""),
        }
    except Exception:
        return None


def update_vulnerabilities(force: bool = False, authoritative: bool = True) -> Dict:
    """更新漏洞庫

    策略：
    1. 先嘗試拉取遠程源（GitHub raw，Layer 2）
    2. 再嘗試權威源（OSV.dev，Layer 3）——合併/覆蓋
    3. 全失敗則返回未更新（保留現有庫）

    返回更新結果
    """
    # 檢查 TTL（非強制時）
    if not force:
        meta = _read_update_meta()
        ttl = get_ttl()
        if meta and time.time() - meta.get("last_update", 0) < ttl:
            return {
                "updated": False,
                "reason": f"在更新周期內（{get_frequency()}），使用緩存",
                "next_check": meta.get("last_update", 0) + ttl,
            }

    # 1. 遠程源（Layer 2）
    remote_data = fetch_remote_feed()

    # 2. 權威源（Layer 3，可選）
    osv_findings = None
    avid_findings = None
    if authoritative:
        osv_findings = fetch_authoritative_vulns()
        # OSV 失敗時回退到 AVID（國際開源 AI 漏洞庫）
        if osv_findings is None:
            avid_findings = fetch_avid_vulns(limit_per_year=30)

    # 決定使用哪個數據
    if osv_findings is not None:
        # 權威源優先：以 OSV 結果重建漏洞庫（自動處理撤銷）
        merged_vulns = osv_findings
        # 如果遠程源也有，合併（保留遠程中 OSV 沒有的手動補充）
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
        # AVID 回退：以 AVID 結果重建（OSV 不可用時）
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

    # 保存到本地緩存
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    _atomic_write_json(data, LOCAL_VULNS_CACHE)

    # 更新 meta
    _write_update_meta()

    # 撤銷清理：寫入後讀取確認無 withdrawn
    active_count = len([v for v in data.get("vulnerabilities", []) if not v.get("withdrawn")])

    return {
        "updated": True,
        "count": active_count,
        "source": data.get("_source", "remote"),
        "last_updated": data.get("_last_updated", "now"),
        "frequency": get_frequency(),
    }


# ============ 後台自動更新 ============

def auto_update_if_due() -> Dict:
    """掃描時調用：檢查是否到期，到期則後台更新（不阻塞）"""
    config = get_config()
    if config.get("update_frequency") == "off":
        return {"updated": False, "reason": "更新已關閉（off）"}

    meta = _read_update_meta()
    ttl = get_ttl()
    if meta and time.time() - meta.get("last_update", 0) < ttl:
        return {"updated": False, "reason": "在更新周期內"}

    # 後台線程更新（不阻塞掃描）
    def _bg_update():
        try:
            update_vulnerabilities(force=True)
        except Exception:
            pass

    thread = threading.Thread(target=_bg_update, daemon=True)
    thread.start()
    return {"updated": "background", "reason": f"觸發後台更新（{get_frequency()}）"}


def _atomic_write_json(data, path: Path) -> None:
    """原子寫入 JSON 檔案（P3-4）

    先寫 .tmp 臨時檔，再 rename 替換。進程中斷時不會留下半寫的 JSON。
    """
    tmp = path.with_suffix(".json.tmp")
    try:
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path)  # 原子替換（Windows 上 os.replace 等價）
    except Exception:
        try:
            tmp.unlink(missing_ok=True)
        except Exception:
            pass
        raise


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
    """檢查今天是否已做過漏洞庫每日檢查（同日不重複）"""
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
    """標記今日已檢查"""
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        DAILY_CHECK_MARKER.write_text(
            json.dumps({"date": time.strftime("%Y-%m-%d")}), encoding="utf-8"
        )
    except Exception:
        pass


def check_and_update_vulns(progress_cb=None) -> Dict:
    """每日檢查漏洞庫定義：同日只查一次，有新版本則更新

    Args:
        progress_cb: 進度回調 (msg: str)
    Returns:
        {"updated": bool, "count": int, "message": str}
    """
    if not daily_check_needed():
        info = get_vuln_source_info()
        return {"updated": False, "count": info.get("count", 0), "message": "今日已檢查，跳過"}

    mark_daily_check_done()

    if progress_cb:
        progress_cb("檢查漏洞庫定義…")

    # 檢查是否已有更新
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


# ============ OSV 實時查詢（單次） ============

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


# ============ 組合檢查 ============

def check_version_against_vulns(version_str: str) -> Dict:
    """檢查版本是否命中漏洞（Layer 1+2 內置+遠程+本地緩存）"""
    parsed = _parse_simple_version(version_str)
    if parsed is None:
        return {"vulnerabilities": [], "clean": True}

    vulnerabilities = []
    all_cves = get_all_cves()

    for cve in all_cves:
        # 跳過已撤銷
        if cve.get("withdrawn"):
            continue
        # affected_below 形式
        if "affected_below" in cve and cve["affected_below"]:
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