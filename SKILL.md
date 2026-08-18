---
name: skill-safety-guard
description: 個人開發者安裝 Skill/MCP 前的安全守護者。掃描 Skill 中的憑證洩露、危險 Shell 命令、敏感路徑訪問，並檢查 Pi Agent 全局安全狀態（CVE 版本 + auth.json 權限）。
allowed-tools:
  - read
  - bash
  - edit
version: 3.4.3
author: Wahero
license: MIT
---

# skill-safety-guard

> **個人開發者安裝 Skill/MCP 前的安全守護者**
> 對話式觸發：`/safety-check` ｜ 開源規則庫 ｜ 寬鬆免費策略

---

## 設置（首次使用前，一次性）

> skill-safety-guard 的引擎是 Python，代碼隨 Skill 一起分發，**無需安裝本項目**。
> 唯一外部依賴是 `pyyaml`（絕大多數環境已預裝）：

```bash
pip install pyyaml
```

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

### 方式 0：作為 Pi Package 安裝（推薦，支持 `pi install` / 更新 / 官網展示）

```bash
pi install git:github.com/Wahero/Skill-safety-guard
# 或 npm 發布後
pi install npm:skill-safety-guard
```

### 方式 1：複製到 Pi Agent skills 目錄

```bash
mkdir -p ~/.pi/agent/skills/skill-safety-guard
cp SKILL.md ~/.pi/agent/skills/skill-safety-guard/
```

### 方式 2：軟連結（開發模式）

```bash
ln -s "$(pwd)" ~/.pi/agent/skills/skill-safety-guard
```

## 工作原理

```
用戶輸入 /safety-check <target>
   ↓
Pi Agent 加載本 SKILL.md（baseDir = 本 Skill 所在目錄）
   ↓
python {baseDir}/scripts/safety-check <target>
   ↓
三層掃描：
  ① Pi Agent 全局（版本 + auth.json 權限）
  ② Skill 內容（憑證 + Shell + 路徑 + Unicode + 注入）
  ③ Skill 依賴（MCP 服務器）
   ↓
Markdown 風險報告（帶風險等級 + 修復建議 + 置信度標記）
```

> `{baseDir}` 是 Pi 注入的 Skill 目錄佔位符——即使 Skill 被安裝到任意位置（pip 全局、~/.pi/agent/git/...、node_modules），
> 都能正確解析到同倉庫內的 `scripts/`、`src/`、`rules/`，因此**同一份代碼無需複製第二遍**。
> 若已 `pip install -e .`，也可直接用 `python -m skill_safety_guard <target>`。

## 安全保證

- ✅ **純靜態分析**——不下載依賴、不執行 Skill 代碼
- ✅ **白名單機制**——已知的誤報模式自動過濾
- ✅ **置信度分級**——🔴 高 / 🟡 中 / 🟢 低，避免噪音淹沒重要問題
- ✅ **規則庫開源**——社區可審計、可貢獻

## 當前狀態

✅ **v3.4.3 功能線**（181 規則 / 9 類檢測 / 自掃 SAFE）

🚀 **Pi Package 化**：根目錄 `package.json` 已配置 `pi` manifest，可通過 `pi install git:...` 安裝並展示於 [pi.dev/packages](https://pi.dev/packages)。

詳細路線圖見 `docs/PRD_v4_聚焦个人开发者版.MD`，完整功能見 `功能說明書.md`。

---

*Skill manifest version: skill-v1*