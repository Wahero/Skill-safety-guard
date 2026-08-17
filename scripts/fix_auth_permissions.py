#!/usr/bin/env python
"""Fix auth.json permissions on this machine.

Run once: python scripts/fix_auth_permissions.py
"""
import os
import subprocess
import sys
from pathlib import Path


def main():
    auth_path = Path.home() / ".pi" / "agent" / "auth.json"
    if not auth_path.exists():
        print(f"auth.json not found at: {auth_path}")
        print("Nothing to fix.")
        return 0

    print(f"Fixing permissions for: {auth_path}")

    if sys.platform.startswith("win"):
        # Windows: 使用 icacls
        # 1. 移除繼承
        result = subprocess.run(
            ["icacls", str(auth_path), "/inheritance:r"],
            capture_output=True, text=True,
        )
        print(f"  Remove inheritance: {'OK' if result.returncode == 0 else 'FAILED'}")

        # 2. 僅授予當前用戶讀寫權限
        username = os.environ.get("USERNAME") or os.environ.get("USER")
        result = subprocess.run(
            ["icacls", str(auth_path), "/grant:r", f"{username}:(R,W)"],
            capture_output=True, text=True,
        )
        print(f"  Grant {username} R/W: {'OK' if result.returncode == 0 else 'FAILED'}")

        # 3. 移除其他用戶
        result = subprocess.run(
            ["icacls", str(auth_path), "/remove", "Everyone", "Authenticated Users", "Users", "Administrators"],
            capture_output=True, text=True,
        )
        print(f"  Remove others: {'OK' if result.returncode == 0 else 'FAILED'}")
    else:
        # Linux/Mac: chmod 600
        os.chmod(auth_path, 0o600)
        print(f"  chmod 600: OK")

    # 驗證
    print("\nVerifying...")
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
    from skill_safety_guard.pi_check.auth import check_auth_permissions

    result = check_auth_permissions()
    if result["permissions_ok"]:
        print(f"[OK] auth.json 權限現在是安全的 ({result['permissions']})")
        return 0
    else:
        print(f"[FAIL] 仍然不安全: {result['description']}")
        return 1


if __name__ == "__main__":
    sys.exit(main())