"""auth.json 文件權限檢查（F-006）

auth.json 應為 600（僅本人可讀寫），其他權限會被掃出。
"""
import os
import stat
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

    st = auth_path.stat()
    mode = stat.S_IMODE(st.st_mode)

    # 期望：600 (rw-------) = 0o600 = 384
    # 過寬：644/664/666/755/777 等
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