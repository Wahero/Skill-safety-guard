"""CLI 主入口（V-01 驗證項 + F-003/F-004）"""
import argparse
import sys
import json
from pathlib import Path
from typing import Dict

from .rules_loader import load_all_rules, load_whitelist
from .detectors import CredentialsDetector, ShellDetector, PathsDetector
from .detectors.base import Finding
from .pi_check import check_pi_version, check_auth_permissions
from .parser import parse_skill_file, validate_skill_frontmatter
from .reporter import generate_report, calculate_risk_grade


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
  python -m skill_safety_guard --pi             只檢查 Pi 全局
  python -m skill_safety_guard --all            完整掃描（Pi + Skill + 依賴）
  python -m skill_safety_guard --output json    JSON 輸出
  python -m skill_safety_guard --report-fp <id> 報告誤報
        """,
    )
    parser.add_argument(
        "target",
        nargs="?",
        default=".",
        help="掃描目標路徑（默認：當前目錄）",
    )
    parser.add_argument(
        "--pi",
        action="store_true",
        help="只掃描 Pi Agent 全局（版本 + auth.json）",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="完整掃描（Pi + Skill + 依賴）",
    )
    parser.add_argument(
        "--output",
        choices=["markdown", "json"],
        default="markdown",
        help="輸出格式（默認：markdown）",
    )
    parser.add_argument(
        "--report-fp",
        metavar="RULE_ID",
        help="報告誤報（會打開 GitHub issue 模板）",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="禁用彩色輸出",
    )
    return parser.parse_args(argv)


def handle_report_fp(rule_id: str) -> int:
    """處理誤報報告（F-016）

    打開 GitHub issue URL，預填標題和內容
    """
    issue_url = (
        f"https://github.com/Wahero/Skill-safety-guard/issues/new"
        f"?template=false_positive.md"
        f"&title=%5BFalse+Positive%5D+{rule_id}"
        f"&labels=false-positive"
    )
    print(f"\n📝 報告誤報：{rule_id}")
    print(f"\n請訪問以下鏈接提交誤報：\n  {issue_url}")
    print(f"\n請在 issue 中包含：")
    print(f"  1. 規則 ID: {rule_id}")
    print(f"  2. 觸發該規則的 SKILL.md 或代碼片段")
    print(f"  3. 為什麼這是誤報")
    print(f"  4. 預期的正確行為")
    return 0


def scan_target(target: Path, args) -> Dict:
    """執行掃描"""
    whitelist = load_whitelist()
    all_rules = load_all_rules()

    # Skill 內容檢測
    skill_results: Dict = {}
    if not args.pi:
        if not target.exists():
            print(f"❌ 目標路徑不存在：{target}", file=sys.stderr)
            sys.exit(2)

        # 三大檢測器
        cred_det = CredentialsDetector(all_rules.get("credentials", []), whitelist)
        shell_det = ShellDetector(all_rules.get("shell", []), whitelist)
        path_det = PathsDetector(all_rules.get("paths", []), whitelist)

        for det in [cred_det, shell_det, path_det]:
            result = det.detect_directory(target)
            skill_results[det.category] = result

        # SKILL.md frontmatter 驗證
        skill_md = target / "SKILL.md" if target.is_dir() else None
        if skill_md and skill_md.exists():
            fm = parse_skill_file(skill_md)
            if fm:
                validation = validate_skill_frontmatter(fm)
                if not validation["valid"] or validation["warnings"]:
                    # 將 SKILL.md 問題包裝成 finding
                    from .detectors.base import Finding

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


def format_json_output(target: str, pi_check: Dict, skill_results: Dict, overall_grade: str) -> str:
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

    return json.dumps({
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
    }, ensure_ascii=False, indent=2)


def main(argv=None):
    """CLI 主入口"""
    args = parse_args(argv)

    # 處理誤報報告
    if args.report_fp:
        return handle_report_fp(args.report_fp)

    target = Path(args.target).resolve()

    # 判斷模式
    if args.pi:
        pi_data = scan_pi_only(args)
        # 只顯示 Pi 結果
        if args.output == "json":
            print(format_json_output(str(target), pi_data["pi_check"], {}, "N/A"))
        else:
            # Markdown
            print(generate_report(str(target), pi_data["pi_check"], {}, "A"))
        return 0

    # 正常掃描
    skill_results = scan_target(target, args)
    pi_check = check_pi_version()
    pi_check["auth_check"] = check_auth_permissions()

    # 計算綜合評分
    all_findings = []
    for r in skill_results.values():
        if hasattr(r, "findings"):
            all_findings.extend(r.findings)
    overall_grade = calculate_risk_grade(all_findings)

    if args.output == "json":
        print(format_json_output(str(target), pi_check, skill_results, overall_grade))
    else:
        print(generate_report(str(target), pi_check, skill_results, overall_grade))

    # 退出碼：基於綜合評分
    grade_to_exit = {"A": 0, "B": 0, "C": 0, "D": 1, "E": 1, "F": 2}
    return grade_to_exit.get(overall_grade, 0)