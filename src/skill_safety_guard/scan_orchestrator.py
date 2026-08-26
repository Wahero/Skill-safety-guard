"""掃描編排器：掃描目標執行、輸出管理（從 cli.py 拆分）

供 CLI 和 Web API 共用。
"""
from pathlib import Path
from typing import Dict, Optional
import sys

from .rules_loader import load_all_rules, load_whitelist
from .detectors import (
    CredentialsDetector, ShellDetector, PathsDetector, UnicodeDetector,
    CriticalPathsDetector, PrivacyDetector,
    InstalledExtensionsDetector, PromptInjectionDetector,
    NativeFileOpsDetector,
    OWASPDetector,
)
from .detectors.base import Finding
from .parser import parse_skill_file, validate_skill_frontmatter


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
        installed_ext_det = InstalledExtensionsDetector(all_rules.get("installed_extensions", []), whitelist)
        prompt_inj_det = PromptInjectionDetector(all_rules.get("prompt_injection", []), whitelist)
        native_fs_det = NativeFileOpsDetector(all_rules.get("native_file_ops", []), whitelist)
        owasp_det = OWASPDetector(all_rules.get("owasp", []), whitelist)

        # 檢測目標是文件還是目錄
        if target.is_file():
            from .detectors.base import DetectionResult
            # 單文件掃描
            try:
                content = target.read_text(encoding="utf-8")
            except (UnicodeDecodeError, PermissionError):
                content = ""

            for det in [cred_det, shell_det, path_det, unicode_det, critical_det,
                        privacy_det, installed_ext_det, prompt_inj_det, native_fs_det, owasp_det]:
                result = DetectionResult(category=det.category, scanned_files=1)
                findings = det.detect_file(target, content)
                for f in findings:
                    if not det._apply_whitelist(f):
                        f = det._apply_confidence_demotion(f)
                        result.findings.append(f)
                skill_results[det.category] = result
        else:
            # installed_extensions 不在目錄掃描中執行：該規則集設計為審計已安裝
            # 擴展代碼（JS/TS），而非掃描一般 Skill 源碼；ext-curl-wget 等規則
            # 對文檔性 curl/wget 提及過度敏感。擴展審計走 --audit-extensions。
            for det in [cred_det, shell_det, path_det, unicode_det, critical_det,
                        privacy_det, prompt_inj_det, native_fs_det, owasp_det]:
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