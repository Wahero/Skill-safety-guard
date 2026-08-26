"""CLI 主入口（命令路由 + 參數解析）

P1-1 重構後職責：
  - parse_args(): 命令行參數定義
  - main(): 命令路由 + 子命令派發
  - _run_scan(): 掃描編排（進度、MCP、LLM、輸出格式化）

掃描邏輯 → scan_orchestrator.py
子命令實現 → commands.py
"""
import argparse
import json
import sys
import time
from pathlib import Path
from typing import Optional

from . import __version__
from .license import (
    can_scan, record_scan, activate_license, generate_license_key,
    load_license, print_tier_banner,
)
from .pi_check import check_pi_version, check_auth_permissions
from .reporter import generate_report, calculate_risk_grade, generate_confidence_explanation
from .sarif import findings_to_sarif_string
from .scan_target_resolver import resolve_target, cleanup_target, ScanTarget

# P1-1 拆分：從新模組導入
from .scan_orchestrator import scan_target, resolve_output_file, emit_output
from .commands import (
    handle_report_fp, scan_pi_only, format_json_output,
    make_install_decision, format_decision_block,
)


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
    parser.add_argument(
        "--version",
        action="version",
        version=f"skill-safety-guard v{__version__}",
        help="顯示版本號",
    )
    return parser.parse_args(argv)


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
        can, info = can_scan()
        print(f"\nTier: {info['tier'].upper()}")
        if info["tier"] == "pro":
            exp = info.get("expires_at")
            print(f"Expires: {time.strftime('%Y-%m-%d', time.localtime(exp)) if exp else 'never'}")
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
            get_all_cves, LOCAL_VULNS_CACHE,
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

    # Skill 首次調用（無目標、無子命令）→ 顯示 CLI 面板 + 自動啟動 Web 界面
    # v3.8.0：優化首次體驗，無需 --web 參數
    scan_flags = {
        "pi": args.pi, "all": args.all, "audit_extensions": args.audit_extensions,
        "pro": args.pro, "no_pi": args.no_pi, "confidence_detail": args.confidence_detail,
    }
    is_first_invocation = (
        args.target == "."  # 預設目標 = 當前目錄
        and not any(scan_flags.values())
        and args.output == "markdown"  # 預設輸出格式
        and args.min_confidence == "low"  # 預設過濾閾值
    )
    if is_first_invocation:
        _cli_welcome_banner(host="127.0.0.1", port=8765)
        _launch_web_server_silent(host="127.0.0.1", port=8765)
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

    # 每日漏洞庫定義檢查（同日只查一次，有新版本則同步更新）
    try:
        from .vuln_feed import check_and_update_vulns
        if args.output == "markdown" and not args.no_color:
            check_and_update_vulns(progress_cb=lambda msg: print(f"  → {msg}"))
        else:
            check_and_update_vulns()
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


def _probe_web_server(host: str = "127.0.0.1", port: int = 8765, timeout: float = 0.5) -> bool:
    """探測 Web 服務器是否已在 host:port 運行

    返回 True = 已在運行；False = 未運行。
    """
    import socket
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (OSError, socket.timeout):
        return False


def _launch_web_server_silent(host: str = "127.0.0.1", port: int = 8765) -> int:
    """後台啟動 Web 服務器（不阻塞、打開瀏覽器）

    與 CLI --web 不同：這個版本不需要 --web 參數，在 Skill 首次調用時自動觸發。
    返回 0 表示服務器已在運行或成功啟動；1 表示啟動失敗。
    """
    web_server = Path(__file__).resolve().parent.parent.parent / "web" / "server.py"
    if not web_server.exists():
        print(f"[ERROR] 找不到 Web 服務器入口: {web_server}", file=sys.stderr)
        return 1

    url = f"http://{host}:{port}"

    # 探測是否已運行
    if _probe_web_server(host, port):
        print(f"   Web 界面已在運行: {url}/")
        return 0

    # 自動開啟瀏覽器
    import webbrowser
    try:
        webbrowser.open(url)
    except Exception:
        pass

    print(f"   啟動 Web 界面: {url}/")
    sys.argv = ["web/server.py", "--host", host, "--port", str(port)]
    try:
        import runpy
        runpy.run_path(str(web_server), run_name="__main__")
        return 0
    except KeyboardInterrupt:
        return 0


def _cli_welcome_banner(host: str = "127.0.0.1", port: int = 8765) -> None:
    """Skill 首次調用時的 CLI 歡迎畫面"""
    url = f"http://{host}:{port}"
    print()
    print("=" * 64)
    print(f"🛡️  skill-safety-guard v{__version__} - Skill 安全掃描工具")
    print("=" * 64)
    print()
    print(f"📡 Web 界面地址: {url}/")
    print(f"   （如瀏覽器未自動打開，請手動訪問上述網址）")
    print()
    print("📋 CLI 用法提示：")
    print(f"   python -m skill_safety_guard <路徑|URL>     掃描本地路徑或 GitHub URL")
    print(f"   python -m skill_safety_guard --pi           只檢查 Pi 全局")
    print(f"   python -m skill_safety_guard --output json  JSON 輸出")
    print(f"   python -m skill_safety_guard --help         完整幫助")
    print()
    print("=" * 64)
    print()