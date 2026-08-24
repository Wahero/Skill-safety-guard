"""Web 後端共用 API：結構化掃描（不列印、不寫檔、不耗免費額度）

供 web/server.py 使用，也供未來其他整合方複用。
複用 cli.scan_target / make_install_decision / reporter.calculate_risk_grade，
不重寫檢測引擎（「Web 是 CLI 的薄 UI 層」原則）。
"""
from __future__ import annotations

import time
from pathlib import Path
from types import SimpleNamespace
from typing import Callable, Dict, List, Optional

from .rules_loader import load_all_rules, load_whitelist
from .detectors import CredentialsDetector, ShellDetector, PathsDetector, UnicodeDetector, CriticalPathsDetector, PrivacyDetector
from .reporter import calculate_risk_grade
from .scan_target_resolver import resolve_target, cleanup_target
from .pi_check import check_pi_version, check_auth_permissions
from .cli import make_install_decision, scan_target

# 進度回調型別
ProgressCb = Optional[Callable[[str], None]]


def _finding_to_dict(f) -> Dict:
    """把 Finding 物件轉成可序列化的 dict"""
    return {
        "rule_id": getattr(f, "rule_id", ""),
        "rule_name": getattr(f, "rule_name", ""),
        "severity": getattr(f, "severity", "low"),
        "confidence": getattr(f, "confidence", "low"),
        "category": getattr(f, "category", ""),
        "description": getattr(f, "description", ""),
        "remediation": getattr(f, "remediation", ""),
        "file_path": getattr(f, "file_path", ""),
        "line_number": getattr(f, "line_number", 0),
        "matched_text": (getattr(f, "matched_text", "") or "")[:200],
        "fp_reason": getattr(f, "fp_reason", ""),
    }


def _count_severity(findings: List[Dict]) -> Dict[str, int]:
    out = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for f in findings:
        sev = f.get("severity", "low")
        if sev in out:
            out[sev] += 1
    return out


def _get_vuln_db_info() -> Dict:
    """獲取漏洞庫狀態（用於報告）"""
    try:
        from .vuln_feed import get_vuln_source_info
        info = get_vuln_source_info()
        return {
            "source": info.get("source", ""),
            "last_updated": info.get("last_updated", ""),
            "count": info.get("count", 0),
        }
    except Exception:
        return {"source": "unavailable", "last_updated": "", "count": 0}


def run_scan(
    target_str: str,
    *,
    include_pi: bool = False,
    include_mcp: bool = False,
    progress: ProgressCb = None,
) -> Dict:
    """執行一次結構化掃描，返回可 JSON 序列化的結果 dict。

    Args:
        target_str: 掃描目標（本地路徑 / GitHub URL）
        include_pi: 是否檢查 Pi Agent 全局（版本 CVE + auth.json ACL）
        include_mcp: 是否檢查 MCP 依賴（--all 等價）
        progress: 進度回調（接收階段描述字串）

    Returns:
        {
            "target": str, "display_name": str,
            "grade": "A"|..., "verdict": "SAFE"|"CAUTION"|"DANGER",
            "decision": {...}, "findings": [...], "summary": {...},
            "pi_check": {...}, "scanned_files": int, "elapsed_ms": int,
            "error": str (only on failure),
        }
    """
    t0 = time.time()
    if progress:
        progress("解析掃描目標…")

    # 每日漏洞庫定義檢查（同日只查一次，在掃描前執行）
    try:
        from .vuln_feed import check_and_update_vulns
        check_and_update_vulns(progress_cb=progress)
    except Exception:
        pass

    resolved = resolve_target(target_str)
    if resolved is None:
        return {"target": target_str, "error": f"無法解析目標：{target_str}"}

    target = resolved.path
    try:
        if progress:
            progress("掃描 Skill 內容…")

        args = SimpleNamespace(pi=False, output="json")
        skill_results = scan_target(target, args)

        if progress:
            progress("完成 Skill 掃描")

        # Pi 全局檢查
        pi_check: Dict
        if include_pi:
            if progress:
                progress("檢查 Pi Agent 全局…")
            pi_check = check_pi_version()
            pi_check["auth_check"] = check_auth_permissions()
            if progress:
                progress("完成 Pi 全局檢查")
        else:
            pi_check = {"pi_available": False, "version": "", "vulnerabilities": [], "auth_check": {}}

        # MCP 依賴檢查
        mcp_result: Optional[Dict] = None
        if include_mcp:
            if progress:
                progress("檢查 MCP 依賴…")
            try:
                from .mcp_check import check_mcp_directory
                from .rules_loader import load_rules_file
                mcp_rules = load_rules_file("mcp.yaml")
                mcp_injection_rules = load_rules_file("mcp_injection.yaml")
                mcp_result = check_mcp_directory(target, mcp_rules, mcp_injection_rules)
            except Exception:
                mcp_result = None

        # 彙整 findings
        all_findings: List = []
        for r in skill_results.values():
            if hasattr(r, "findings"):
                all_findings.extend(r.findings)

        real_findings = [f for f in all_findings if not getattr(f, "fp_reason", "")]
        grade = calculate_risk_grade(real_findings)

        # MCP findings 併入決策評分
        mcp_findings_for_grade: List = []
        if mcp_result:
            from .detectors.base import Finding
            for f in mcp_result.get("findings", []):
                mcp_findings_for_grade.append(Finding(
                    rule_id=f["rule_id"], rule_name=f["rule_name"],
                    severity=f["severity"], confidence=f["confidence"],
                    category="mcp", description=f["description"],
                    remediation=f["remediation"], file_path=f["file_path"],
                    line_number=f["line_number"], matched_text=f["matched_text"],
                ))
        decision = make_install_decision(grade, real_findings + mcp_findings_for_grade)

        findings_json = [_finding_to_dict(f) for f in all_findings]
        if mcp_result:
            findings_json.extend(mcp_result.get("findings", []))

        summary = _count_severity(findings_json)
        summary["total"] = len(findings_json)
        summary["fp_excluded"] = len(all_findings) - len(real_findings)

        scanned_files = sum(
            getattr(r, "scanned_files", 0) for r in skill_results.values() if hasattr(r, "scanned_files")
        )

        if progress:
            progress("完成掃描")

        return {
            "target": target_str,
            "display_name": resolved.display_name,
            "grade": grade,
            "verdict": decision.get("verdict", "SAFE"),
            "decision": decision,
            "findings": findings_json,
            "summary": summary,
            "pi_check": {
                "version": pi_check.get("version", ""),
                "pi_available": pi_check.get("pi_available", False),
                "vulnerabilities": pi_check.get("vulnerabilities", []),
                "auth_check": pi_check.get("auth_check", {}),
            },
            "scanned_files": scanned_files,
            "elapsed_ms": int((time.time() - t0) * 1000),
            "vuln_db": _get_vuln_db_info(),
        }
    finally:
        cleanup_target(resolved)
