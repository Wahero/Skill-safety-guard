"""子命令實現：誤報處理、決策邏輯、輸出格式化（從 cli.py 拆分）

供 CLI 和 Web API 共用。
"""
from typing import Dict
import json


def handle_report_fp(rule_id: str) -> int:
    """處理誤報報告（F-016）"""
    issue_url = (
        f"https://github.com/Wahero/Skill-safety-guard/issues/new"
        f"?template=false_positive.md"
        f"&title=%5BFalse+Positive%5D+{rule_id}"
        f"&labels=false-positive"
    )
    print(f"\n[REPORT] 報告誤報：{rule_id}")
    print(f"\n請訪問以下鏈接提交誤報：\n  {issue_url}")
    print(f"\n請在 issue 中包含：")
    print(f"  1. 規則 ID: {rule_id}")
    print(f"  2. 觸發該規則的 SKILL.md 或代碼片段")
    print(f"  3. 為什麼這是誤報")
    print(f"  4. 預期的正確行為")
    print(f"\n提交後，維護者會：")
    print(f"  - 在 7 天內處理")
    print(f"  - 添加白名單條目到 src/skill_safety_guard/rules/whitelist.yaml")
    print(f"  - 或調整規則（你會在 PR 中看到討論）")
    print(f"\n本地臨時白名單（不等於社區認可）：")
    print(f"  編輯 src/skill_safety_guard/rules/whitelist.yaml，添加：")
    print(f"  ```yaml")
    print(f"  whitelisted_patterns:")
    print(f"    - rule_id: {rule_id}")
    print(f"      pattern: \"<your-specific-text>\"")
    print(f"      reason: \"<why-this-is-false-positive>\"")
    print(f"  ```")
    return 0


def scan_pi_only(args) -> Dict:
    """只掃描 Pi 全局"""
    from .pi_check import check_pi_version, check_auth_permissions

    pi_result = check_pi_version(use_osv=getattr(args, "osv", False))
    auth_result = check_auth_permissions()

    pi_combined = {
        **pi_result,
        "auth_check": auth_result,
    }

    return {"_pi_only": True, "pi_check": pi_combined}


def format_json_output(target: str, pi_check: Dict, skill_results: Dict, overall_grade: str, decision: dict = None) -> str:
    """JSON 格式輸出"""
    all_findings = []
    for r in skill_results.values():
        if hasattr(r, "findings"):
            for f in r.findings:
                all_findings.append({
                    "rule_id": f.rule_id,
                    "rule_name": f.rule_name,
                    "severity": f.severity,
                    "confidence": f.confidence,
                    "category": f.category,
                    "description": f.description,
                    "file_path": f.file_path,
                    "line_number": f.line_number,
                    "matched_text": f.matched_text,
                })

    output = {
        "target": target,
        "overall_grade": overall_grade,
        "pi_check": {
            "version": pi_check.get("version", ""),
            "pi_available": pi_check.get("pi_available", False),
            "vulnerabilities": pi_check.get("vulnerabilities", []),
            "auth_check": pi_check.get("auth_check", {}),
        },
        "findings": all_findings,
        "summary": {
            "total": len(all_findings),
            "critical": sum(1 for f in all_findings if f["severity"] == "critical"),
            "high": sum(1 for f in all_findings if f["severity"] == "high"),
            "medium": sum(1 for f in all_findings if f["severity"] == "medium"),
            "low": sum(1 for f in all_findings if f["severity"] == "low"),
        },
    }

    if decision:
        output["decision"] = decision

    return json.dumps(output, ensure_ascii=False, indent=2)


def make_install_decision(grade: str, findings: list) -> dict:
    """殺手場景決策邏輯（F-010）"""
    critical = sum(1 for f in findings if f.severity == "critical")
    high = sum(1 for f in findings if f.severity == "high")
    medium = sum(1 for f in findings if f.severity == "medium")

    if grade in ["A", "B"]:
        return {
            "verdict": "SAFE",
            "title": "安全",
            "description": "未發現重大安全問題，可以繼續評估其他因素（許可證、依賴、作者信譽等）",
        }
    elif grade == "C":
        return {
            "verdict": "CAUTION",
            "title": "警告",
            "description": f"發現 {medium} 個中風險問題，建議人工審查每個後再決定是否安裝",
        }
    elif grade in ["D", "E"]:
        return {
            "verdict": "CAUTION",
            "title": "警告",
            "description": f"發現 {high} 個高風險問題。不建議安裝，除非你能解釋每個問題",
        }
    else:  # F
        return {
            "verdict": "DANGER",
            "title": "危險",
            "description": f"發現 {critical} 個嚴重問題。強烈建議不要安裝此 Skill",
        }


def format_decision_block(target_name: str, decision: dict) -> str:
    """格式化殺手場景決策區塊"""
    verdict_map = {
        "SAFE": "[SAFE] 建議：可以安裝",
        "CAUTION": "[CAUTION] 建議：人工複查後決定",
        "DANGER": "[DANGER] 建議：不要安裝",
    }

    return f"""> **{verdict_map.get(decision['verdict'], decision['verdict'])}**
>
> **目標**: `{target_name}`
> **{decision['title']}**: {decision['description']}
>
> ---

"""