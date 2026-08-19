# Skill-safety-guard 待跟進事項（0819）

> **更新**：2026-08-19 ｜ **當前功能線**：**v3.5.0**（181 規則 / 9 類 / 自掃 SAFE / Release 已建）
> **說明**：✓ = 已完成；⬜ = 待跟進；⚠️ = 有阻塞/需決策
> **前版**：`Skill-safety-guard待跟進0818.md`（已完成項已歸檔至此）

---

## 📊 總覽

| 優先級 | 數量 | 說明 |
|--------|------|------|
| 🔴 P0（緊急） | 4 | 已全部完成 ✅ |
| 🟠 P1（重要） | 7 | 2 需決策，5 可直接做 |
| 🟡 P2（增強） | 5 | 含新 Web UI 方向 |
| 🔵 P3（後置） | 3 | Phase 4 |
| 🚀 Pi Package 上線 | 4 步 | 待執行 |

---

## ✅ 本 session 已完成（2026-08-19，交接後）

### 交接驗證
| 項 | 結果 |
|----|------|
| pytest | 3 passed ✅ |
| 檢出率 | 8/8 = 100% ✅ |
| 自掃 | SAFE / A / 0 ✅（修復後）|

### A-001 ~ A-004（P0 全部完成）
| ID | 事項 | 結果 |
|----|------|------|
| A-001 | 版本統一 v3.5.0（`__init__.py`/`package.json`/`pyproject.toml`/`SKILL.md`/`README.md`）| ✅ commit fe32e92 |
| A-002 | Release v3.5.0（含完整 release notes）| ✅ https://github.com/Wahero/Skill-safety-guard/releases/tag/v3.5.0 |
| A-003 | CHANGELOG 3 個 [Unreleased] 歸檔（→3.5.0 / →2.0.0 歷史 / →已完成計劃）| ✅ |
| A-004 | TASKS.md 全面重寫為 v3.5.0 視角 | ✅ |

### 交接時發現的異常（已修復）
| 問題 | 修復 |
|------|------|
| `docs/PACKAGE_INTRO.md`（0818 後新增）含 ClawHavoc 攻擊示例未入白名單 → 自掃 8 發現 DANGER/F | 加白名單 → SAFE/A/0 |
| reporter.py 報告版本硬編碼 v1.5.0 | 改為讀取 `__version__` |

### 新增產出
| commit | 內容 |
|--------|------|
| bd7cc81 | **docs/SELFSCAN_RULES.md**：自掃維護規則（🟢可改動/🟡需自查/🔴禁止 三區 + 常見誤觸發模式 + 四步驗證流程）|
| 9d6d85a | **Web 界面設計**：docs/WEB_UI_DESIGN.md（完整規格）+ demo/web-ui/index.html（可交互原型，7 視圖）|

### 白名單現況（rules/whitelist.yaml）
- 新增：`*/docs/PACKAGE_INTRO.md`、`*/docs/SELFSCAN_RULES.md`、`*/demo/web-ui/*`
- **教訓**（已入記憶）：新增含安全術語的 docs/demo 後必須重跑自掃驗證

---

## 🔴 P0 緊急（版本一致性與發布）— ✅ 全部完成

~~A-001 同步版本號~~ → v3.5.0 ✅
~~A-002 建 Release~~ → v3.5.0 已建 ✅
~~A-003 CHANGELOG 歸檔~~ → ✅
~~A-004 SKILL.md / TASKS.md 同步~~ → ✅

---

## 🟠 P1 重要（功能完善）

### B-001 安裝前自動攔截掃描 ⚠️
- **現狀**：V-05 降級為手動 URL 掃描；v4 PRD 的 P0 終極形態是「安裝前自動觸發」
- **阻塞**：Pi Agent 目前無 hook API（需研究 extension API / 包裝腳本 / 外部 watcher）
- **待決策**：無 hook API 時接受手動掃描為最終形態，還是投資做擴展？

### B-002 pytest 補齊 V-03 / V-05 ⬜
- **動作**：V-03（Pi 版本檢測）補 pytest；V-05 以「URL 解析 + 決策輸出」替代驗證
- **工時**：半天

### B-003 誤報反饋文檔（F-017）⬜
- **現狀**：README 缺官方誤報反饋流程文檔
- **工時**：1 小時

### B-004 白名單貢獻教程（T-011）⬜
- **動作**：寫 rules/WHITELIST_GUIDE.md（含自掃教訓：pattern 過寬誤傷 fixture 案例 + SELFSCAN_RULES 三區）
- **工時**：1-2 小時

### B-005 置信度分級完善（F-015）⬜
- **工時**：半天

### B-006 LLM 輔助檢測真實測試 ⚠️
- **阻塞**：本環境所有 LLM key 被脫敏，需真實 DeepSeek/OpenAI key
- **動作**：拿真實 key 後跑完整 5 類注入測試

### B-007 免費額度機制審查 ⬜
- **待決策**：是否加 `SKIP_LICENSE` 環境變數讓 CI/開發環境不耗免費額度？（交接單 0818 已激活測試 Pro key 繞過）

---

## 🟡 P2 增強（產品化與推廣）

### C-001 部署 Demo 到 GitHub Pages ⬜ ⚠️
- **⚠️ 阻塞確認**：Wahero 賬號為 GitHub 免費計劃，**不支持 Pages**（gh api 返回 422，已入記憶）
- **替代方案**：本地 demo/index.html + demo/web-ui/index.html 已可直接用；或部署到免費靜態託管（Vercel/Netlify）

### C-002 社區推廣 ⬜
- **待決策**：優先渠道（V2EX / Twitter / Reddit）？
- **動作**：錄製 demo 視頻 → 推廣文案 → 社區介紹帖

### C-003 規則庫持續擴展 ⬜
- **現狀**：181 條
- **方向**：更多 AI Agent 框架、真實 ClawHavoc 樣本模式、MCP 生態新攻擊面

### C-004 GitHub Action 正式化（F-049）⬜
- **工時**：1-2 天

### C-005 Pre-commit Hook 正式化（F-050）⬜
- **工時**：半天

### 🆕 C-006 Web 界面落地（本 session 新增方向）
- **現狀**：設計規格 + HTML 原型已完成（docs/WEB_UI_DESIGN.md + demo/web-ui/index.html）
- **選項 A**：正式前端骨架（React/Vite + 組件庫按 §6 token 落地）
- **選項 B**：後端封裝（按 §8 API 對照：`POST /api/scans` + SSE 進度，複用現有 Python 模組）
- **選項 C**：先伺服器化部署，Web 與 CLI 並存
- **工時**：A/B 各 2-3 天

---

## 🔵 P3 後置（Phase 4 擴展）

| ID | 事項 | 說明 | 條件 |
|----|------|------|------|
| D-001 | 多框架適配（F-045）| OpenClaude / OpenCode / Claude Code | 有社區需求 |
| D-002 | MCP 代理網關（F-046）| 運行時攔截 | 檢測能力成熟後 |
| D-003 | 實時危險命令攔截（F-047）| 防範層 | 需 Pi 運行時支援 |

---

## 🚀 Pi Package 上線步驟（v3.5.0 已就緒，待執行）

1. 倉庫設 **Public**（pi.dev gallery 需要）
2. （可選）生成 demo 截圖 → package.json 加 `pi.image`
3. `npm publish`（git 源已可直接用）
4. 驗證 https://pi.dev/packages 展示

---

## 📋 建議執行順序

### 今天（< 1 小時）
1. **B-003** 誤報反饋文檔
2. **B-004** 白名單貢獻教程（含 SELFSCAN_RULES 三區）

### 本週（2-3 小時）
3. **B-002** pytest 補 V-03
4. **B-005** 置信度分級
5. **C-006** 決定 Web 落地方向（A/B/C）

### 下一個 Sprint（3-5 天）
6. **B-001** 安裝前自動攔截（研究 Pi hook API / 決策）
7. **C-004** GitHub Action marketplace
8. **C-002** 社區推廣
9. **Pi Package 上線**（轉 Public → npm publish）

---

## ❓ 待決策

1. **安裝前攔截**：無 hook API 時，接受「手動 URL 掃描」為最終形態，還是投資做擴展 API？
2. **SKIP_LICENSE**：是否加環境變數讓 CI/開發環境不耗免費額度？
3. **推廣優先渠道**：V2EX / Twitter / Reddit 哪個先做？
4. **Web 界面落地**：先做前端骨架 / 先做後端封裝 / 先伺服器化？
5. **Pages 替代**：Vercel / Netlify 免費靜態託管是否部署 demo？

---

## 🔧 環境事實速查（0818 交接 + 本 session 更新）

- Windows；Python 3.11；一律 `PYTHONIOENCODING=utf-8`
- `python scripts/safety-check` 或 `python -m skill_safety_guard`（pip exe 不在 git-bash PATH）
- **對照掃描目標**：`C:/Users/Administrator/.agents/skills/url-extract`（⚠️ 在 `.agents` 下，非 `~/.pi/agent/skills/`，0818 交接單路徑已過時）
- 本環境無外網（GitHub raw 超時）但 api.github.com 與 api.osv.dev 可達
- 所有 LLM key 被脫敏（3 字符），--pro 只能驗證降級路徑
- gh CLI 可用（已認證）；AskUserQuestion 非 TUI 不可用
- `report/` = 本地掃描報告（gitignore + 白名單），勿提交

---

*生成：2026-08-19 ｜ 倉庫：https://github.com/Wahero/Skill-safety-guard ｜ 工作區乾淨（commit 9d6d85a）*
