---
name: skill-safety-guard
description: 個人開發者安裝 Skill/MCP 前的安全守護者。掃描 Skill 中的憑證洩露、危險 Shell 命令、敏感路徑訪問，並檢查 Pi Agent 全局安全狀態（CVE 版本 + auth.json 權限）。
allowed-tools:
  - read
  - bash
  - edit
version: 0.1.0
author: Wahero
license: MIT
---

# skill-safety-guard

> **個人開發者安裝 Skill/MCP 前的安全守護者**
> 對話式觸發：`/safety-check` ｜ 開源規則庫 ｜ 寬鬆免費策略

---

## 觸發命令

| 命令 | 說明 | 範例 |
|------|------|------|
| `/safety-check` | 掃描當前目錄 | `/safety-check` |
| `/safety-check <path>` | 掃描指定路徑 | `/safety-check ./my-skill` |
| `/safety-check <url>` | 🆕 掃描遠端 Skill（殺手功能），**自動生成 MD 報告到當前目錄** | `/safety-check https://github.com/x/y` |
| `/safety-check <url> --output-file <path>` | 掃描遠端 Skill 並指定報告路徑 | `/safety-check <url> --output-file ./report.md` |
| `/safety-check --pi` | 只掃描 Pi Agent 全局 | `/safety-check --pi` |
| `/safety-check --all` | 完整掃描（Pi + Skill + 依賴） | `/safety-check --all` |
| `/safety-check --output json` | JSON 輸出 | `/safety-check --output json` |
| `/safety-check --report-fp <id>` | 🆕 報告誤報 | `/safety-check --report-fp shell-curl-bash` |
| `/safety-check --help` | 幫助 | `/safety-check --help` |

## 預設行為：GitHub URL → 自動生成 MD 報告

> 🎯 **當掃描目標是 GitHub URL 時，預設自動把掃描結果寫成一份 Markdown 報告，存放在當前工作目錄**，檔名為 `scan-report-<repo>.md`。

```bash
# 範例：掃描遠端 Skill，報告自動存到當前目錄
cd /my/working/dir
safety-check https://github.com/Wahero/url-extract
# → 產生 /my/working/dir/scan-report-url-extract.md
```

**規則：**
- ✅ 目標是 GitHub URL（`github.com/...`）→ 自動寫入 `./scan-report-<repo>.md`
- ✅ 可用 `--output-file <path>` 覆蓋預設路徑
- ✅ 報告內容 = 完整 Markdown 掃描報告（風險等級 + 發現項 + 修復建議）
- ✅ **尾段自動生成「📌 掃描結論」**（統一三部分格式）：① 文字結論 ② 結論說明 ③ 漏洞數字卡片，誤報不計入風險評分
- ℹ️ 本地路徑掃描不自動寫檔（避免污染目錄），需要時用 `--output-file`
- ℹ️ 報告同時印到終端與寫入檔案，不會遺失即時輸出

## 安裝方式

```bash
# 方式 1：複製到 Pi Agent skills 目錄
mkdir -p ~/.pi/agent/skills/skill-safety-guard
cp SKILL.md ~/.pi/agent/skills/skill-safety-guard/

# 方式 2：軟連結（開發模式）
ln -s "$(pwd)" ~/.pi/agent/skills/skill-safety-guard
```

## 工作原理

```
用戶輸入 /safety-check <target>
   ↓
Pi Agent 加載本 SKILL.md，調用 bash 執行
   ↓
python -m skill_safety_guard <target>
   ↓
三層掃描：
  ① Pi Agent 全局（版本 + auth.json 權限）
  ② Skill 內容（憑證 + Shell + 路徑 + Unicode）
  ③ Skill 依賴（MCP 服務器）
   ↓
Markdown 風險報告（帶風險等級 + 修復建議 + 置信度標記）
```

## 安全保證

- ✅ **純靜態分析**——不下載依賴、不執行 Skill 代碼
- ✅ **白名單機制**——已知的誤報模式自動過濾
- ✅ **置信度分級**——🔴 高 / 🟡 中 / 🟢 低，避免噪音淹沒重要問題
- ✅ **規則庫開源**——社區可審計、可貢獻

## 當前狀態

🚧 **v0.1.0 (Phase 0 通過，MVP 開發中)**

詳細路線圖見 `docs/PRD_v4_聚焦个人开发者版.MD`。

---

*Skill manifest version: skill-v1*