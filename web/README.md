# skill-safety-guard Web 後端

CLI 的「薄 UI 層」——把現有 Python 檢測引擎封裝成 HTTP API + 功能型前端，純 stdlib、零外部依賴。

> 對齊 [`docs/WEB_UI_DESIGN.md`](../docs/WEB_UI_DESIGN.md) §8 的 API 對照表。

## 啟動

```bash
cd web
python server.py --port 8765
```

開啟：
- **功能型前端**：http://127.0.0.1:8765/ （粘貼目標 → 掃描 → 決策大徽章 + 發現表格）
- **設計原型**：http://127.0.0.1:8765/ui （`demo/web-ui/index.html`，7 視圖 SPA 原型）

## API

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/api/health` | 健康檢查 |
| POST | `/api/scans` | 建立掃描 job（body: `{target, include_pi?, include_mcp?}`），回傳 `{job_id}` |
| GET | `/api/scans` | 歷史列表 |
| GET | `/api/scans/{id}` | job 結果（running 時回 status + progress） |
| GET | `/api/scans/{id}/events` | SSE 進度流 |
| GET | `/api/license` | 許可狀態 |
| GET | `/api/vulns/status` | 漏洞庫狀態 |

## 快速測試

```bash
# 健康檢查
curl http://127.0.0.1:8765/api/health

# 建立掃描（本地路徑）
curl -X POST http://127.0.0.1:8765/api/scans \
  -H "Content-Type: application/json" \
  -d '{"target": "./demo"}'

# 查結果（把 <job_id> 換成上一步回傳的 id）
curl http://127.0.0.1:8765/api/scans/<job_id>
```

## 架構

```
web/server.py            # stdlib HTTP server（ThreadingHTTPServer）+ SSE
web/index.html           # 功能型前端（決策徽章 + 發現表格）
src/skill_safety_guard/web_api.py   # 結構化掃描（複用 cli.scan_target / reporter）
src/skill_safety_guard/*            # 檢測引擎（不重寫）
```

**原則**：Web 不重寫檢測引擎，只複用 `scan_target` / `calculate_risk_grade` / `make_install_decision`。`web_api.run_scan` 不觸碰許可額度、不列印、不寫檔。

## 注意

- Job store 為**進程內記憶體**（適合單機個人開發者），重啟即清空。
- 掃描在後台執行緒執行，GitHub URL 目標會 `git clone`（依賴 git 已安裝）。
- 本目錄檔不含危險樣本，無需白名單豁免（自掃 SAFE/A/0）。
