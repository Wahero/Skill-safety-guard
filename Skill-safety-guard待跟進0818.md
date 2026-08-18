# Skill-safety-guard 待跟進事項（0818）

> **更新**：2026-08-18 ｜ **當前功能線**：v3.4.3（181 規則 / 9 類 / SAFE 自掃）
> **說明**：✓ = 已完成；⬜ = 待跟進；⚠️ = 有阻塞/需決策

---

## 📊 總覽

| 優先級 | 數量 | 說明 |
|--------|------|------|
| 🔴 P0（緊急） | 4 | 版本一致性、Release、文檔同步 |
| 🟠 P1（重要） | 7 | 殺手場景完善、測試補齊、誤報治理 |
| 🟡 P2（增強） | 5 | 產品化、推廣、進階功能 |
| 🔵 P3（後置） | 4 | Phase 4 擴展 |

---

## 🔴 P0 緊急（版本一致性與發布）

### A-001 同步版本號 ⬜
- **現狀**：`src/skill_safety_guard/__init__.py` 內 `__version__ = "0.1.0"`，但實際功能已到 v3.4.3（README badge 已標 3.4.3）
- **動作**：版本號統一為 v3.5.0（含未發布功能）或 v3.4.3
- **工時**：10 分鐘

### A-002 創建 GitHub Release v3.5.0 ⬜
- **現狀**：只有 `v0.1.0` 一個 tag；PROGRESS.md 聲稱 6 個 Release 但 GitHub 上未建
- **動作**：整理 CHANGELOG → 打 tag → 建 Release（含 release notes、二進位、截圖）
- **前置**：A-001
- **工時**：30 分鐘

### A-003 CHANGELOG [Unreleased] 歸檔 ⬜
- **現狀**：GitHub URL 自動報告、誤報自動識別、掃描結論三部分已在 main（commit 1b73c38/407c382/714eae8）但仍在 [Unreleased]
- **動作**：歸入正式版本節
- **工時**：10 分鐘

### A-004 SKILL.md / TASKS.md 過時 ⬜
- **現狀**：SKILL.md 仍標「v0.1.0 (Phase 0 通過，MVP 開發中)」；TASKS.md 仍以 v0.1.0 視角（Phase 1 60%）
- **動作**：SKILL.md 更新版本與能力；TASKS.md 全面重寫或標註已過時並指向功能說明書
- **工時**：1 小時

---

## 🟠 P1 重要（功能完善）

### B-001 安裝前自動攔截掃描 ⚠️
- **現狀**：V-05 降級為手動 URL 掃描（用戶要記得運行）；v4 PRD 的 P0 終極形態是「安裝前自動觸發」
- **阻塞**：Pi Agent 目前無 hook API（需研究：extension API / 包裝腳本 / 外部 watcher）
- **工時**：3 天

### B-002 pytest 補齊 V-03 / V-05 ⬜
- **現狀**：pytest 只有 3 個函數（V-02/V-04/V-06）；V-03（Pi 版本檢測）、V-05 未入 pytest
- **動作**：V-03 補 pytest；V-05 以「URL 解析 + 決策輸出」替代驗證
- **工時**：半天

### B-003 誤報反饋文檔（F-017）⬜
- **現狀**：TESTING.md 有提及，README 缺官方誤報反饋流程文檔
- **工時**：1 小時

### B-004 白名單貢獻教程（T-011）⬜
- **現狀**：whitelist.yaml 已有結構（patterns/paths/match_context/demotions），缺教學
- **動作**：寫 rules/WHITELIST_GUIDE.md（含自掃教訓：pattern 過寬誤傷 fixture 的案例）
- **工時**：1-2 小時

### B-005 置信度分級完善（F-015）⬜
- **現狀**：三檔固定，缺規則級配置與「低置信度摺疊顯示」策略
- **工時**：半天

### B-006 LLM 輔助檢測真實測試 ⚠️
- **現狀**：本環境所有 LLM key 被脫敏，--pro 只能驗證降級路徑
- **阻塞**：需要真實 DeepSeek/OpenAI key
- **動作**：拿真實 key 後跑完整 5 類注入測試（直接/隱式/多步/數據外泄/持久化）

### B-007 免費額度機制審查 ⬜
- **現狀**：本機免費額度已用盡（本 session 激活了測試 Pro key 繞過）
- **動作**：確認週一重置邏輯；考慮測試環境豁免（如 SKIP_LICENSE 環境變數）
- **工時**：半天

---

## 🟡 P2 增強（產品化與推廣）

### C-001 部署 Demo 到 GitHub Pages ⬜
- **現狀**：demo/ 已有 index.html + outputs（52 個示例發現）
- **工時**：半天

### C-002 社區推廣 ⬜
- **現狀**：未開始
- **動作**：T-004 錄製 demo 視頻 → T-005 推廣文案（Twitter/Reddit/V2EX）→ T-006 社區介紹帖
- **工時**：1-2 天

### C-003 規則庫持續擴展 ⬜
- **現狀**：181 條
- **方向**：更多 AI Agent 框架、真實 ClawHavoc 樣本模式、MCP 生態新攻擊面
- **工時**：持續

### C-004 GitHub Action 正式化（F-049）⬜
- **現狀**：CI workflow 已有；缺「一鍵掃描任意 repo」的 marketplace Action
- **工時**：1-2 天

### C-005 Pre-commit Hook 正式化（F-050）⬜
- **現狀**：.pre-commit-config.yaml 範例已寫，未驗證正式可用
- **工時**：半天

---

## 🔵 P3 後置（Phase 4 擴展）

| ID | 事項 | 說明 | 條件 |
|----|------|------|------|
| D-001 | 多框架適配（F-045） | OpenClaude / OpenCode / Claude Code | 有社區需求 |
| D-002 | MCP 代理網關（F-046） | 運行時攔截 | 檢測能力成熟後 |
| D-003 | 實時危險命令攔截（F-047） | 防範層 | 需 Pi 運行時支援 |
| D-004 | 企業合規報告 | ~~F-048~~ 已取消（不在定位） | — |

---

## ✅ 本 session 已完成（2026-08-18）

| commit | 內容 |
|--------|------|
| 556de3a | Windows 路徑跳過失效修復（自掃 242 → 113） |
| ce9a782 | 白名單覆蓋自指內容（自掃 113 → 0，SAFE/A 級） |
| 714eae8 | 掃描結論統一三部分格式 |
| 407c382 | 誤報自動識別（os.environ 模式） |
| 1b73c38 | GitHub URL 掃描自動生成 MD 報告 |

## 🎁 本 session 新增：Pi Package 化（已完成 + 已驗證）

**結論：不需要維護兩份代碼。** Pi Package 是同一倉庫的薄聲明層——根目錄加 `package.json`（`pi` manifest 指向 `./SKILL.md`），引擎/規則原地不動。

| 文件 | 內容 |
|------|------|
| `package.json`（新增） | pi manifest：`"skills": ["./SKILL.md"]` + `pi-package` keyword |
| `SKILL.md`（更新） | `{baseDir}/scripts/safety-check` 自引用調用 + Setup（pyyaml）+ 版本 3.4.3 |
| `docs/PI_PACKAGE.md`（新增） | 發布指南（git/npm/gallery/檢查清單） |
| `scripts/safety-check`（更新） | pyyaml 缺失時友好提示 |
| `rules/whitelist.yaml`（更新） | 新增 `*/report/*`、`*/scan-report-*.md`、源碼/說明書自指模式 |
| `.gitignore`（更新） | 提交先前遺留的 `report/` 忽略規則 |
| `critical_paths.py`（更新） | context_line 從空字串改為實際行內容（修復 match_context 白名單對 critical_paths 無效） |

**驗證**：
- `DefaultResourceLoader` 實測解析：`skill-safety-guard | baseDir=<package root> | SKILL.md` ✓
- 本地自掃恢復 SAFE/A/0（report/ 與新文檔的自指模式已覆蓋）
- pytest 3 passed，檢出率 8/8

**待辦（發布前）**：npm publish（可選，git 源已可用）→ pi.dev gallery 展示 → 加 image/video 預覽

**驗證結果**：
- 自掃（遠端/本地）：SAFE / A 級 / 0 發現
- 檢出率：8/8 = 100%（fixtures）
- 對照掃描 url-extract skill：CAUTION / 3 發現（未失明）
- pytest：3 passed

---

## 📋 建議執行順序

### 今天（< 1 小時）
1. **A-001** 同步版本號
2. **A-003** CHANGELOG 歸檔
3. **A-002** 建 Release v3.5.0

### 本週（2-3 小時）
4. **A-004** SKILL.md + TASKS.md 更新
5. **B-003** / **B-004** 誤報反饋文檔 + 白名單教程
6. **B-002** pytest 補 V-03

### 下一個 Sprint（3-5 天）
7. **B-001** 安裝前自動攔截（研究 Pi hook API）
8. **C-001** GitHub Pages demo
9. **C-002** 社區推廣

---

## ❓ 待決策

1. **版本號**：下一個正式版叫 v3.5.0（含未發布功能）還是直接 v4.0？
2. **安裝前攔截**：若 Pi Agent 無 hook API，是否接受「手動 URL 掃描」為最終形態，還是投資做擴展 API？
3. **測試環境豁免**：是否加 `SKIP_LICENSE` 環境變數讓 CI/開發環境不耗免費額度？
4. **推廣優先渠道**：V2EX / Twitter / Reddit 哪個先做？

---

*生成：2026-08-18 ｜ 倉庫：https://github.com/Wahero/Skill-safety-guard*
