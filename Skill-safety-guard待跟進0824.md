# Skill-safety-guard 待跟進事項（0824）

> **更新**：2026-08-24 ｜ **當前功能線**：**v3.7.0**（187 規則 / 10 類 / 自掃 SAFE / Pi 擴展 + Web 後端）
> **前版**：`Skill-safety-guard待跟進0819.md`

---

## 📊 今日完成摘要（14 commits）

| 版本 | 內容 | 關鍵 Commit |
|------|------|-------------|
| **v3.6.0** | 隱私行為檢測（6 規則）+ .mjs/.cjs 掃描修復 | `bad432e` |
| **v3.7.0** | Pi 擴展攔截（B-001）+ Web 後端（C-006） | `51c3460` |

### 🛡️ B-001：Pi 擴展（安裝前自動攔截 + 實時命令攔截）

| 項目 | 狀態 |
|------|------|
| `extension/safety-guard.ts`（純 TS 零依賴） | ✅ |
| `tool_call` hook：12 條危險 shell 攔截 | ✅ 實戰驗證通過 |
| `input` hook：`/skill:<name>` 載入前輕量掃描 | ✅ 實戰驗證通過 |
| 輕量掃描僅掃 SKILL.md + 根層安裝腳本（不遞迴） | ✅ 修復自掃誤報 |
| `package.json` `pi.extensions` 聲明 | ✅ |

### 🌐 C-006：Web 後端（選項 B：後端封裝）

| 項目 | 狀態 |
|------|------|
| `web/server.py`（stdlib ThreadingHTTPServer） | ✅ |
| `web/index.html`（功能型前端，決策徽章 + 表格） | ✅ |
| `src/skill_safety_guard/web_api.py`（結構化掃描） | ✅ |
| `POST /api/scans` + SSE 進度 | ✅ |
| SSE 失敗降級輪詢 + 30s 超時 | ✅ |
| Windows GBK 編碼修復 | ✅ |
| 發現項「漏洞說明：」「建議操作：」 | ✅ |
| 全局報告漏洞庫狀態（CLI + Web） | ✅ |
| 每日漏洞庫定義檢查（同日只查一次） | ✅ |
| 掃描完成後生成 MD 報告下載鏈接 | ✅ |

### 🔧 其他修復

| 問題 | 修復 |
|------|------|
| 擴展自掃 skill-safety-guard 誤報 44 發現 | 跳過 rules/tests/docs/demo，再改為只掃 SKILL.md + 安裝腳本 |
| Web 瀏覽器 Load failed | SSE 失敗降級為輪詢 |
| GBK 編碼 server.py 無法啟動 | stdout 設 UTF-8 |
| 大量殭屍 Python 進程佔舊代碼 | taskkill 全殺後重啟 |

---

## 🔴 P0 緊急

| ID | 事項 | 說明 |
|----|------|------|
| P0-01 | Web server 版號硬編碼 `3.6.0` | health/version 應讀 `__version__`（`web/server.py` 及 `web/index.html` header） |
| P0-02 | 擴展需 reload 後才生效 | 首次 `pi install` 後需手動 `/reload`，考慮自動載入或提示 |

---

## 🟠 P1 重要

| ID | 事項 | 來源 | 說明 |
|----|------|------|------|
| B-002 | pytest 補 V-03 / V-05 | 0819 | 半天工時 |
| B-003 | 誤報反饋文檔 | 0819 | README 缺官方誤報流程 |
| B-004 | 白名單貢獻教程 | 0819 | 含 SELFSCAN_RULES 三區 |
| B-005 | 置信度分級完善 | 0819 | 半天工時 |
| B-007 | 免費額度機制審查 | 0819 | 是否加 SKIP_LICENSE 環境變數？ |
| P1-01 | Web 前端載入外部字體 | 今日 | Inter / Noto Sans SC 需 CDN 或本地化 |
| P1-02 | Web 掃描歷史持久化 | 今日 | 目前是進程內記憶體，重啟即清空 |
| P1-03 | Web 報告目錄清理 | 今日 | `report/` 目錄累積，需自動清理策略 |

---

## 🟡 P2 增強

| ID | 事項 | 來源 | 說明 |
|----|------|------|------|
| C-001 | GitHub Pages demo | 0819 | ⚠️ Wahero 免費計劃不支持 Pages |
| C-002 | 社區推廣 | 0819 | V2EX / Twitter / Reddit 優先？ |
| C-003 | 規則庫持續擴展 | 0819 | 187 條，更多 AI Agent 框架 |
| C-004 | GitHub Action 正式化 | 0819 | 1-2 天 |
| C-005 | Pre-commit Hook | 0819 | 半天 |
| P2-01 | Web 前端設計原型整合 | 今日 | `demo/web-ui/index.html`（7 視圖）→ 逐步遷移到功能前端 |
| P2-02 | 擴展支援更多攔截點 | 今日 | `user_bash` event（`!` 命令）、`read` tool（auth.json 防護） |

---

## 🔵 P3 後置（Phase 4）

| ID | 事項 | 來源 | 說明 |
|----|------|------|------|
| D-001 | 多框架適配 | 0819 | OpenClaude / OpenCode / Claude Code |
| D-002 | MCP 代理網關 | 0819 | 運行時攔截 |
| ~~D-003~~ | ~~實時危險命令攔截~~ | ~~0819~~ | ✅ 已完成（Pi 擴展 tool_call hook） |

---

## 🚀 Pi Package 上線

| 步驟 | 狀態 |
|------|------|
| 1. 倉庫設 Public | ⬜ |
| 2. 生成 demo 截圖 → package.json `pi.image` | ⬜ |
| 3. `npm publish` | ⬜ |
| 4. 驗證 https://pi.dev/packages | ⬜ |

---

## ❓ 待決策

1. **SKIP_LICENSE**：是否加環境變數讓 CI/開發環境不耗免費額度？
2. **推廣優先渠道**：V2EX / Twitter / Reddit？
3. **Pages 替代**：Vercel / Netlify？
4. **Web 前端方向**：繼續增強功能前端 vs 遷移到 React/Vite 正式版？

---

## 🔧 環境事實速查

- Windows；Python 3.11；Node v24.15.0
- 一律 `PYTHONIOENCODING=utf-8`；`python scripts/safety-check` 或 `python -m skill_safety_guard`
- Web 啟動：`taskkill //F //IM python.exe && cd D:/AI/@項目/Skill-safety-guard && PYTHONPATH=src python -B web/server.py --host 0.0.0.0 --port 8765`
- 擴展目錄：`~/.pi/agent/extensions/safety-guard.ts`（修改後需 `/reload`）
- 運行時資料：`~/.skill-safety-guard/`（license / usage / vuln 快取 / daily_check）
- 本環境無外網（raw 超時），api.github.com / api.osv.dev 可達
- gh CLI 可用；AskUserQuestion 非 TUI 不可用
- `report/` = 本地掃描報告 + Web 生成的 MD（gitignore + 白名單 `*/report/*`）

---

*生成：2026-08-24 ｜ 倉庫：https://github.com/Wahero/Skill-safety-guard ｜ 功能線 v3.7.0*