"""漏洞庫配置管理（P3-2 從 vuln_feed.py 拆分）

負責：常量定義、配置讀寫、頻率/TTL 管理。
被 vuln_feed.py 和 vuln_feed_sources.py 依賴，不依賴兩者（無循環導入）。
"""
import json
from pathlib import Path
from typing import Dict

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
GITHUB_PROXIES = [
    "https://ghproxy.net/",
    "https://mirror.ghproxy.com/",
    "https://gh-proxy.com/",
]

# 國內/替代漏洞源（可配置）
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

# AVID GitHub API
AVID_GITHUB_API = "https://api.github.com/repos/avidml/avid-db"


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
    """設置 GitHub 加速代理（國內用戶用）"""
    if not proxy_url.startswith("http"):
        return {"ok": False, "error": f"無效代理 URL: {proxy_url}（需以 http:// 或 https:// 開頭）"}

    config = get_config()
    proxies = config.get("github_proxies", [])
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
