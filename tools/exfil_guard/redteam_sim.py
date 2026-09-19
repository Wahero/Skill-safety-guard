"""exfil_guard 紅隊模擬（驗證檢測 + 可選響應）

默認僅做「檢測」驗證：在 %TEMP% 寫入一個仿外洩產物，確認規則命中。
加 --execute（且 config response.mode != audit）才會真正對該樣本執行
block/nuke 響應（修改 ACL / 防火牆），需管理員且經審批。

用法：
  python tools/exfil_guard/redteam_sim.py
  python tools/exfil_guard/redteam_sim.py --execute
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import yaml
from guard import load_rules, evaluate_file
from responder import respond


def main() -> int:
    ap = argparse.ArgumentParser(description="exfil_guard red-team simulation")
    ap.add_argument("--execute", action="store_true", help="真正執行響應（修改系統，需管理員）")
    args = ap.parse_args()

    with open(os.path.join(HERE, "config.yaml"), encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    rules = load_rules(cfg)
    temp_dirs = [os.path.expandvars(p) for p in cfg.get("watch", {}).get("paths", [])]
    temp = temp_dirs[0] if temp_dirs else os.getenv("TEMP", "/tmp")

    payload = (
        "repo_snapshot_extra_manifest/v1\n"
        + "\n".join(f"repo{i}/.git/HEAD" for i in range(12))
        + "\nkeyWrapAlgorithm publicKeySpkiPem aes-256-ctr\n"
    )
    target = os.path.join(temp, "redteam_leak.zip")
    with open(target, "w", encoding="utf-8") as f:
        f.write(payload)
    print(f"[redteam] 已寫入樣本: {target}")

    hits = evaluate_file(target, payload, rules, temp_dirs)
    if not hits:
        print("[redteam] 檢測未命中 —— 守禦邏輯需檢查")
        return 1
    print(f"[redteam] 檢測命中 {len(hits)} 條:")
    for h in hits:
        print(f"   - [{h['severity']}] {h['rule_id']} ({h['name']})")

    if args.execute:
        mode = cfg.get("response", {}).get("mode", "audit")
        print(f"[redteam] --execute：以 mode={mode} 響應樣本")
        for h in hits:
            respond(h, mode, cfg)
    else:
        print("[redteam] 未加 --execute，僅驗證檢測（不修改系統）。可刪除樣本。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
