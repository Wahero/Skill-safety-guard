"""V-05: TS 擴展規則與 YAML 一致性驗證（P2-2）

Python 端驗證 extension/safety-guard.ts 中的正則字串與 YAML 規則一致，
確保安裝前攔截（TS）和深度掃描（Python/YAML）使用相同檢測模式。
"""
import re
from pathlib import Path

import yaml

# 路徑
ROOT = Path(__file__).resolve().parent.parent
RULES_DIR = ROOT / "src" / "skill_safety_guard" / "rules"
# P3-1: 規則已從 safety-guard.ts 拆到 safety-guard-rules.ts（generator 產出）
TS_FILE = ROOT / "extension" / "safety-guard-rules.ts"


def _load_yaml_rules(filename: str) -> list:
    """載入 YAML 規則"""
    data = yaml.safe_load((RULES_DIR / filename).read_text(encoding="utf-8"))
    return data.get("rules", [])


def _unescape_ts_string(s: str) -> str:
    """將 TS 字串字面量的轉義還原為實際值

    TS "curl\\s+" 的實際值是 "curl\\s+"（\\\\ → \\）
    """
    return s.replace("\\\\", "\\")


def _extract_ts_patterns(ts_content: str, var_name: str) -> dict:
    """從 TS 源碼中提取 RegExp 字串，返回 {rule_id: pattern_str}"""
    patterns = {}
    lines = ts_content.split("\n")
    in_block = False
    current_id = None
    for i, line in enumerate(lines):
        if f"const {var_name}" in line:
            in_block = True
        if in_block:
            # 提取 id
            id_match = re.search(r'id:\s*"([^"]+)"', line)
            if id_match:
                current_id = id_match.group(1)
            # 提取 new RegExp("...")
            pat_match = re.search(r'new RegExp\("([^"]+)"\)', line)
            if pat_match and current_id:
                # 還原 TS 字串轉義（\\s → \s）
                patterns[current_id] = _unescape_ts_string(pat_match.group(1))
                current_id = None
            # 偵測 block 結束
            if line.strip() == "];" and patterns:
                break
    return patterns


def test_shell_rules_count():
    """TS SHELL_RULES 數量與 YAML 一致"""
    yaml_rules = _load_yaml_rules("dangerous_shell.yaml")
    ts_content = TS_FILE.read_text(encoding="utf-8")
    ts_patterns = _extract_ts_patterns(ts_content, "SHELL_RULES")
    assert len(ts_patterns) == len(yaml_rules), (
        f"TS has {len(ts_patterns)} shell rules, YAML has {len(yaml_rules)}"
    )


def test_shell_rules_pattern_match():
    """每條 TS shell 正則與 YAML pattern 字串一致"""
    yaml_rules = _load_yaml_rules("dangerous_shell.yaml")
    ts_content = TS_FILE.read_text(encoding="utf-8")
    ts_patterns = _extract_ts_patterns(ts_content, "SHELL_RULES")

    for rule in yaml_rules:
        rid = rule["id"]
        assert rid in ts_patterns, f"YAML rule {rid} not found in TS"
        assert ts_patterns[rid] == rule["pattern"], (
            f"Pattern mismatch for {rid}:\n"
            f"  YAML: {rule['pattern']}\n"
            f"  TS:   {ts_patterns[rid]}"
        )


def test_cred_rules_count():
    """TS CRED_RULES 數量 ≤ YAML（TS 為精簡版）"""
    yaml_rules = _load_yaml_rules("credentials.yaml")
    ts_content = TS_FILE.read_text(encoding="utf-8")
    ts_patterns = _extract_ts_patterns(ts_content, "CRED_RULES")
    for rid in ts_patterns:
        yaml_ids = [r["id"] for r in yaml_rules]
        assert rid in yaml_ids, f"TS cred rule {rid} not in YAML"


def test_cred_rules_pattern_subset():
    """TS 憑證正則為 YAML 的子集（TS 為精簡版，允許更少分支）"""
    yaml_rules = _load_yaml_rules("credentials.yaml")
    yaml_by_id = {r["id"]: r for r in yaml_rules}
    ts_content = TS_FILE.read_text(encoding="utf-8")
    ts_patterns = _extract_ts_patterns(ts_content, "CRED_RULES")

    for rid, ts_pat in ts_patterns.items():
        yaml_rule = yaml_by_id.get(rid)
        assert yaml_rule is not None, f"TS rule {rid} not in YAML"
        # TS pattern 的每個 | 分支都應出現在 YAML pattern 中
        ts_alternatives = set(ts_pat.split("|"))
        yaml_alternatives = set(yaml_rule["pattern"].split("|"))
        missing = ts_alternatives - yaml_alternatives
        assert not missing, (
            f"TS rule {rid} has alternatives not in YAML: {missing}"
        )
