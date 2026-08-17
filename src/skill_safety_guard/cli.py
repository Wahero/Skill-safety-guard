"""CLI 主入口（F-007~F-010 殺手場景 + V-01 驗證項 + F-003/F-004）"""
import argparse
import sys
import json
from pathlib import Path
from typing import Dict

from .rules_loader import load_all_rules, load_whitelist
from .detectors import CredentialsDetector, ShellDetector, PathsDetector, UnicodeDetector
from .detectors.base import Finding
from .pi_check import check_pi_version, check_auth_permissions
from .parser import parse_skill_file, validate_skill_frontmatter
from .reporter import generate_report, calculate_risk_grade, generate_confidence_explanation
from .scan_target_resolver import resolve_target, cleanup_target, ScanTarget


def parse_args(argv=None):
    """解析命令行參數"""
    parser = argparse.ArgumentParser(
        prog="skill-safety-guard",
        description="個人開發者 Skill/MCP 安全掃描工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
範例：
  python -m skill_safety_guard                  掃描當前目錄
  python -m skill_safety_guard ./my-skill       掃描指定路徑
  python -m skill_safety_guard <github-url>     掃描 GitHub repo
  python -m skill_safety_guard paste            從 stdin 讀取內容
  python -m skill_safety_guard --pi             只檢查 Pi 全局
  python -m skill_safety_guard --output json    JSON 輸出
  python -m skill_safety_guard --report-fp <id> 報告誤報
        """,
    )
    parser.add_argument(
        "target",
        nargs="?",
        default=".",
        help="掃描目標：本地路徑 / GitHub URL / 'paste' (從 stdin)",
    )
    parser.add_argument("--pi", action="store_true", help="只掃描 Pi Agent 全局")
    parser.add_argument("--all", action="store_true", help="完整掃描（Pi + Skill + 依賴）")
    parser.add_argument("--output", choices=["markdown", "json"], default="markdown", help="輸出格式")
    parser.add_argument("--report-fp", metavar="RULE_ID", help="報告誤報")
    parser.add_argument("--no-color", action="store_true", help="禁用彩色輸出")
    parser.add_argument(
        "--min-confidence",
        choices=["high", "medium", "low"],
        default="low",
        help="只顯示高於此置信度的結果",
    )
    parser.add_argument("--confidence-detail", action="store_true", help="顯示置信度分級詳細原因")
    return parser.parse_args(argv)


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
    print(f"  - 添加白名單條目到 rules/whitelist.yaml")
    print(f"  - 或調整規則（你會在 PR 中看到討論）")
    print(f"\n本地臨時白名單（不等於社區認可）：")
    print(f"  編輯 rules/whitelist.yaml，添加：")
    print(f"  ```yaml")
    print(f"  whitelisted_patterns:")
    print(f"    - rule_id: {rule_id}")
    print(f"      pattern: \"<your-specific-text>\"")
    print(f"      reason: \"<why-this-is-false-positive>\"")
    print(f"  ```")
    return 0


def scan_target(target: Path, args) -> Dict:
    """執行掃描"""
    whitelist = load_whitelist()
    all_rules = load_all_rules()

    skill_results: Dict = {}
    if not args.pi:
        if not target.exists():
            print(f"[ERROR] 目標路徑不存在：{target}", file=sys.stderr)
            sys.exit(2)

        cred_det = CredentialsDetector(all_rules.get("credentials", []), whitelist)
        shell_det = ShellDetector(all_rules.get("shell", []), whitelist)
        path_det = PathsDetector(all_rules.get("paths", []), whitelist)
        unicode_det = UnicodeDetector(all_rules.get("unicode", []), whitelist)

        # 檢測目標是文件還是目錄
        if target.is_file():
            from .detectors.base import DetectionResult
            # 單文件掃描
            try:
                content = target.read_text(encoding="utf-8")
            except (UnicodeDecodeError, PermissionError):
                content = ""

            for det in [cred_det, shell_det, path_det, unicode_det]:
                result = DetectionResult(category=det.category, scanned_files=1)
                findings = det.detect_file(target, content)
                for f in findings:
                    if not det._apply_whitelist(f):
                        f = det._apply_confidence_demotion(f)
                        result.findings.append(f)
                skill_results[det.category] = result
        else:
            for det in [cred_det, shell_det, path_det, unicode_det]:
                result = det.detect_directory(target)
                skill_results[det.category] = result

        # SKILL.md frontmatter 驗證
        skill_md = target / "SKILL.md" if target.is_dir() else None
        if skill_md and skill_md.exists():
            fm = parse_skill_file(skill_md)
            if fm:
                validation = validate_skill_frontmatter(fm)
                if not validation["valid"] or validation["warnings"]:
                    fm_findings = []
                    for missing in validation["missing"]:
                        fm_findings.append(Finding(
                            rule_id="skill-frontmatter-missing",
                            rule_name=f"SKILL.md 缺少必需字段：{missing}",
                            severity="medium",
                            confidence="high",
                            category="skill_meta",
                            description=f"SKILL.md frontmatter 缺少 `{missing}` 字段",
                            remediation=f"在 frontmatter 中添加 `{missing}: <value>`",
                            file_path=str(skill_md),
                            line_number=1,
                            matched_text=f"---\n[缺少 {missing}]",
                            context_line=f"---\nname: ...\n[{missing} missing]\n---",
                        ))
                    for warn in validation["warnings"]:
                        fm_findings.append(Finding(
                            rule_id="skill-frontmatter-warning",
                            rule_name="SKILL.md 警告",
                            severity="low",
                            confidence="medium",
                            category="skill_meta",
                            description=warn,
                            remediation="審查並修正",
                            file_path=str(skill_md),
                            line_number=1,
                            matched_text=warn[:50],
                            context_line="",
                        ))
                    skill_results["skill_meta"] = type('R', (), {
                        "category": "skill_meta",
                        "findings": fm_findings,
                        "scanned_files": 1,
                    })()

    return skill_results


def scan_pi_only(args) -> Dict:
    """只掃描 Pi 全局"""
    pi_result = check_pi_version()
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


def main(argv=None):
    """CLI 主入口"""
    args = parse_args(argv)

    # 處理誤報報告
    if args.report_fp:
        return handle_report_fp(args.report_fp)

    # 解析掃描目標（F-007 殺手場景：支援 URL/粘貼）
    resolved = resolve_target(args.target)
    if resolved is None:
        print(f"[ERROR] 無法解析目標：{args.target}", file=sys.stderr)
        print(f"  請提供本地路徑、GitHub URL，或用 'paste' 從 stdin 讀取", file=sys.stderr)
        return 2

    target = resolved.path

    try:
        return _run_scan(args, target, resolved)
    finally:
        cleanup_target(resolved)


def _run_scan(args, target: Path, resolved: ScanTarget) -> int:
    """執行掃描"""

    if args.pi:
        pi_data = scan_pi_only(args)
        if args.output == "json":
            print(format_json_output(str(target), pi_data["pi_check"], {}, "N/A"))
        else:
            print(generate_report(str(target), pi_data["pi_check"], {}, "A"))
        return 0

    # 正常掃描
    skill_results = scan_target(target, args)
    pi_check = check_pi_version()
    pi_check["auth_check"] = check_auth_permissions()

    # 應用置信度過濾（F-015）
    if args.min_confidence != "low":
        confidence_order = {"high": 3, "medium": 2, "low": 1}
        threshold = confidence_order[args.min_confidence]
        for result in skill_results.values():
            if hasattr(result, "findings"):
                result.findings = [
                    f for f in result.findings
                    if confidence_order.get(f.confidence, 1) >= threshold
                ]

    # 計算綜合評分
    all_findings = []
    for r in skill_results.values():
        if hasattr(r, "findings"):
            all_findings.extend(r.findings)
    overall_grade = calculate_risk_grade(all_findings)

    # 殺手場景決策（F-010）
    decision = make_install_decision(overall_grade, all_findings)

    if args.output == "json":
        print(format_json_output(str(target), pi_check, skill_results, overall_grade, decision))
    else:
        report = generate_report(str(target), pi_check, skill_results, overall_grade)
        decision_block = format_decision_block(resolved.display_name, decision)
        report = decision_block + report
        if args.confidence_detail:
            report = report + "\n\n" + generate_confidence_explanation(all_findings)
        print(report)

    grade_to_exit = {"A": 0, "B": 0, "C": 0, "D": 1, "E": 1, "F": 2}
    return grade_to_exit.get(overall_grade, 0)