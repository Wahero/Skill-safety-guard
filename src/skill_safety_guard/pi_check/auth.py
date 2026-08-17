"""auth.json 文件權限檢查（F-006）

auth.json 應為 600（僅本人可讀寫），其他權限會被掃出。

跨平台說明：
- Linux/Mac: 使用 os.stat() 讀取 POSIX 權限
- Windows: 使用 icacls 命令讀取 ACL（os.stat() 不反映真實 ACL）
"""
import os
import platform
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional


def get_auth_path() -> Optional[Path]:
    """獲取 auth.json 路徑"""
    home = Path.home()
    candidates = [
        home / ".pi" / "agent" / "auth.json",
        home / ".pi" / "auth.json",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def _check_windows_acl(auth_path: Path) -> Dict:
    """Windows 下使用 icacls 讀取 ACL 並評估安全性

    安全標準：僅當前用戶有讀寫權限，其他用戶無權限
    """
    try:
        result = subprocess.run(
            ["icacls", str(auth_path)],
            capture_output=True, text=True, timeout=5,
        )
        output = result.stdout

        # 解析 icacls 輸出
        # 格式如：DOMAIN\username:(R,W) 或 (N) 表示無權限
        username = os.environ.get("USERNAME", "")

        # icacls 輸出格式：第一行 = "文件路徑 ACL條目"，後續行 = 成功消息
        # 抽取所有 "username:(perms)" 模式的條目
        acl_pattern = re.compile(r"([\w\\\.\-\-]+):\(([RWXDMF,\sN]+)\)")
        user_acls = []
        for match in acl_pattern.finditer(output):
            user_acls.append((match.group(1), match.group(2)))

        # 檢查：當前用戶是否有 R/W
        current_user_has_rw = False
        for user, perms in user_acls:
            user_lower = user.lower()
            username_lower = username.lower()
            # icacls 用戶可能是 "DOMAIN\username" 或 "username" 格式
            user_short = user_lower.split("\\")[-1]
            if (
                username_lower in user_lower
                or user_lower in username_lower
                or username_lower == user_short
                or user_short == username_lower
            ):
                if "R" in perms and "W" in perms:
                    current_user_has_rw = True
                break

        # 檢查：其他用戶是否有任何權限
        others_have_perms = False
        dangerous_users = ["everyone", "users", "authenticated users", "administrators", "guests"]
        for user, perms in user_acls:
            user_lower = user.lower()
            for danger in dangerous_users:
                if danger in user_lower and perms != "N":
                    others_have_perms = True
                    break

        perm_str = "Windows ACL"
        if current_user_has_rw and not others_have_perms:
            return {
                "permissions": perm_str,
                "permissions_ok": True,
                "severity": "ok",
                "description": f"Windows ACL 符合安全要求（僅 {username} 有讀寫權限）",
            }
        elif current_user_has_rw and others_have_perms:
            return {
                "permissions": perm_str,
                "permissions_ok": False,
                "severity": "high",
                "description": "Windows ACL 過寬：其他用戶也有權限",
            }
        else:
            return {
                "permissions": perm_str,
                "permissions_ok": False,
                "severity": "critical",
                "description": "Windows ACL 配置錯誤：當前用戶無讀寫權限",
            }
    except Exception as e:
        return {
            "permissions": "unknown",
            "permissions_ok": False,
            "severity": "high",
            "description": f"無法讀取 Windows ACL: {e}",
        }


def check_auth_permissions() -> Dict:
    """檢查 auth.json 文件權限

    返回：
    {
        "exists": bool,
        "path": str,
        "permissions": str (如 "0600"),
        "permissions_ok": bool,
        "severity": str (critical/high/medium/low/ok),
        "description": str,
        "remediation": str
    }
    """
    auth_path = get_auth_path()
    if auth_path is None:
        return {
            "exists": False,
            "path": "",
            "permissions": "",
            "permissions_ok": True,  # 不存在不算違規
            "severity": "ok",
            "description": "auth.json 不存在，無需檢查",
            "remediation": "",
        }

    if sys.platform.startswith("win"):
        # Windows: 使用 icacls
        result = _check_windows_acl(auth_path)
        result["exists"] = True
        result["path"] = str(auth_path)
        if not result["permissions_ok"]:
            username = os.environ.get("USERNAME", "")
            result["remediation"] = (
                f"執行 icacls 修復：\n"
                f"  icacls \"{auth_path}\" /inheritance:r\n"
                f"  icacls \"{auth_path}\" /grant:r \"{username}:(R,W)\"\n"
                f"  icacls \"{auth_path}\" /remove Everyone Users \"Authenticated Users\"\n"
                f"或直接執行：python scripts/fix_auth_permissions.py"
            )
        else:
            result["remediation"] = ""
        return result

    # Linux/Mac: 使用 POSIX 權限
    import stat
    st = auth_path.stat()
    mode = stat.S_IMODE(st.st_mode)

    world_readable = bool(mode & stat.S_IRWXO) or bool(mode & stat.S_IRWXG)
    group_readable = bool(mode & stat.S_IRWXG)

    perm_str = oct(mode)

    if mode == 0o600:
        return {
            "exists": True,
            "path": str(auth_path),
            "permissions": perm_str,
            "permissions_ok": True,
            "severity": "ok",
            "description": f"權限 {perm_str} 符合安全要求",
            "remediation": "",
        }

    severity = "critical" if (world_readable or mode & 0o077) else "high"
    description_parts = []
    if world_readable:
        description_parts.append("可被其他用戶讀取")
    if group_readable:
        description_parts.append("可被同組用戶讀取")
    if not description_parts:
        description_parts.append("權限過寬")

    return {
        "exists": True,
        "path": str(auth_path),
        "permissions": perm_str,
        "permissions_ok": False,
        "severity": severity,
        "description": f"權限 {perm_str} 不安全：{'; '.join(description_parts)}",
        "remediation": f"執行：chmod 600 {auth_path}",
    }