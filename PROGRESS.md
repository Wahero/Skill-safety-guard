# skill-safety-guard 項目進度記錄

> **已歸檔**：此文檔已過時，僅保留歷史記錄。
> 最新狀態請見：[`MEMORY.md`](MEMORY.md) / [`Skill-safety-guard待跟進事項0826.md`](Skill-safety-guard待跟進事項0826.md)
>
> 歸檔日期：2026-08-26

---

## 歷史記錄（截至 2026-08-17）

| 版本 | 日期 | 內容 |
|------|------|------|
| v0.1.0 | 08-17 | Phase 0 全通過 + 基礎 MVP（45 規則）|
| v1.0.0 | 08-17 | 殺手場景（URL/粘貼/決策）|
| v1.1.0 | 08-17 | Unicode 隱寫 + Demo 包 |
| v1.2.0 | 08-17 | 全局 AGENTS.md 檢測（critical_paths 16 條）|
| v1.3.0 | 08-17 | AI Agent 全覆蓋 + 包管理器 + 持久化（39 條）|
| v1.4.0 | 08-17 | 編輯器 + Git + 歷史 + 數據庫 + Rootkit（67 條）|
| v1.5.0 | 08-17 | Freemium + SARIF + 提示詞注入 + 擴展審計（142 條）|
| v1.6.0 | 08-17 | MCP 依賴檢查 + --all 完整掃描 + 進度顯示（158 條）|
| v2.0.0 | 08-17 | Phase 2 全部完成 + 發布推廣 |
| v3.0.0 | 08-17 | MCP 注入檢測 + 傳輸安全 + LLM 輔助檢測（181 條）|

## 當前能力（v3.7.0，2026-08-26 更新）

- 187 條規則，10 個檢測類別
- 殺手場景：GitHub URL / 粘貼 / 本地掃描
- Freemium：免費 5 次/週，Pro 無限
- 輸出：Markdown / JSON / SARIF
- CI：3 OS × 3 Python 版本 + pytest（44 用例）
- Web 後端：CORS 白名單 / rate limit / 路徑遍歷防禦
- Phase 0 + Phase 1 已完成，Phase 2/3 進行中
