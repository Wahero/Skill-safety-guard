"""exfil_guard 開機自啟註冊（需管理員）

經 Windows 工作排程器（schtasks）註冊登入時以最高權限啟動 guard.py。
執行本腳本即修改系統排程，須具備管理員權限且經審批。

用法（管理員 CMD/PowerShell）：
  python tools/exfil_guard/install_autostart.py
  python tools/exfil_guard/install_autostart.py --remove
"""
import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TASK_NAME = "ExfilGuard"
GUARD_PY = os.path.join(HERE, "guard.py")
PY = sys.executable


def build_cmd(remove: bool) -> list:
    if remove:
        return ["schtasks", "/Delete", "/TN", TASK_NAME, "/F"]
    # 以 SYSTEM/最高權限在用戶登入時啟動；/RL HIGHEST 需管理員
    return [
        "schtasks", "/Create", "/TN", TASK_NAME,
        "/TR", f'"{PY}" "{GUARD_PY}"',
        "/SC", "ONLOGON", "/RL", "HIGHEST", "/F",
    ]


def main() -> int:
    ap = argparse.ArgumentParser(description="註冊/移除 exfil_guard 開機自啟")
    ap.add_argument("--remove", action="store_true")
    args = ap.parse_args()
    cmd = build_cmd(args.remove)
    print("將執行:", " ".join(cmd))
    try:
        subprocess.run(cmd, check=True)
        print("OK" if not args.remove else "已移除")
        return 0
    except subprocess.CalledProcessError as e:
        print("失敗（需管理員權限）:", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
