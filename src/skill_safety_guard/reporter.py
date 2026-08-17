"""Markdown 風險報告生成器（F-018）"""
from typing import Dict, List
from .detectors.base import Finding, DetectionResult


SEVERITY_EMOJI = {
    "critical": "🔴",
    "high": "🟠",
    "medium": "🟡",
    "low": "🟢",
    "ok": "✅",
}

CONFIDENCE_EMOJI = {
    "high": "🔴",
    "medium": "🟡",
    "low": "🟢",
}


def generate_confidence_explanation(findings: List[Finding]) -> str:
    """生成置信度解釋（F-015 增強）

    解釋為什麼某些被分為高/中/低置信度，幫助用戶理解
    """
    if not findings:
        return ""

    high = [f for f in findings if f.confidence == "high"]
    medium = [f for f in findings if f.confidence == "medium"]
    low = [f for f in findings if f.confidence == "low"]

    lines = [
        "---",
        "",
        "## 置信度分級詳解",
        "",
        f"**總計**: 高 {len(high)} | 中 {len(medium)} | 低 {len(low)}",
        "",
        "### 分級標準",
        "",
        "| 級別 | 含义 | 建議行為 |",
        "|------|------|---------|",
        "| 🔴 高置信度 | 明確危險模式，推累為真實威脅 | 必須處理 |",
        "| 🟡 中置信度 | 有可疑特徵但可能误報 | 人工複查 |",
        "| 🟢 低置信度 | 複雜上下文才會觸發 | 可能是 false positive |",
        "",
    ]

    if low:
        lines.append("### 低置信度提示")
        lines.append("")
        lines.append("以下規則被分為低置信度，可能需要人工確認：")
        lines.append("")
        for f in low[:5]:
            lines.append(f"- `{f.rule_id}` ({f.rule_name}): {f.file_path}:{f.line_number}")
        if len(low) > 5:
            lines.append(f"- ... 還有 {len(low) - 5} 個")
        lines.append("")

    lines.extend([
        "### 調整置信度",
        "",
        "如果認為某些規則誤報過多：",
        "",
        "1. 在 `rules/whitelist.yaml` 中添加白名單條目（本地生效）",
        "2. 運行 `safety-check --report-fp <rule-id>` 報告誤報（社區生效）",
        "3. 使用 `--min-confidence high` 只看高置信度問題",
        "",
    ])

    return "\n".join(lines)


def calculate_risk_grade(findings: List[Finding]) -> str:
    """根據 findings 計算綜合風險等級 A-F"""
    if not findings:
        return "A"

    critical = sum(1 for f in findings if f.severity == "critical")
    high = sum(1 for f in findings if f.severity == "high")
    medium = sum(1 for f in findings if f.severity == "medium")
    low = sum(1 for f in findings if f.severity == "low")

    score = critical * 10 + high * 5 + medium * 2 + low * 1

    if critical > 0 and score >= 20:
        return "F"
    if critical > 0:
        return "E"
    if high >= 3:
        return "D"
    if high > 0 or medium >= 5:
        return "C"
    if medium > 0:
        return "B"
    return "A"


def format_finding(f: Finding) -> str:
    """格式化單個 finding 為 Markdown"""
    emoji = SEVERITY_EMOJI.get(f.severity, "⚪")
    conf_emoji = CONFIDENCE_EMOJI.get(f.confidence, "⚪")

    return f"""### {emoji} {f.rule_name}
- **規則 ID**: `{f.rule_id}`
- **嚴重度**: {emoji} {f.severity.upper()} | **置信度**: {conf_emoji} {f.confidence}
- **位置**: `{f.file_path}:{f.line_number}`
- **命中**: `{f.matched_text}`
- **說明**: {f.description}
- **建議**: {f.remediation}

```text
{f.context_line}
```"""


def generate_report(
    target: str,
    pi_check: Dict,
    skill_results: Dict[str, DetectionResult],
    overall_grade: str = None,
) -> str:
    """生成 Markdown 風險報告

    target: 掃描目標路徑/URL
    pi_check: 來自 pi_check 的結果
    skill_results: {category: DetectionResult}
    overall_grade: 可選，預先計算好的綜合評分
    """
    all_findings: List[Finding] = []
    for r in skill_results.values():
        all_findings.extend(r.findings)

    if overall_grade is None:
        overall_grade = calculate_risk_grade(all_findings)

    grade_meaning = {
        "A": "✅ 安全",
        "B": "🟢 輕微風險",
        "C": "🟡 中等風險",
        "D": "🟠 較高風險",
        "E": "🔴 高風險",
        "F": "🔴🔴 極高風險，建議不要使用",
    }

    # 統計
    total_files = sum(r.scanned_files for r in skill_results.values())
    total_findings = len(all_findings)
    critical = sum(1 for f in all_findings if f.severity == "critical")
    high = sum(1 for f in all_findings if f.severity == "high")
    medium = sum(1 for f in all_findings if f.severity == "medium")
    low = sum(1 for f in all_findings if f.severity == "low")

    lines = [
        f"# Skill Safety-guard 風險報告",
        f"",
        f"> **掃描目標**: `{target}`  ",
        f"> **掃描文件數**: {total_files}  ",
        f"> **發現問題數**: {total_findings}（🔴 {critical} | 🟠 {high} | 🟡 {medium} | 🟢 {low}）",
        f"",
        f"## 綜合風險等級：{overall_grade}",
        f"",
        f"**{grade_meaning.get(overall_grade, '?')}**",
        f"",
        f"---",
        f"",
        f"## 第一層：Pi Agent 全局檢查",
        f"",
    ]

    # Pi 版本 CVE
    lines.append(f"### Pi 版本")
    if pi_check.get("pi_available"):
        version = pi_check.get("version", "unknown")
        lines.append(f"- **檢測到版本**: `{version}`")
        if pi_check.get("clean"):
            lines.append(f"- ✅ 不在已知漏洞範圍")
        else:
            lines.append(f"- ⚠️ 發現 {len(pi_check['vulnerabilities'])} 個已知漏洞：")
            for v in pi_check["vulnerabilities"]:
                lines.append(f"  - **{v['cve_id']}** ({v['severity'].upper()}): {v['description']}")
                lines.append(f"    - 💡 {v['remediation']}")
    else:
        lines.append(f"- ⚠️ Pi 命令不可用（{pi_check.get('error', '未知錯誤')}）")
        lines.append(f"- 💡 確保 Pi 已正確安裝並在 PATH 中")
    lines.append("")

    # auth.json 權限
    lines.append(f"### auth.json 權限")
    auth = pi_check.get("auth_check", {})
    if not auth:
        lines.append(f"- ℹ️ 未執行 auth.json 檢查")
    elif not auth.get("exists"):
        lines.append(f"- ℹ️ {auth.get('description', 'auth.json 不存在')}")
    elif auth.get("permissions_ok"):
        lines.append(f"- ✅ {auth.get('description', '權限正確')}")
    else:
        lines.append(f"- ⚠️ {auth.get('description', '權限異常')}")
        lines.append(f"- 💡 {auth.get('remediation', '')}")
    lines.append("")

    # 第二層：Skill 檢測結果
    lines.append("---")
    lines.append("")
    lines.append("## 第二層：Skill 內容檢測")
    lines.append("")

    category_names = {
        "credentials": "🔑 憑證洩露",
        "shell": "💀 危險 Shell 命令",
        "paths": "📁 敏感路徑訪問",
        "unicode": "🕵️ Unicode 隱寫",
        "critical_paths": "🚨 關鍵系統參數修改",
    }

    for cat, result in skill_results.items():
        cat_name = category_names.get(cat, cat)
        lines.append(f"### {cat_name}")
        lines.append(f"- 掃描文件: {result.scanned_files} 個")
        lines.append(f"- 發現問題: {len(result.findings)} 個")

        if result.findings:
            lines.append("")
            for f in result.findings:
                lines.append(format_finding(f))
                lines.append("")
        else:
            lines.append(f"- ✅ 未發現問題")
            lines.append("")

    # 底部：建議
    lines.append("---")
    lines.append("")
    lines.append("## 建議")

    if overall_grade in ["A", "B"]:
        lines.append("- ✅ 該 Skill 相對安全，可以繼續評估其他因素")
    elif overall_grade == "C":
        lines.append("- ⚠️ 建議人工審查每個發現項，確認是否為誤報")
    elif overall_grade in ["D", "E"]:
        lines.append("- ⚠️ 不建議安裝，除非你能解釋每個發現")
    else:  # F
        lines.append("- 🚫 強烈建議不要安裝此 Skill")
        lines.append("- 🔍 可嘗試聯繫作者修復，或尋找替代品")
        lines.append("- 💬 可使用 `/safety-check --report-fp <rule-id>` 報告誤報")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*本報告由 skill-safety-guard v1.5.0 自動生成*  ")
    lines.append("*規則庫開源：https://github.com/Wahero/Skill-safety-guard/blob/main/rules/*  ")
    lines.append("*發現誤報？執行 `/safety-check --report-fp <rule-id>`*")

    return "\n".join(lines)