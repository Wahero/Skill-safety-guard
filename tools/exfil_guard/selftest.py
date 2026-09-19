"""exfil_guard 自檢（無需管理員）

驗證：平台、規則載入、檢測邏輯正/負樣本。不修改任何系統。
用法：python tools/exfil_guard/selftest.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import yaml
from guard import load_rules, evaluate_file


def check(label: str, cond: bool) -> bool:
    print(f"[{'PASS' if cond else 'FAIL'}] {label}")
    return cond


def main() -> int:
    ok = True
    ok &= check("平台為 Windows", sys.platform == "win32")

    with open(os.path.join(HERE, "config.yaml"), encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}

    rules = load_rules(cfg)
    ok &= check(f"規則已載入 ({len(rules)} 條)", len(rules) > 0)

    temp_dirs = [os.path.expandvars(p) for p in cfg.get("watch", {}).get("paths", [])]
    sample = (
        "repo_snapshot_extra_manifest/v1\n"
        + "\n".join(f"proj{i}/.git/config" for i in range(12))
        + "\nkeyWrapAlgorithm publicKeySpkiPem aes-256-ctr\n"
    )
    hits = evaluate_file(os.path.join(temp_dirs[0] if temp_dirs else "/tmp", "leak.zip"),
                         sample, rules, temp_dirs)
    ok &= check("惡意樣本觸發命中", len(hits) > 0)

    benign = evaluate_file("clean.py", "print('hello world')", rules, temp_dirs)
    ok &= check("良性樣本無誤報", len(benign) == 0)

    print("SELFTEST:", "OK" if ok else "FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
