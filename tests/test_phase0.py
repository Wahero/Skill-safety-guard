"""Phase 0 驗證測試套件：
- V-02: YAML 解析驗證
- V-04: 正則檢測驗證（檢出率 ≥80%）
- V-06: 誤報基線測試（誤報率 ≤10%）
"""
import sys
from pathlib import Path

# 確保 src/ 在 Python path 中
src_path = Path(__file__).resolve().parent.parent / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))

# Windows 終端編碼
if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from skill_safety_guard.cli import scan_target
from skill_safety_guard.parser import parse_skill_md, parse_skill_file, validate_skill_frontmatter
from skill_safety_guard.reporter import calculate_risk_grade
from skill_safety_guard.detectors.base import Finding


# 顏色（禁用 emoji，改用 ASCII）
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def colored(text: str, color: str) -> str:
    # 移除 emoji 以避免 Windows 編碼問題
    return f"{color}{text}{RESET}"


def test_v02_yaml_parser():
    """V-02: YAML 解析驗證"""
    print(colored("\n=== V-02: YAML 解析驗證 ===", BLUE))

    sample_md = """---
name: test-skill
description: 測試 Skill
allowed-tools:
  - read
  - bash
version: 1.0.0
---

# Body
This is the body content.
"""

    fm, body = parse_skill_md(sample_md)
    assert fm.get("name") == "test-skill", f"name 解析失敗: {fm.get('name')}"
    assert fm.get("description") == "測試 Skill", f"description 解析失敗"
    assert "read" in fm.get("allowed-tools", []), "allowed-tools 列表解析失敗"
    assert "Body" in body, "body 提取失敗"

    print(colored("[OK] YAML frontmatter 解析正確", GREEN))
    print(f"  - name: {fm.get('name')}")
    print(f"  - description: {fm.get('description')}")
    print(f"  - allowed-tools: {fm.get('allowed-tools')}")
    print(f"  - body 長度: {len(body)} 字符")

    # 驗證缺失字段
    validation = validate_skill_frontmatter({"name": "x", "description": "y"})
    assert not validation["valid"], "缺失字段應被標記為 invalid"
    assert "allowed-tools" in validation["missing"]
    print(colored("[OK] 缺失字段檢測正確", GREEN))

    return True


def test_v04_detection_rate():
    """V-04: 正則檢測驗證（檢出率 ≥80%）"""
    print(colored("\n=== V-04: 正則檢測驗證 ===", BLUE))

    fixtures_dir = Path(__file__).resolve().parent / "fixtures" / "malicious"
    if not fixtures_dir.exists():
        print(colored(f"✗ 惡意樣本目錄不存在: {fixtures_dir}", RED))
        assert False, f"惡意樣本目錄不存在: {fixtures_dir}"

    malicious_samples = [d for d in fixtures_dir.iterdir() if d.is_dir()]
    print(f"  找到 {len(malicious_samples)} 個惡意樣本")

    detected = 0
    total_findings_per_sample = {}

    for sample in malicious_samples:
        print(f"\n  掃描: {sample.name}")
        # 使用 argparse Namespace mock
        import argparse
        args = argparse.Namespace(pi=False)

        results = scan_target(sample, args)

        all_findings = []
        for r in results.values():
            if hasattr(r, "findings"):
                all_findings.extend(r.findings)

        total_findings_per_sample[sample.name] = len(all_findings)

        if all_findings:
            detected += 1
            print(colored(f"    [PASS] 檢出 {len(all_findings)} 個問題", GREEN))
            for f in all_findings[:3]:
                print(f"      - {f.rule_name} ({f.severity})")
            if len(all_findings) > 3:
                print(f"      ... 還有 {len(all_findings) - 3} 個")
        else:
            print(colored(f"    [FAIL] 未檢出任何問題", RED))

    detection_rate = detected / len(malicious_samples) if malicious_samples else 0
    print(colored(f"\n  檢出率: {detected}/{len(malicious_samples)} = {detection_rate:.0%}", YELLOW if detection_rate < 1.0 else GREEN))

    if detection_rate >= 0.8:
        print(colored("  [PASS] 通過 V-04 驗證標準（≥80%）", GREEN))
    else:
        print(colored(f"  [FAIL] 未通過 V-04 驗證標準", RED))
        assert False, f"V-04 檢出率 {detection_rate:.0%} < 80%（{detected}/{len(malicious_samples)}）"
    return True


def test_v06_false_positive_baseline():
    """V-06: 誤報基線測試（目標 ≤10%，加入白名單後 ≤3%）"""
    print(colored("\n=== V-06: 誤報基線測試 ===", BLUE))

    fixtures_dir = Path(__file__).resolve().parent / "fixtures" / "clean"
    if not fixtures_dir.exists():
        print(colored(f"✗ 乾淨樣本目錄不存在: {fixtures_dir}", RED))
        assert False, f"乾淨樣本目錄不存在: {fixtures_dir}"

    clean_samples = [d for d in fixtures_dir.iterdir() if d.is_dir()]
    print(f"  找到 {len(clean_samples)} 個乾淨樣本")

    false_positives = 0
    total_clean = len(clean_samples)
    fp_details = {}

    for sample in clean_samples:
        print(f"\n  掃描: {sample.name}")
        import argparse
        args = argparse.Namespace(pi=False)

        results = scan_target(sample, args)

        # 過濾掉低置信度（low）的命中——它們可能是合理的觸發
        high_conf_findings = []
        all_findings = []
        for r in results.values():
            if hasattr(r, "findings"):
                all_findings.extend(r.findings)
                high_conf_findings.extend([f for f in r.findings if f.confidence != "low"])

        if all_findings:
            # 注意：我們只計算 high/medium 置信度的命中為「誤報候選」
            print(colored(f"    [FP] 命中 {len(all_findings)} 條規則", YELLOW))
            for f in all_findings:
                print(f"      - {f.rule_id} ({f.confidence}): {f.rule_name}")
            false_positives += 1
            fp_details[sample.name] = [f.rule_id for f in all_findings]
        else:
            print(colored(f"    [CLEAN] 無誤報", GREEN))

    fp_rate = false_positives / total_clean if total_clean else 0
    print(colored(f"\n  誤報率: {false_positives}/{total_clean} = {fp_rate:.0%}", YELLOW if fp_rate > 0 else GREEN))

    if fp_rate <= 0.1:
        print(colored("  [PASS] 通過 V-06 驗證標準（≤10%）", GREEN))
    else:
        print(colored(f"  [WARN] 誤報率 {fp_rate:.0%} 高於 10% 標準", YELLOW))
        print(colored(f"  -> 需要檢查白名單規則是否覆蓋", YELLOW))
        if fp_details:
            print(colored(f"  誤報詳情:", YELLOW))
            for sample, rules in fp_details.items():
                print(f"    {sample}: {rules}")
        assert False, f"V-06 誤報率 {fp_rate:.0%} > 10%"
    return True


def main():
    """運行所有 Phase 0 測試"""
    print(colored("========================================", BLUE))
    print(colored("  skill-safety-guard Phase 0 驗證測試", BLUE))
    print(colored("========================================", BLUE))

    results = {}

    # V-02
    try:
        results["V-02"] = test_v02_yaml_parser()
    except Exception as e:
        print(colored(f"✗ V-02 拋出異常: {e}", RED))
        results["V-02"] = False

    # V-04
    try:
        results["V-04"] = test_v04_detection_rate()
    except Exception as e:
        print(colored(f"✗ V-04 拋出異常: {e}", RED))
        results["V-04"] = False

    # V-06
    try:
        results["V-06"] = test_v06_false_positive_baseline()
    except Exception as e:
        print(colored(f"✗ V-06 拋出異常: {e}", RED))
        results["V-06"] = False

    # 總結
    print(colored("\n" + "=" * 50, BLUE))
    print(colored("Phase 0 驗證總結", BLUE))
    print(colored("=" * 50, BLUE))
    all_passed = True
    for vid, passed in results.items():
        status = colored("[PASS]", GREEN) if passed else colored("[FAIL]", RED)
        print(f"  {vid}: {status}")
        if not passed:
            all_passed = False

    print()
    if all_passed:
        print(colored(">>> Phase 0 全部通過！可以進入 Phase 1。", GREEN))
    else:
        print(colored(">>> 部分驗證失敗，需要調整後重試。", YELLOW))

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())