"""exfil_guard 運行時守禦入口（Windows-only, opt-in）

用法：
  python tools/exfil_guard/guard.py [--config config.yaml] [--dry-run]

設計：
  - L1 文件監控（fs_watch）+ L2 產物啟發式 + L3 網絡關聯（net_watch）
  - 命中規則 -> responder（audit / block / nuke）+ notify
  - 完全獨立於 skill_safety_guard 靜態引擎，不污染其「純靜態」保證
  - mode=audit 或 --dry-run 時不修改任何系統；block/nuke 需管理員且經審批

退出：Ctrl-C
"""
import argparse
import logging
import os
import re
import sys
import threading
import time

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from fs_watch import DirectoryWatcher  # noqa: E402
from net_watch import get_external_connections  # noqa: E402
from responder import respond  # noqa: E402
from notify import notify  # noqa: E402

_logs_dir = os.path.join(HERE, "logs")
os.makedirs(_logs_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.FileHandler(os.path.join(_logs_dir, "guard.log"), encoding="utf-8"),
              logging.StreamHandler()],
)
logger = logging.getLogger("exfil_guard")


def _load_yaml_rules(path: str) -> list:
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return (yaml.safe_load(f) or {}).get("rules", [])


def load_rules(cfg: dict) -> list:
    rules = []
    rd = os.path.join(HERE, "rules")
    rc = cfg.get("rules", {})
    if rc.get("builtin_zcode", True):
        rules += _load_yaml_rules(os.path.join(rd, "builtin_zcode.yaml"))
    if rc.get("generic", True):
        rules += _load_yaml_rules(os.path.join(rd, "generic.yaml"))
    return rules


def _read_content(path: str, limit: int = 2_000_000) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read(limit)
    except (OSError, PermissionError):
        return ""


def evaluate_file(path: str, content: str, rules: list, temp_dirs: list) -> list:
    """對單個文件評估所有規則，返回命中事件列表。"""
    hits = []
    ext = os.path.splitext(path)[1].lower()
    under_temp = any(path.lower().startswith(t.lower()) for t in temp_dirs)
    for r in rules:
        rtype = r.get("type")
        rid = r.get("id")
        sev = r.get("severity", "medium")
        matched = False
        if rtype == "substring":
            matched = any(m in content for m in r.get("markers", []))
        elif rtype == "co_occur":
            matched = all(m in content for m in r.get("markers", []))
        elif rtype == "path_enum":
            n = len(re.findall(r.get("pattern", r"\.git/"), content))
            matched = n > int(r.get("threshold", 10))
        elif rtype == "ext_in_temp":
            matched = under_temp and ext in [e.lower() for e in r.get("extensions", [])]
        if matched:
            hits.append({
                "rule_id": rid, "severity": sev, "name": r.get("name", rid),
                "path": path, "ext": ext, "under_temp": under_temp,
            })
    return hits


class Guard:
    def __init__(self, cfg: dict, rules: list, dry_run: bool):
        self.cfg = cfg
        self.rules = rules
        self.dry_run = dry_run
        self.mode = "audit" if dry_run else cfg.get("response", {}).get("mode", "audit")
        self.temp_dirs = [os.path.expandvars(p) for p in cfg.get("watch", {}).get("paths", [])]
        self.deep_ext = [e.lower() for e in cfg.get("watch", {}).get("extensions_deep", [])]
        self.notify_method = cfg.get("notify", {}).get("method", "messagebox")
        self.watchers = []
        self._stop = threading.Event()
        self._recent_flag = threading.Event()  # L3 關聯用：近期有 exfil 命中

    def on_event(self, path: str, action: str):
        ext = os.path.splitext(path)[1].lower()
        # 僅對「深度擴展名」或文字類文件做規則評估，降低開銷
        if ext not in self.deep_ext and ext not in (".py", ".js", ".ts", ".ps1", ".bat", ".sh", ".md", ".json", ".yaml", ".yml"):
            return
        content = _read_content(path)
        hits = evaluate_file(path, content, self.rules, self.temp_dirs)
        if not hits:
            return
        for h in hits:
            logger.warning("命中規則 %s (%s): %s", h["rule_id"], h["severity"], path)
            if self.mode != "audit":
                self._recent_flag.set()
            respond(h, self.mode, self.cfg)
            notify(
                "exfil_guard 告警",
                f"[{h['severity']}] {h['name']}\n{h['rule_id']}\n{path}",
                method=self.notify_method,
                error=(h["severity"] == "critical"),
            )

    def _net_loop(self):
        interval = 5
        while not self._stop.is_set():
            try:
                conns = get_external_connections()
            except Exception as e:
                logger.error("L3 查詢異常: %s", e)
                conns = []
            if self.mode == "nuke" and self._recent_flag.is_set():
                remotes = {c["remote"].split(":")[0] for c in conns}
                if remotes:
                    from responder import nuke_firewall
                    nuke_firewall(list(remotes))
                self._recent_flag.clear()
            else:
                for c in conns:
                    logger.debug("L3 外連: pid=%s %s -> %s", c["pid"], c["local"], c["remote"])
            self._stop.wait(interval)

    def start(self):
        if sys.platform != "win32":
            logger.error("exfil_guard 僅支援 Windows；當前平台 %s，退出。", sys.platform)
            return
        for p in self.temp_dirs:
            if not os.path.isdir(p):
                logger.warning("監控目錄不存在，跳過: %s", p)
                continue
            w = DirectoryWatcher(p, self.cfg.get("watch", {}).get("recursive", True), self.on_event)
            w.start()
            self.watchers.append(w)
            logger.info("已啟動 L1 監控: %s", p)
        self._net = threading.Thread(target=self._net_loop, daemon=True)
        self._net.start()
        logger.info("exfil_guard 運行中（mode=%s）。Ctrl-C 退出。", self.mode)
        try:
            while not self._stop.is_set():
                self._stop.wait(1)
        except KeyboardInterrupt:
            logger.info("收到中斷，停止監控…")
            self.stop()

    def stop(self):
        self._stop.set()
        for w in self.watchers:
            w.stop()


def main():
    ap = argparse.ArgumentParser(description="Workspace Exfiltration Guard (runtime)")
    ap.add_argument("--config", default=os.path.join(HERE, "config.yaml"))
    ap.add_argument("--dry-run", action="store_true", help="觀測模式，不修改系統")
    args = ap.parse_args()

    with open(args.config, encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    rules = load_rules(cfg)
    logger.info("載入規則 %d 條", len(rules))
    Guard(cfg, rules, args.dry_run).start()


if __name__ == "__main__":
    main()
