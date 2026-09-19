"""響應層：audit / block / nuke

  audit : 僅記錄日誌 + 通知（不修改系統）
  block : 對命中文件/目錄施加拒絕寫入 ACL（icacls /deny Everyone:(W)）
  nuke  : 在 block 基礎上，額外經 netsh 防火牆封鎖外連（需管理員）

所有修改系統的操作（icacls / netsh）均僅在 mode != audit 時執行，
且須由具備權限的用戶顯式啟用（見 config.yaml response.mode）。
"""
import logging
import subprocess
import sys

logger = logging.getLogger("exfil_guard.responder")


def audit(event: dict) -> None:
    """audit 模式：記錄並返回（通知由 guard.py 統一處理）"""
    logger.warning(
        "AUDIT [%s] %s -> %s",
        event.get("rule_id"), event.get("severity"), event.get("path"),
    )


def block_path(path: str) -> bool:
    """block 模式：拒絕寫入 ACL。成功返回 True。"""
    try:
        subprocess.run(
            ["icacls", path, "/deny", "Everyone:(W)"],
            check=True, capture_output=True, text=True, timeout=30,
        )
        logger.info("BLOCK 已拒絕寫入 ACL: %s", path)
        return True
    except Exception as e:
        logger.error("BLOCK 失敗 %s: %s", path, e)
        return False


def nuke_firewall(targets: list) -> bool:
    """nuke 模式：經 netsh 防火牆封鎖外連。targets 為 IP/域名列表，空=全封。

    返回是否成功下發至少一條規則。
    """
    if not targets:
        targets = ["0.0.0.0/0"]
    ok = True
    for t in targets:
        rule = f"exfil_guard_block_{abs(hash(t)) % 10**8}"
        cmd = [
            "netsh", "advfirewall", "firewall", "add", "rule",
            f"name={rule}", "dir=out", "action=block",
            "remoteip=" + t, "enable=yes",
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=30)
            logger.info("NUKE 防火牆封鎖: %s", t)
        except Exception as e:
            logger.error("NUKE 防火牆失敗 %s: %s", t, e)
            ok = False
    return ok


def respond(event: dict, mode: str, cfg: dict) -> None:
    """依 mode 分派響應。"""
    audit(event)
    if mode == "audit":
        return
    path = event.get("path")
    if mode in ("block", "nuke") and path:
        block_path(path)
    if mode == "nuke" and cfg.get("response", {}).get("nuke_firewall"):
        nuke_firewall(cfg.get("response", {}).get("block_targets", []))
