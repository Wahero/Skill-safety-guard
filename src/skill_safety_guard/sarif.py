"""SARIF v2.1.0 輸出格式（F-042）

SARIF (Static Analysis Results Interchange Format) 是 GitHub Code Scanning 等工具的標準格式。
詳見：https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html
"""
import json
from typing import Dict, List


SARIF_VERSION = "2.1.0"
SARIF_SCHEMA = "https://json.schemastore.org/sarif-2.1.0.json"


def severity_to_sarif_level(severity: str) -> str:
    """將內部嚴重度映射到 SARIF level"""
    mapping = {
        "critical": "error",
        "high": "error",
        "medium": "warning",
        "low": "note",
        "ok": "none",
    }
    return mapping.get(severity, "warning")


def findings_to_sarif(findings: List[Dict], target: str, tool_version: str = "1.5.0") -> Dict:
    """將 findings 轉換為 SARIF 格式

    findings: [{rule_id, rule_name, severity, confidence, file_path, line_number, matched_text, ...}]
    """
    results = []

    for f in findings:
        rule_id = f.get("rule_id", "unknown")
        result = {
            "ruleId": rule_id,
            "level": severity_to_sarif_level(f.get("severity", "warning")),
            "message": {
                "text": f.get("rule_name", rule_id),
            },
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {
                            "uri": f.get("file_path", target),
                        },
                        "region": {
                            "startLine": f.get("line_number", 1),
                            "snippet": {
                                "text": f.get("matched_text", ""),
                            },
                        },
                    }
                }
            ],
            "properties": {
                "confidence": f.get("confidence", "medium"),
                "category": f.get("category", ""),
                "security-severity": _severity_to_score(f.get("severity", "medium")),
                "tags": ["security", "skill-safety-guard", f.get("category", "")],
            },
            "rule": {
                "id": rule_id,
                "index": 0,
            },
        }
        results.append(result)

    sarif = {
        "$schema": SARIF_SCHEMA,
        "version": SARIF_VERSION,
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "skill-safety-guard",
                        "version": tool_version,
                        "informationUri": "https://github.com/Wahero/Skill-safety-guard",
                        "rules": _build_rules_index(findings),
                        "properties": {
                            "category": "security",
                            "tags": ["ai-security", "skill-scanning", "agent-security"],
                        },
                    }
                },
                "results": results,
                "originalUriBaseIds": {
                    "PROJECTROOT": {"uri": "file://" + target}
                },
            }
        ],
    }

    return sarif


def _severity_to_score(severity: str) -> float:
    """將嚴重度映射到 CVSS 風格分數（用於 GitHub Code Scanning）"""
    mapping = {
        "critical": 9.5,
        "high": 7.5,
        "medium": 5.0,
        "low": 3.0,
    }
    return mapping.get(severity, 5.0)


def _build_rules_index(findings: List[Dict]) -> List[Dict]:
    """構建規則索引（去重）"""
    seen = set()
    rules = []
    for f in findings:
        rule_id = f.get("rule_id", "unknown")
        if rule_id in seen:
            continue
        seen.add(rule_id)
        rules.append({
            "id": rule_id,
            "name": f.get("rule_name", rule_id),
            "shortDescription": {
                "text": f.get("description", rule_id)[:100],
            },
            "fullDescription": {
                "text": f.get("description", rule_id),
            },
            "help": {
                "text": f.get("remediation", ""),
            },
            "defaultConfiguration": {
                "level": severity_to_sarif_level(f.get("severity", "warning")),
            },
            "properties": {
                "category": f.get("category", ""),
            },
        })
    return rules


def findings_to_sarif_string(findings: List[Dict], target: str, tool_version: str = "1.5.0") -> str:
    """SARIF 字符串輸出"""
    return json.dumps(findings_to_sarif(findings, target, tool_version), ensure_ascii=False, indent=2)