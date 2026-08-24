#!/usr/bin/env python3
"""skill-safety-guard Web 後端（純 stdlib，零外部依賴）

薄 UI 層：業務邏輯全部複用 src/skill_safety_guard/web_api.py。

端點（對齊 docs/WEB_UI_DESIGN.md §8）：
  GET  /                      → 功能型前端（web/index.html）
  GET  /ui                    → 設計原型（demo/web-ui/index.html）
  GET  /api/health            → 健康檢查
  POST /api/scans             → 建立掃描 job（異步），回傳 {job_id}
  GET  /api/scans             → 歷史列表（含分頁）
  GET  /api/scans/{id}        → job 結果（running 時回 status）
  GET  /api/scans/{id}/events → SSE 進度流
  GET  /api/license           → 許可狀態
  GET  /api/vulns/status      → 漏洞庫狀態

啟動：
  python web/server.py [--port 8765]
"""
from __future__ import annotations

import argparse
import json
import sys
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

# 開發模式：確保 src/ 在 Python path 中
SRC = Path(__file__).resolve().parent.parent / "src"
if SRC.exists():
    sys.path.insert(0, str(SRC))

from skill_safety_guard.web_api import run_scan  # noqa: E402

ROOT = Path(__file__).resolve().parent
WEB_INDEX = ROOT / "index.html"
DEMO_UI = ROOT.parent / "demo" / "web-ui" / "index.html"

# ---------------------------------------------------------------------------
# Job store（進程內記憶體，適合單機 / 個人開發者）
# ---------------------------------------------------------------------------
JOBS: dict = {}
JOBS_LOCK = threading.Lock()
_HISTORY_MAX = 100


def _new_job() -> str:
    jid = uuid.uuid4().hex[:12]
    with JOBS_LOCK:
        JOBS[jid] = {
            "id": jid,
            "target": "",
            "mode": "",
            "status": "queued",  # queued | running | done | error
            "progress": [],       # [{t, msg}]
            "result": None,
            "error": None,
            "created_at": time.time(),
            "done": threading.Event(),
        }
        # 限制歷史條數
        if len(JOBS) > _HISTORY_MAX:
            oldest = sorted(JOBS.keys(), key=lambda k: JOBS[k]["created_at"])[: len(JOBS) - _HISTORY_MAX]
            for k in oldest:
                del JOBS[k]
    return jid


def _run_job(jid: str, target: str, include_pi: bool, include_mcp: bool) -> None:
    job = JOBS[jid]
    job["target"] = target
    job["status"] = "running"

    def progress(msg: str) -> None:
        job["progress"].append({"t": time.time(), "msg": msg})

    try:
        result = run_scan(target, include_pi=include_pi, include_mcp=include_mcp, progress=progress)
        if result.get("error"):
            job["status"] = "error"
            job["error"] = result["error"]
        else:
            job["status"] = "done"
            job["result"] = result
    except Exception as e:  # noqa: BLE001
        job["status"] = "error"
        job["error"] = str(e)
    finally:
        job["done"].set()


def _job_brief(job: dict) -> dict:
    result = job.get("result") or {}
    return {
        "id": job["id"],
        "target": job["target"],
        "status": job["status"],
        "grade": result.get("grade"),
        "verdict": result.get("verdict"),
        "findings": (result.get("summary") or {}).get("total", 0),
        "elapsed_ms": result.get("elapsed_ms"),
        "created_at": job["created_at"],
        "error": job.get("error"),
    }


# ---------------------------------------------------------------------------
# HTTP Handler
# ---------------------------------------------------------------------------
class Handler(BaseHTTPRequestHandler):
    server_version = "skill-safety-guard/0.1"

    # -- helpers --
    def _send_json(self, obj, code: int = 200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path: Path):
        if not path.exists():
            self.send_error(404, "Not Found")
            return
        content_type = {
            ".html": "text/html; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".js": "application/javascript; charset=utf-8",
            ".json": "application/json; charset=utf-8",
            ".png": "image/png",
            ".svg": "image/svg+xml",
        }.get(path.suffix, "application/octet-stream")
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0) or 0)
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            return {}

    # -- routing --
    def do_OPTIONS(self):
        self._send_json({}, 204)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/health":
            return self._send_json({"ok": True, "version": "3.6.0", "jobs": len(JOBS)})

        if path == "/api/scans":
            jobs = [ _job_brief(j) for j in sorted(JOBS.values(), key=lambda j: -j["created_at"]) ]
            return self._send_json({"jobs": jobs})

        if path.startswith("/api/scans/") and path.endswith("/events"):
            jid = path.split("/")[3]
            return self._sse(jid)

        if path.startswith("/api/scans/"):
            jid = path.split("/")[3]
            job = JOBS.get(jid)
            if not job:
                return self._send_json({"error": "job not found"}, 404)
            if job["status"] in ("queued", "running"):
                return self._send_json({"id": jid, "status": job["status"], "progress": job["progress"]})
            if job["status"] == "error":
                return self._send_json({"id": jid, "status": "error", "error": job["error"]})
            return self._send_json({"id": jid, "status": "done", **job["result"]})

        if path == "/api/license":
            try:
                from skill_safety_guard.license import can_scan
                _can, info = can_scan()
                return self._send_json({"tier": info.get("tier"), **info})
            except Exception as e:  # noqa: BLE001
                return self._send_json({"error": str(e)}, 500)

        if path == "/api/vulns/status":
            try:
                from skill_safety_guard.vuln_feed import get_vuln_source_info
                return self._send_json(get_vuln_source_info())
            except Exception as e:  # noqa: BLE001
                return self._send_json({"error": str(e)}, 500)

        # 報告下載
        if path.startswith("/reports/"):
            filename = path.split("/reports/")[1]
            if ".." in filename or "/" in filename or "\\" in filename:
                return self.send_error(403, "Forbidden")
            report_path = Path(__file__).resolve().parent.parent / "report" / filename
            return self._send_file(report_path)

        # 靜態頁面
        if path in ("/", "/index.html"):
            return self._send_file(WEB_INDEX)
        if path == "/ui" or path == "/ui/":
            return self._send_file(DEMO_UI)

        return self.send_error(404, "Not Found")

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/scans":
            body = self._read_body()
            target = (body.get("target") or "").strip()
            if not target:
                return self._send_json({"error": "缺少 target 欄位"}, 400)
            include_pi = bool(body.get("include_pi", False))
            include_mcp = bool(body.get("include_mcp", False))
            jid = _new_job()
            t = threading.Thread(target=_run_job, args=(jid, target, include_pi, include_mcp), daemon=True)
            t.start()
            return self._send_json({"job_id": jid, "status": "queued"}, 202)

        return self._send_json({"error": "not found"}, 404)

    # -- SSE --
    def _sse(self, jid: str):
        job = JOBS.get(jid)
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        if not job:
            self.wfile.write(b"event: error\ndata: {\"error\":\"job not found\"}\n\n")
            self.wfile.flush()
            return

        sent = 0
        try:
            while True:
                prog = job["progress"]
                while sent < len(prog):
                    data = json.dumps(prog[sent], ensure_ascii=False)
                    self.wfile.write(f"event: progress\ndata: {data}\n\n".encode("utf-8"))
                    self.wfile.flush()
                    sent += 1
                if job["done"].is_set():
                    payload = json.dumps({"status": job["status"], "grade": (job.get("result") or {}).get("grade"), "error": job.get("error"), "report_md_url": (job.get("result") or {}).get("report_md_url")}, ensure_ascii=False)
                    self.wfile.write(f"event: done\ndata: {payload}\n\n".encode("utf-8"))
                    self.wfile.flush()
                    break
                time.sleep(0.2)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def log_message(self, *args):  # 靜默（避免刷屏）
        pass


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main():
    # Windows 終端 UTF-8 兼容
    if sys.platform.startswith("win"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    ap = argparse.ArgumentParser(description="skill-safety-guard Web 後端")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--host", default="127.0.0.1")
    args = ap.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    server.daemon_threads = True
    print(f"🛡️  skill-safety-guard Web 後端：http://{args.host}:{args.port}")
    print(f"   功能前端：http://{args.host}:{args.port}/")
    print(f"   設計原型：http://{args.host}:{args.port}/ui")
    print(f"   Ctrl+C 停止")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n停止服務")


if __name__ == "__main__":
    main()
