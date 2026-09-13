"""本地高危服務版本 CVE 檢查（V-04）

個人開發者常本地運行的 AI/自動化服務（langflow、n8n 等）若版本過舊，
可能存在無需登錄即可利用的高危漏洞（如 CVE-2025-3248 Langflow 未授權 RCE）。
本模組探測本機已安裝版本，比對漏洞庫（Layer 1+2）與 OSV 實時查詢（Layer 3）。

版本探測方式（按包生態）：
- pip：importlib.metadata（當前解釋器環境）→ `<bin> --version` 回退
- npm：`<bin> --version`（與 pi 檢查相同的 PATH 探測策略）

限制：dedicated venv 裡的 pip 包若不在 PATH 上則探測不到；docker 部署的服務不適用。
"""
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

from ..vuln_feed_config import TRACKED_PACKAGES, PI_PACKAGE_NAMES
from ..vuln_feed import check_version_against_vulns

# 只檢查非 Pi 的本地服務包（Pi 自己走 check_pi_version）
LOCAL_SERVICE_PACKAGES = [
    pkg for pkg in TRACKED_PACKAGES
    if pkg["name"] not in set(PI_PACKAGE_NAMES)
]


def _version_cache_path() -> Path:
    return Path.home() / ".skill-safety-guard" / "local_services_version.json"


def _read_version_cache() -> Optional[Dict]:
    try:
        cache_path = _version_cache_path()
        if not cache_path.exists():
            return None
        data = json.loads(cache_path.read_text(encoding="utf-8"))
        if time.time() - data.get("cached_at", 0) > 3600:
            return None
        return data.get("versions", {})
    except Exception:
        return None


def _write_version_cache(versions: Dict) -> None:
    try:
        cache_path = _version_cache_path()
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(
            json.dumps({"versions": versions, "cached_at": time.time()}),
            encoding="utf-8",
        )
    except Exception:
        pass


def _clear_version_cache() -> None:
    try:
        _version_cache_path().unlink(missing_ok=True)
    except Exception:
        pass


def _parse_version_from_output(output: str) -> str:
    """從命令輸出中提取版本號"""
    match = re.search(r"(\d+\.\d+(?:\.\d+)?(?:[a-z0-9.]*)?)", output or "")
    return match.group(1) if match else ""


def _probe_bin_version(bin_name: str) -> Dict:
    """通過 `<bin> --version` 探測本機命令行版本"""
    use_shell = sys.platform.startswith("win")
    try:
        result = subprocess.run(
            [bin_name, "--version"],
            capture_output=True,
            text=True,
            timeout=8,
            shell=use_shell,
        )
        output = (result.stdout or "") + (result.stderr or "")
        version_str = _parse_version_from_output(output)
        if result.returncode == 0 and version_str:
            return {"available": True, "version": version_str, "error": ""}
        return {"available": False, "version": "", "error": "命令不可用或無法解析版本"}
    except FileNotFoundError:
        return {"available": False, "version": "", "error": f"{bin_name} 命令未找到"}
    except subprocess.TimeoutExpired:
        return {"available": False, "version": "", "error": f"{bin_name} --version 超時"}
    except Exception as e:
        return {"available": False, "version": "", "error": str(e)}


def _probe_pip_versions(names: List[str]) -> Dict:
    """一次 subprocess 探測當前解釋器環境下的多個 pip 包版本"""
    code = (
        "import importlib.metadata as _m, json\n"
        f"names = {names!r}\n"
        "out = {}\n"
        "for _n in names:\n"
        "    try:\n"
        "        out[_n] = _m.version(_n)\n"
        "    except Exception:\n"
        "        pass\n"
        "print(json.dumps(out))\n"
    )
    try:
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0:
            return json.loads(result.stdout.strip() or "{}")
    except Exception:
        pass
    return {}


def get_local_service_versions(use_cache: bool = True) -> Dict[str, Dict]:
    """探測所有本地服務包的已安裝版本

    返回 {name: {"available": bool, "version": str, "ecosystem": str, "error": str}}
    """
    if use_cache:
        cached = _read_version_cache()
        if cached is not None:
            return cached

    versions = {}
    pip_names = [p["name"] for p in LOCAL_SERVICE_PACKAGES if p.get("type") == "pip"]
    pip_found = _probe_pip_versions(pip_names) if pip_names else {}

    for pkg in LOCAL_SERVICE_PACKAGES:
        name, eco = pkg["name"], pkg.get("type", "npm")
        info = {"available": False, "version": "", "ecosystem": eco, "error": ""}

        if eco == "pip" and name in pip_found:
            info.update(available=True, version=pip_found[name])
        elif pkg.get("bin"):
            probe = _probe_bin_version(pkg["bin"])
            info.update(available=probe["available"], version=probe["version"],
                        error="" if probe["available"] else probe["error"])
        if not info["available"]:
            info["error"] = "未安裝或不在 PATH"
        versions[name] = info

    _write_version_cache(versions)
    return versions


def check_local_services(use_osv: bool = False) -> List[Dict]:
    """執行本地高危服務版本 CVE 檢查

    返回每個服務的檢查結果列表：
    {name, ecosystem, available, version, vulnerabilities, clean, error, osv_checked}
    """
    versions = get_local_service_versions()
    results = []

    for pkg in LOCAL_SERVICE_PACKAGES:
        name = pkg["name"]
        eco = pkg.get("type", "npm")
        info = versions.get(name, {})
        result = {
            "name": name,
            "ecosystem": eco,
            "available": info.get("available", False),
            "version": info.get("version", ""),
            "vulnerabilities": [],
            "clean": True,
            "error": info.get("error", ""),
            "osv_checked": False,
        }

        if result["available"]:
            vuln_result = check_version_against_vulns(result["version"], packages=[name])
            result["vulnerabilities"] = vuln_result["vulnerabilities"]

            if use_osv:
                from ..vuln_feed import query_osv
                osv_findings = query_osv(name, result["version"], ecosystem=eco)
                existing_ids = {v.get("cve_id") for v in result["vulnerabilities"]}
                for f in osv_findings:
                    if f["cve_id"] not in existing_ids:
                        result["vulnerabilities"].append(f)
                        existing_ids.add(f["cve_id"])
                result["osv_checked"] = True

            result["clean"] = len(result["vulnerabilities"]) == 0

        results.append(result)

    return results
