"""CLI 主入口（F-007~F-010 殺手場景 + V-01 驗證項 + F-003/F-004）"""
import argparse
import sys
import json
import time
from pathlib import Path
from typing import Dict, Optional

from .rules_loader import load_all_rules, load_whitelist
from .detectors import CredentialsDetector, ShellDetector, PathsDetector, UnicodeDetector, CriticalPathsDetector, PrivacyDetector
from .license import (
    can_scan, record_scan, activate_license, generate_license_key,
    load_license, print_tier_banner, FREE_SCANS_PER_WEEK, PRO_PRICE_MONTHLY_USD,
)
from .detectors.base import Finding
from .pi_check import check_pi_version, check_auth_permissions
from .parser import parse_skill_file, validate_skill_frontmatter
from .reporter import generate_report, calculate_risk_grade, generate_confidence_explanation
from .sarif import findings_to_sarif_string
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
    parser.add_argument(
        "--output",
        choices=["markdown", "json", "sarif"],
        default="markdown",
        help="輸出格式（sarif 用於 GitHub Code Scanning）",
    )
    parser.add_argument(
        "--output-file",
        metavar="PATH",
        default=None,
        help="把報告寫入指定檔案（預設：GitHub URL 掃描時自動寫入當前目錄 scan-report-<repo>.md）",
    )
    parser.add_argument("--report-fp", metavar="RULE_ID", help="報告誤報")
    parser.add_argument("--no-color", action="store_true", help="禁用彩色輸出")
    parser.add_argument("--no-pi", action="store_true", help="跳過 Pi Agent 全局檢查（加快掃描）")
    parser.add_argument(
        "--min-confidence",
        choices=["high", "medium", "low"],
        default="low",
        help="只顯示高於此置信度的結果",
    )
    parser.add_argument("--confidence-detail", action="store_true", help="顯示置信度分級詳細原因")
    parser.add_argument("--activate-pro", metavar="KEY", help="激活 Pro 許可證")
    parser.add_argument("--generate-pro-key", action="store_true", help="生成測試用 Pro 密鑰")
    parser.add_argument("--license-status", action="store_true", help="顯示許可證狀態")
    parser.add_argument("--audit-extensions", action="store_true", help="掃描已安裝擴展目錄")
    parser.add_argument("--pro", action="store_true", help="啟用 Pro 功能（LLM 輔助檢測）")
    parser.add_argument("--update-vulns", action="store_true", help="更新漏洞庫（每日漏洞情報）")
    parser.add_argument("--osv", action="store_true", help="啟用 OSV.dev 實時漏洞查詢")
    parser.add_argument("--vuln-frequency", choices=["daily", "weekly", "monthly", "off"], help="設置漏洞庫自動更新頻率")
    parser.add_argument("--vuln-status", action="store_true", help="查看漏洞庫狀態")
    parser.add_argument("--vuln-sources", action="store_true", help="查看所有漏洞源（含國內源）")
    parser.add_argument("--vuln-proxy", metavar="URL", help="設置 GitHub 加速代理（如 https://ghproxy.net/）")
    return parser.parse_args(argv)


def resolve_output_file(args, resolved) -> Optional[Path]:
    """解析報告輸出檔案路徑

    優先序：
    1. 用戶顯式指定 --output-file
    2. GitHub URL 掃描 → 自動生成 scan-report-<repo>.md 到當前工作目錄
    3. 其他情況 → None（只印 stdout，不寫檔）
    """
    if getattr(args, "output_file", None):
        return Path(args.output_file).resolve()
    if args.output == "markdown" and resolved and resolved.kind.startswith("github"):
        display = resolved.display_name  # e.g. github.com/user/repo
        repo = display.split("/")[-1] if display else "scan"
        return Path.cwd() / f"scan-report-{repo}.md"
    return None


def emit_output(text: str, output_file: Optional[Path]) -> None:
    """印出報告；若指定 output_file 則同時寫入該檔案"""
    print(text)
    if output_file:
        try:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(text, encoding="utf-8")
            print(f"\n📄 報告已存檔：{output_file}", file=sys.stderr)
        except OSError as e:
            print(f"\n[WARN] 報告寫檔失敗：{e}", file=sys.stderr)


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
        critical_det = CriticalPathsDetector(all_rules.get("critical_paths", []), whitelist)
        privacy_det = PrivacyDetector(all_rules.get("privacy", []), whitelist)
        installed_ext_det = CredentialsDetector(all_rules.get("installed_extensions", []), whitelist)  # reuse base
        prompt_inj_det = CredentialsDetector(all_rules.get("prompt_injection", []), whitelist)  # reuse base

        # 檢測目標是文件還是目錄
        if target.is_file():
            from .detectors.base import DetectionResult
            # 單文件掃描
            try:
                content = target.read_text(encoding="utf-8")
            except (UnicodeDecodeError, PermissionError):
                content = ""

            for det, cat in [(cred_det, "credentials"), (shell_det, "shell"), (path_det, "paths"),
                              (unicode_det, "unicode"), (critical_det, "critical_paths"),
                              (privacy_det, "privacy"),
                              (installed_ext_det, "installed_extensions"), (prompt_inj_det, "prompt_injection")]:
                det.category = cat
                result = DetectionResult(category=cat, scanned_files=1)
                findings = det.detect_file(target, content)
                for f in findings:
                    if not det._apply_whitelist(f):
                        f = det._apply_confidence_demotion(f)
                        result.findings.append(f)
                skill_results[cat] = result
        else:
            for det, cat in [(cred_det, "credentials"), (shell_det, "shell"), (path_det, "paths"),
                              (unicode_det, "unicode"), (critical_det, "critical_paths"),
                              (privacy_det, "privacy")]:
                det.category = cat
                result = det.detect_directory(target)
                skill_results[cat] = result

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


def main(argv=None):
    """CLI 主入口"""
    args = parse_args(argv)

    # 處理誤報報告
    if args.report_fp:
        return handle_report_fp(args.report_fp)

    # 許可證管理命令（F-033~F-036）
    if args.generate_pro_key:
        key = generate_license_key()
        print(f"\n[PRO KEY GENERATED] {key}\n")
        print(f"啟動：safety-check --activate-pro {key}\n")
        return 0

    if args.activate_pro:
        try:
            lic = activate_license(args.activate_pro)
            print(f"\n[PRO ACTIVATED] {lic.tier}")
            print(f"  Expires: {time.strftime('%Y-%m-%d', time.localtime(lic.expires_at))}\n")
            return 0
        except ValueError as e:
            print(f"[ERROR] {e}", file=sys.stderr)
            return 1

    if args.license_status:
        lic = load_license()
        can, info = can_scan()
        print(f"\nTier: {info['tier'].upper()}")
        if info["tier"] == "pro":
            print(f"Expires: {time.strftime('%Y-%m-%d', time.localtime(info['expires_at']))}")
        else:
            used = info['limit'] - info['remaining']
            print(f"Scans this week: {used}/{info['limit']}")
        print(f"Can scan now: {can}\n")
        return 0

    # 更新漏洞庫（每日漏洞情報）
    if args.update_vulns:
        from .vuln_feed import update_vulnerabilities, get_vuln_source_info
        print("\n[VULN UPDATE] 從權威源（OSV.dev）更新漏洞庫...")
        result = update_vulnerabilities(force=True)
        print(f"  狀態: {'✅ 已更新' if result.get('updated') else '⏭ 未更新'}")
        print(f"  原因: {result.get('reason', 'ok')}")
        if result.get('count'):
            print(f"  漏洞條目: {result['count']}")
        if result.get('frequency'):
            print(f"  更新頻率: {result['frequency']}")
        info = get_vuln_source_info()
        print(f"  當前來源: {info['source']}（更新於 {info['last_updated']}）")
        print(f"  當前規則: {info['count']} 條\n")
        return 0

    # 設置漏洞庫更新頻率
    if args.vuln_frequency:
        from .vuln_feed import set_frequency
        result = set_frequency(args.vuln_frequency)
        if result.get("ok"):
            print(f"\n[VULN FREQUENCY] 更新頻率已設置為: {result['frequency']}")
            print(f"  說明: {'每天' if result['frequency']=='daily' else '每週' if result['frequency']=='weekly' else '每月' if result['frequency']=='monthly' else '關閉'}自動更新漏洞庫\n")
        else:
            print(f"\n[ERROR] {result.get('error', '設置失敗')}\n")
        return 0

    # 設置 GitHub 加速代理（國內用戶用）
    if args.vuln_proxy:
        from .vuln_feed import set_github_proxy
        result = set_github_proxy(args.vuln_proxy)
        if result.get("ok"):
            print(f"\n[PROXY] 已設置加速代理: {result['proxies']}")
            print(f"  漏洞庫更新將通過代理訪問 GitHub\n")
        else:
            print(f"\n[ERROR] {result.get('error', '設置失敗')}\n")
        return 0

    # 查看所有漏洞源（含國內源）
    if args.vuln_sources:
        from .vuln_feed import DOMESTIC_SOURCES, GITHUB_PROXIES, get_config
        print("\n[VULN SOURCES] 漏洞源列表")
        print("\n  === 自動源 ===")
        print(f"  🌐 OSV.dev（主）: Google 官方，自動排除已撤銷 CVE")
        print(f"  📦 本項目漏洞庫: GitHub raw（GitHub Actions 每天更新）")
        config = get_config()
        custom_proxies = config.get("github_proxies", [])
        if custom_proxies:
            print(f"  🔀 自定義加速代理: {', '.join(custom_proxies)}")
        else:
            print(f"  🔀 內置加速代理: {', '.join(GITHUB_PROXIES)}")
        print(f"  ⚙️  可配置: 在 {config.get('_path', '~/.skill-safety-guard/config.json')} 添加 github_proxies")
        print("\n  === 國內源（需人工/註冊） ===")
        for key, src in DOMESTIC_SOURCES.items():
            print(f"  🏛 {src['name']}")
            print(f"     權威性: {src['authority']}")
            print(f"     訪問: {src['access']}")
            print(f"     URL: {src['url']}")
        print()
        return 0

    # 查看漏洞庫狀態
    if args.vuln_status:
        from .vuln_feed import (
            get_vuln_source_info, get_frequency, get_ttl, _read_update_meta,
            get_all_cves, load_vulnerabilities,
        )
        info = get_vuln_source_info()
        print("\n[VULN STATUS] 漏洞庫狀態")
        print(f"  📊 漏洞條目: {info['count']}")
        print(f"  📡 數據來源: {info['source']}")
        print(f"  🕐 數據庫更新日期: {info['last_updated']}")
        print(f"  🔄 自動更新頻率: {info['frequency']}（TTL: {get_ttl() // 3600} 小時）")

        # 本地緩存最後檢查時間
        meta = _read_update_meta()
        if meta:
            last_check = time.strftime('%Y-%m-%d %H:%M', time.localtime(meta.get('last_update', 0)))
            print(f"  ⏱ 本地最後檢查: {last_check}")
        else:
            print(f"  ⏱ 本地最後檢查: 從未（使用內置/緩存庫）")

        # 本地緩存狀態
        from .vuln_feed import LOCAL_VULNS_CACHE
        if LOCAL_VULNS_CACHE.exists():
            mtime = time.strftime('%Y-%m-%d %H:%M', time.localtime(LOCAL_VULNS_CACHE.stat().st_mtime))
            print(f"  💾 本地緩存文件: 存在（{mtime}）")
        else:
            print(f"  💾 本地緩存文件: 無（使用內置庫）")

        # 漏洞 ID 預覽
        all_cves = get_all_cves()
        if all_cves:
            ids = [c.get('cve_id', '?') for c in all_cves]
            print(f"  🎯 漏洞清單: {', '.join(ids)}")

        # 到期提示
        meta2 = _read_update_meta()
        if meta2 and time.time() - meta2.get('last_update', 0) > get_ttl():
            print()
            print("  ⚠️ 漏洞庫已過期，建議執行: safety-check --update-vulns")
        print()
        return 0

    # 解析掃描目標（F-007 殺手場景：支援 URL/粘貼）
    resolved = resolve_target(args.target)
    if resolved is None:
        print(f"[ERROR] 無法解析目標：{args.target}", file=sys.stderr)
        print(f"  請提供本地路徑、GitHub URL，或用 'paste' 從 stdin 讀取", file=sys.stderr)
        return 2

    target = resolved.path

    # 檢查使用限制
    can, info = can_scan()
    if not can:
        print(f"[FREE TIER LIMIT REACHED] 0/{info['limit']} scans remaining this week")
        print(f"  Resets: {time.strftime('%Y-%m-%d', time.localtime(info['resets_at']))}")
        print(f"  Upgrade to Pro: $4.99/month")
        print(f"  Generate key: safety-check --generate-pro-key")
        return 3

    # 打印 banner（僅人類可讀模式）
    if args.output == "markdown":
        print_tier_banner()
        print()

    # 解析報告輸出檔案（GitHub URL → 自動寫入當前目錄）
    output_file = resolve_output_file(args, resolved)

    try:
        return _run_scan(args, target, resolved, output_file)
    finally:
        cleanup_target(resolved)


def _run_scan(args, target: Path, resolved: ScanTarget, output_file: Optional[Path] = None) -> int:
    """執行掃描（F-025: --all 完整掃描）"""

    if args.pi:
        pi_data = scan_pi_only(args)
        if args.output == "json":
            print(format_json_output(str(target), pi_data["pi_check"], {}, "N/A"))
        else:
            emit_output(generate_report(str(target), pi_data["pi_check"], {}, "A"), output_file)
        return 0

    # 進度顯示（F-026）
    def progress(msg: str):
        if args.output == "markdown" and not args.no_color:
            print(f"  → {msg}")

    # 漏洞庫自動更新檢查（可配置頻率，後台更新不阻塞）
    try:
        from .vuln_feed import auto_update_if_due
        auto_update_if_due()
    except Exception:
        pass

    # 正常掃描
    progress("正在掃描 Skill 內容...")
    skill_results = scan_target(target, args)
    progress(f"完成 Skill 掃描（{sum(len(r.findings) for r in skill_results.values())} 個發現）")

    # --no-pi：跳過 Pi 全局檢查（性能優化 F-043）
    if args.no_pi:
        pi_check = {"pi_available": False, "version": "", "vulnerabilities": [],
                    "clean": True, "error": "跳過（--no-pi）", "auth_check": {}}
    else:
        progress("正在檢查 Pi Agent 全局...")
        pi_check = check_pi_version(use_osv=getattr(args, "osv", False))
        pi_check["auth_check"] = check_auth_permissions()
        progress("完成 Pi 全局檢查")

    # --all 模式：增加 MCP 依賴檢查（F-029~F-032 + F-039/F-040）
    mcp_result = None
    if args.all:
        progress("正在檢查 MCP 依賴...")
        from .mcp_check import check_mcp_directory, format_mcp_report
        from .rules_loader import load_rules_file

        mcp_rules = load_rules_file("mcp.yaml")
        mcp_injection_rules = load_rules_file("mcp_injection.yaml")
        mcp_result = check_mcp_directory(target, mcp_rules, mcp_injection_rules)
        progress(f"完成 MCP 檢查（{len(mcp_result['findings'])} 個發現，{len(mcp_result['tools'])} 個工具）")

    # Pro 模式：LLM 輔助提示詞注入檢測（F-037）
    llm_result = None
    if args.pro:
        # 檢查許可證
        lic = load_license()
        if not lic.is_pro():
            print("  [PRO] LLM 輔助檢測需要 Pro 許可證")
            print("  生成測試密鑰: safety-check --generate-pro-key")
        else:
            progress("正在執行 LLM 輔助提示詞注入檢測...")
            from .llm_check import llm_check_skill_file, format_llm_report

            # 掃描目標中的 SKILL.md
            skill_md = target / "SKILL.md" if target.is_dir() else target
            if skill_md and skill_md.exists():
                llm_result = llm_check_skill_file(skill_md)
                if llm_result.get("analyzed"):
                    progress(f"完成 LLM 檢測（{len(llm_result.get('findings', []))} 個發現）")
                elif not llm_result.get("llm_available"):
                    progress("LLM 不可用（未配置 DEEPSEEK_API_KEY）")

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
    # 誤報（fp_reason 非空）不計入風險評分
    real_findings = [f for f in all_findings if not getattr(f, "fp_reason", "")]
    overall_grade = calculate_risk_grade(real_findings)

    # 殺手場景決策（F-010）
    # 將 MCP findings 也計入風險評估（F-032）
    mcp_findings_for_grade = []
    if mcp_result:
        from .detectors.base import Finding as MCPFinding
        for f in mcp_result["findings"]:
            mcp_findings_for_grade.append(MCPFinding(
                rule_id=f["rule_id"], rule_name=f["rule_name"],
                severity=f["severity"], confidence=f["confidence"],
                category="mcp", description=f["description"],
                remediation=f["remediation"], file_path=f["file_path"],
                line_number=f["line_number"], matched_text=f["matched_text"],
            ))
    all_findings_for_decision = real_findings + mcp_findings_for_grade
    decision = make_install_decision(overall_grade, all_findings_for_decision)

    if args.output == "json":
        output = json.loads(format_json_output(str(target), pi_check, skill_results, overall_grade, decision))
        # MCP 結果併入 JSON（F-032）
        if mcp_result:
            output["mcp_check"] = mcp_result
        # LLM 結果併入 JSON（F-037）
        if llm_result:
            output["llm_check"] = llm_result
        emit_output(json.dumps(output, ensure_ascii=False, indent=2), output_file)
    elif args.output == "sarif":
        all_finding_dicts = []
        for r in skill_results.values():
            if hasattr(r, "findings"):
                for f in r.findings:
                    all_finding_dicts.append({
                        "rule_id": f.rule_id,
                        "rule_name": f.rule_name,
                        "severity": f.severity,
                        "confidence": f.confidence,
                        "category": f.category,
                        "description": f.description,
                        "remediation": f.remediation,
                        "file_path": f.file_path,
                        "line_number": f.line_number,
                        "matched_text": f.matched_text,
                    })
        # MCP findings 也併入 SARIF
        if mcp_result:
            for f in mcp_result["findings"]:
                all_finding_dicts.append(f)
        # LLM findings 也併入 SARIF
        if llm_result:
            for f in llm_result.get("findings", []):
                all_finding_dicts.append({
                    "rule_id": f"llm-{f.get('type', 'finding')}",
                    "rule_name": f.get("description", "LLM finding")[:60],
                    "severity": {"high": "critical", "medium": "high", "low": "medium"}.get(f.get("confidence"), "medium"),
                    "confidence": f.get("confidence", "medium"),
                    "category": "llm_injection",
                    "description": f.get("description", ""),
                    "remediation": f.get("remediation", ""),
                    "file_path": str(target),
                    "line_number": 1,
                    "matched_text": f.get("location", "")[:80],
                })
        emit_output(findings_to_sarif_string(all_finding_dicts, str(target)), output_file)
    else:
        report = generate_report(str(target), pi_check, skill_results, overall_grade)
        # MCP 報告併入 Markdown（F-032）
        if mcp_result:
            from .mcp_check import format_mcp_report
            report = report + "\n---\n\n## 第三層：MCP 依賴檢查\n\n" + format_mcp_report(mcp_result)
        # LLM 報告併入 Markdown（F-037）
        if llm_result:
            from .llm_check import format_llm_report
            report = report + "\n---\n\n## 第四層：LLM 輔助檢測（Pro）\n\n" + format_llm_report(llm_result)
        decision_block = format_decision_block(resolved.display_name, decision)
        report = decision_block + report
        if args.confidence_detail:
            report = report + "\n\n" + generate_confidence_explanation(all_findings)
        emit_output(report, output_file)

    # 記錄掃描使用
    record_scan()

    grade_to_exit = {"A": 0, "B": 0, "C": 0, "D": 1, "E": 1, "F": 2}
    return grade_to_exit.get(overall_grade, 0)