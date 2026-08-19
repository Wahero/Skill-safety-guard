# skill-safety-guard 任務清單

> **當前狀態**：v3.5.0（功能線）｜ 181 規則 / 9 類檢測 / 自掃 SAFE（A 級）
> **更新時間**：2026-08-19
> **過時說明**：本文檔以 v3.5.0 視角重寫，取代 v0.1.0 舊版。完整功能規格見 [`功能說明書.md`](功能說明書.md)；待辦清單以 [`Skill-safety-guard待跟進0818.md`](Skill-safety-guard待跟進0818.md) 為準。

---

## 📊 整體進度（v3.5.0）

| 階段 | 狀態 | 完成度 | 說明 |
|------|------|--------|------|
| Phase 0 前置驗證 | ✅ 已完成 | 100% | CLI 骨架 + 目標定位器 |
| Phase 1 MVP | ✅ 已完成 | 100% | 殺手場景（URL/粘貼/決策）+ 三類基礎檢測 |
| Phase 2 增強 | ✅ 已完成 | 100% | Unicode 隱寫 + 提示詞注入 + MCP 依賴 |
| Phase 3 商業化 | ✅ 已完成 | 100% | Freemium license + SARIF + 漏洞情報 |
| Phase 4 擴展 | 🔵 後置 | 0% | 多框架 / MCP 網關 / 實時攔截（見待跟進 D 組）|

---

## ✅ 已交付能力（v3.5.0）

### 三層檢測架構
1. **Pi Agent 全局**：版本 CVE 檢測（OSV.dev 權威源）+ auth.json ACL（icacls）
2. **Skill 內容四類規則**：憑證洩露 / 危險 Shell / 敏感路徑 / Unicode 隱寫（181 條規則、9 類檢測器）
3. **Critical Paths**：67 條關鍵路徑（~/.pi/agent/*、~/.claude/*、rootkit 向量、包管理配置）

### 殺手場景
- ✅ GitHub URL 掃描 → 自動生成 `scan-report-<repo>.md`
- ✅ 本地路徑掃描 / 粘貼式掃描
- ✅ 三級安裝建議（SAFE/CAUTION/DANGER）+ 統一掃描結論三部分

### 商業化（Phase 3）
- ✅ Freemium license（每日免費 3-5 次 / Pro $4.99/月）
- ✅ SARIF 輸出 / 已安裝擴展靜態審計 / LLM 輔助檢測（--pro）
- ✅ 每日漏洞情報（OSV.dev → AVID → GitHub 多源回退鏈）

### Pi Package
- ✅ 單一來源（根目錄 package.json + SKILL.md 自引用）→ 克隆即用
- ✅ pi.dev gallery 發布指南（docs/PI_PACKAGE.md）

---

## 🟠 待跟進（詳見待跟進清單 0818）

| 優先級 | 事項 | ID |
|--------|------|----|
| 🔴 P0 | ~~版本統一 / CHANGELOG 歸檔 / Release~~ | A-001~A-003 ✅ |
| 🔴 P0 | SKILL.md / TASKS.md 同步 | A-004 ✅ |
| 🟠 P1 | 安裝前自動攔截（研究 Pi hook API）| B-001 ⚠️ 需決策 |
| 🟠 P1 | pytest 補 V-03 / V-05 | B-002 |
| 🟠 P1 | 誤報反饋文檔 / 白名單教程 | B-003 / B-004 |
| 🟠 P1 | 置信度分級完善 / LLM 真實測試 / 額度機制 | B-005~B-007 |
| 🟡 P2 | GitHub Pages demo / 社區推廣 / 規則擴展 | C-001~C-003 |
| 🟡 P2 | GitHub Action 正式化 / Pre-commit | C-004 / C-005 |
| 🔵 P3 | 多框架適配 / MCP 網關 / 實時攔截 | D-001~D-003 |

---

## 📋 快速驗證

```bash
cd D:/ai/PiAgent/Skill-safety-guard
PYTHONIOENCODING=utf-8 python -m pytest tests/ -q                    # 3 passed
PYTHONIOENCODING=utf-8 python scripts/safety-check . --no-pi          # SAFE / A / 0 發現
PYTHONIOENCODING=utf-8 python -m pytest tests/test_phase0.py::test_v04_detection_rate -s -q | grep 檢出率   # 8/8
```

---

## 📌 歷史版本里程碑

| 版本 | 內容 |
|------|------|
| v0.1.0 → v1.6.0 | Phase 0/1/2（殺手場景、Unicode 隱寫、MCP 依賴）|
| v2.0.0 | Phase 2 全部完成 |
| v3.0.0 → v3.4.x | Phase 3（LLM 輔助、MCP 注入、漏洞情報、國內源）|
| **v3.5.0** | URL 自動報告 + 誤報識別 + Pi Package 化 + 版本統一 |

*完整變更見 CHANGELOG.md*
