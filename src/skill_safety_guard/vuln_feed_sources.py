"""漏洞源拉取（OSV.dev + AVID + 遠程 feed）（P3-2 從 vuln_feed.py 拆分）

負責：HTTP 工具、OSV 查詢/解析、AVID 拉取、遠程 feed 拉取。
依賴 vuln_feed_config.py，不依賴 vuln_feed.py（無循環導入）。
"""
import json
import math
import urllib.request
from typing import Dict, List, Optional

from .vuln_feed_config import (
    OSV_QUERY_URL, OSV_BATCH_URL, TRACKED_PACKAGES,
    REMOTE_FEED_URL, GITHUB_PROXIES, AVID_GITHUB_API,
    get_config,
)


# ============ HTTP 工具 ============

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
    """生成訪問 GitHub raw 的 URL 列表（直連 + 加速代理）"""
    config = get_config()
    custom_proxies = config.get("github_proxies", [])
    proxies = list(custom_proxies) + GITHUB_PROXIES
    urls = [base_url]
    for proxy in proxies:
        proxy = proxy.rstrip("/") + "/"
        urls.append(proxy + base_url)
    return urls


# ============ OSV.dev 查詢 + 解析 ============

def _osv_query(package: str, version: Optional[str] = None, ecosystem: str = "npm") -> Optional[Dict]:
    """查詢 OSV.dev（權威源，自動排除 withdrawn）"""
    payload = {"package": {"name": package, "ecosystem": ecosystem}}
    if version:
        payload["version"] = version

    result = _http_post_json(OSV_QUERY_URL, payload, timeout=15)
    if result is not None:
        return result

    # OSV 失敗 → 不再回退到 NVD 鏡像（P3-3：未實作）
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


def _version_key(version_str: str):
    """版本號排序鍵（簡單 X.Y.Z 數字比較，非數字後綴忽略）"""
    import re

    match = re.match(r"(\d+)(?:\.(\d+))?(?:\.(\d+))?", version_str or "")
    if not match:
        return (0, 0, 0)
    return (
        int(match.group(1)),
        int(match.group(2) or 0),
        int(match.group(3) or 0),
    )


def _extract_fixed_intervals(v: Dict):
    """從 OSV affected ranges 提取受影響版本區間 [(lo, hi), ...]

    支持 SEMVER 與 ECOSYSTEM（PyPI 等）範圍；hi=None 表示無修復版本（開放區間）。
    同一 range 內多組 introduced/fixed 對應多分支修復（如 n8n 的 1.x/2.x 分支）。
    """
    intervals = []
    fixed_versions = []
    for affected in v.get("affected", []):
        for rng in affected.get("ranges", []):
            if rng.get("type") not in ("SEMVER", "ECOSYSTEM"):
                continue
            lo = "0"
            for event in rng.get("events", []):
                if "introduced" in event:
                    lo = event["introduced"]
                elif "fixed" in event:
                    fixed_versions.append(event["fixed"])
                    intervals.append((lo, event["fixed"]))
                    lo = None  # 該分支之後不再受影響
    return intervals, fixed_versions


def _parse_osv_vuln(v: Dict, package: Optional[str] = None) -> Dict:
    """將 OSV 漏洞轉為內部格式

    package: 漏洞所屬包名（OSV 查詢時的目標包）；不傳時保持舊行為（pi-coding-agent）
    """
    severity = _osv_severity(v)

    intervals, fixed_versions = _extract_fixed_intervals(v)
    if fixed_versions:
        affected_below = max(fixed_versions, key=_version_key)
        affected_versions = sorted({f"<{f}" for f in fixed_versions},
                                   key=lambda s: _version_key(s[1:]))
    else:
        affected_below = None
        affected_versions = []

    aliases = v.get("aliases", [])
    cve_id = v.get("id", "OSV-unknown")
    for alias in aliases:
        if alias.startswith("CVE-"):
            cve_id = alias
            break

    return {
        "cve_id": cve_id,
        "osv_id": v.get("id", ""),
        "package": package or "pi-coding-agent",
        "affected_below": affected_below,
        "affected_ranges": intervals if intervals else None,
        "affected_versions": affected_versions if affected_versions else None,
        "severity": severity,
        "confidence": "high",
        "description": (v.get("summary") or v.get("details") or "")[:200],
        "remediation": f"升級至 {affected_below}+" if affected_below else "升級至修復版本",
        "source": "OSV",
        "published": v.get("published", ""),
        "withdrawn": v.get("withdrawn"),
    }


def _cvss31_base_score(vector: str) -> Optional[float]:
    """計算 CVSS 3.1 基礎分（OSV 的 severity 多為向量字符串，無法直接取數字）"""
    metrics = dict(tok.split(":", 1) for tok in vector.split("/") if ":" in tok)
    try:
        av = {"N": 0.85, "L": 0.62, "A": 0.55, "P": 0.2}[metrics.get("AV")]
        ac = {"L": 0.77, "H": 0.44}[metrics.get("AC")]
        ui = {"N": 0.85, "R": 0.62}[metrics.get("UI")]
        c = {"H": 0.56, "L": 0.22, "N": 0.0}[metrics.get("C")]
        i = {"H": 0.56, "L": 0.22, "N": 0.0}[metrics.get("I")]
        a = {"H": 0.56, "L": 0.22, "N": 0.0}[metrics.get("A")]
        scope_changed = metrics.get("S") == "C"
        if scope_changed:
            pr = {"N": 0.85, "L": 0.68, "H": 0.5}[metrics.get("PR")]
        else:
            pr = {"N": 0.85, "L": 0.62, "H": 0.27}[metrics.get("PR")]
    except (KeyError, ValueError):
        return None

    iss = 1 - (1 - c) * (1 - i) * (1 - a)
    if scope_changed:
        impact = 7.52 * (iss - 0.029) - 3.25 * (iss - 0.02) ** 15
    else:
        impact = 6.42 * iss
    exploitability = 8.22 * av * ac * pr * ui
    if impact <= 0:
        return 0.0
    if scope_changed:
        score = min(1.08 * (impact + exploitability), 10.0)
    else:
        score = min(impact + exploitability, 10.0)
    return min(math.ceil(score * 10) / 10, 10.0)


def _osv_severity(vuln: Dict) -> str:
    """OSV 嚴重度映射（CVSS 評分）

    支持：純數字評分、CVSS 3.x 向量字符串（精確計算基礎分）、
    CVSS 4.x 向量（粗略啟發式：AV:N+PR:N+高影響 → critical / AV:N → high）。
    無法判斷時回退 medium（保守）。
    """
    for ref in vuln.get("severity", []):
        score = ref.get("score", "")
        if score.startswith("CVSS:4"):
            # CVSS v4 精確計算複雜，用向量特徵做保守啟發式
            if "AV:N" in score and "PR:N" in score and ("VI:H" in score or "VA:H" in score or "VC:H" in score):
                return "critical"
            if "AV:N" in score:
                return "high"
            continue
        if score.startswith("CVSS"):
            computed = _cvss31_base_score(score)
            if computed is not None:
                score_num = computed
            else:
                continue
        else:
            try:
                score_num = float(score.split(":")[-1])
            except (ValueError, IndexError):
                continue
        if score_num >= 9.0:
            return "critical"
        if score_num >= 7.0:
            return "high"
        if score_num >= 4.0:
            return "medium"
        return "low"
    return "medium"


# ============ 遠程 feed + 權威源拉取 ============

def fetch_remote_feed() -> Optional[Dict]:
    """從 GitHub 拉取最新漏洞庫（Layer 2，含國內加速代理回退）"""
    for url in _get_proxy_urls(REMOTE_FEED_URL):
        data = _http_get_json(url, timeout=10)
        if data is not None and isinstance(data, dict) and "vulnerabilities" in data:
            return data
    return None


def fetch_authoritative_vulns() -> Optional[List[Dict]]:
    """從權威源（OSV.dev）拉取追蹤包的漏洞（Layer 3）

    Pi 生態全量保留；其餘本地服務包（langflow/n8n 等）條目量大，
    只保留 high/critical 且有明確修復版本的條目，避免漏洞庫膨脹。
    """
    from .vuln_feed_config import PI_PACKAGE_NAMES

    pi_names = set(PI_PACKAGE_NAMES)
    findings = []
    for pkg in TRACKED_PACKAGES:
        ecosystem = pkg.get("ecosystem") or pkg.get("type", "npm")
        result = _osv_query(pkg["name"], ecosystem=ecosystem)
        if not result:
            continue
        is_pi = pkg["name"] in pi_names
        for v in result.get("vulns", []):
            if v.get("withdrawn"):
                continue
            parsed = _parse_osv_vuln(v, package=pkg["name"])
            if not is_pi and not (
                parsed["severity"] in ("high", "critical") and parsed["affected_below"]
            ):
                continue
            if not any(f["cve_id"] == parsed["cve_id"] for f in findings):
                findings.append(parsed)
    return findings or None


# ============ AVID（AI 漏洞庫，國際開源） ============

def fetch_avid_vulns(limit_per_year: int = 50) -> Optional[List[Dict]]:
    """從 AVID 開源 AI 漏洞庫拉取漏洞（通過 GitHub API）"""
    findings = []

    try:
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

        desc = data.get("description", {})
        if isinstance(desc, dict):
            desc_text = desc.get("value", "")
        elif isinstance(desc, list):
            desc_text = "; ".join(d.get("value", "") for d in desc if isinstance(d, dict))
        else:
            desc_text = str(desc)

        problemtype = data.get("problemtype", {})
        if isinstance(problemtype, dict):
            ptype = problemtype.get("type") or problemtype.get("classof") or "ai-vulnerability"
        else:
            ptype = "ai-vulnerability"

        affects = data.get("affects", {})
        affected_name = ""
        if isinstance(affects, dict):
            developer = affects.get("developer", {})
            if isinstance(developer, dict):
                affected_name = developer.get("name", "")

        return {
            "cve_id": vuln_id,
            "package": affected_name or "ai-system",
            "severity": "medium",
            "confidence": "medium",
            "description": f"[AVID] {ptype}: {desc_text[:180]}",
            "remediation": f"查看 AVID 詳情: https://avidml.org/database/{vuln_id}",
            "source": "AVID",
            "published": data.get("published_date", ""),
        }
    except Exception:
        return None
