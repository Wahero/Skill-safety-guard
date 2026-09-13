---
name: skill-safety-guard
description: 個人開發者安裝 Skill/MCP 前的安全守護者。掃描 Skill 中的憑證洩露、危險 Shell、原生代碼刪除（Rust/Python/Go/PS）、OWASP 程式碼模式（SQL 注入/SSRF/命令注入）、多框架配置（Windsurf/Copilot/Docker/K8s）、CI/CD 安全（GitHub Actions/Jenkinsfile），檢查 Pi Agent 全局安全狀態（CVE 版本 + auth.json 權限），並檢測本機已安裝的高危服務版本漏洞（langflow/n8n/flowise/open-webui）。
license: MIT
allowed-tools:
  - Read
  - Bash
  - Edit
metadata:
  version: 3.10.0
  author: Wahero
---

# skill-safety-guard

> **個人開發者安裝 Skill/MCP 前的安全守護者**
> 用戶要求「安裝 / 接入某個 Skill 或 MCP 前」先做安全掃描時使用本 Skill ｜ 開源規則庫 ｜ 寬鬆免費策略

## 何時使用本 Skill

- 用戶說「安裝這個 Skill / 掃描這個 Skill / 這個 MCP 安全嗎 / 裝之前幫我檢查」
- 用戶貼出一個 GitHub 倉庫、本地資料夾路徑，要求在接入前評估風險
- 用戶要求檢查本機 Agent 全局安全狀態（版本漏洞 / 憑證權限 / 已裝高危服務）

## 使用方法（通用，適用任何支援 Agent Skills 的環境）

引擎是 Python，代碼隨本 Skill 一起分發，**無需額外安裝本項目**。唯一外部依賴是 `pyyaml`（絕大多數環境已預裝）：

```bash
pip install pyyaml
```

本 Skill 目錄自帶 `scripts/safety-check` 入口與 `src/` 引擎。**以本 SKILL.md 所在目錄為基準**執行（下文以 `<skill-dir>` 表示本 Skill 所在目錄的絕對路徑）：

```bash
python <skill-dir>/scripts/safety-check <目標路徑或 GitHub URL>
```

常用掃描命令：

| 命令 | 說明 |
|------|------|
| `safety-check <path>` | 掃描本地路徑（如 `./my-skill`） |
| `safety-check <url>` | 掃描遠端 Skill，**自動生成 MD 報告到當前目錄** |
| `safety-check <url> --output-file <path>` | 掃描遠端 Skill 並指定報告路徑 |
| `safety-check --pi` | 只掃描 Pi Agent 全局 |
| `safety-check --all` | 完整掃描（Pi 全局 + Skill 內容 + 依賴） |
| `safety-check --chk-myself <path>` | 包含掃描本工具自身；**默認自動跳過自身**，避免自掃誤報 |
| `safety-check --output json` | JSON 輸出 |
| `safety-check --report-fp <id>` | 報告誤報 |
| `safety-check --help` | 幫助 |

掃描完成後，把報告中的風險等級與發現項**逐條向用戶報告**，由用戶決定是否安裝；不要代替用戶做安裝決定。

## 預設行為：GitHub URL → 自動生成 MD 報告

> 當掃描目標是 GitHub URL 時，預設自動把掃描結果寫成一份 Markdown 報告，存放在當前工作目錄，檔名為 `scan-report-<repo>.md`。

```bash
cd /my/working/dir
python <skill-dir>/scripts/safety-check https://github.com/Wahero/url-extract
# → 產生 /my/working/dir/scan-report-url-extract.md
```

**規則：**
- 目標是 GitHub URL（`github.com/...`）→ 自動寫入 `./scan-report-<repo>.md`
- 可用 `--output-file <path>` 覆蓋預設路徑
- 報告內容 = 完整 Markdown 掃描報告（風險等級 + 發現項 + 修復建議）
- 尾段自動生成「📌 掃描結論」（統一三部分格式）：① 文字結論 ② 結論說明 ③ 漏洞數字卡片，誤報不計入風險評分
- 本地路徑掃描不自動寫檔（避免污染目錄），需要時用 `--output-file`
- 報告同時印到終端與寫入檔案，不會遺失即時輸出

## 預設行為：跳過本工具自身

> 默認自動跳過掃描 skill-safety-guard 自身，避免把工具自己的測試樣本 / 文檔中的惡意示例當成風險。僅在指定 `--chk-myself` 時才掃描自身。

- 默認（不加 `--chk-myself`）→ 只要 `skill-safety-guard` 是被掃描目錄的子目錄，就自動整棵跳過
- `--chk-myself` → 包含掃描 skill-safety-guard 自身全部文件
- 掃描目標就在 skill-safety-guard 內部（如掃 `tests/fixtures` 樣本）時，不受跳過影響，正常掃描

## 安裝方式

### 方式 1：複製整個 Skill 資料夾到目標 Agent 的 skills 目錄（通用）

引擎腳本與規則庫必須與 SKILL.md 一起分發，**請複製整個資料夾，不要只複製 SKILL.md**：

```bash
# 以下任一 agent 的 skills 目錄均可（目錄名以目標 Agent 文檔為準）
mkdir -p ~/.claude/skills
cp -r skill-safety-guard ~/.claude/skills/

# Pi Agent 用戶：
cp -r skill-safety-guard ~/.pi/agent/skills/
```

### 方式 2：標準 Skill zip 包

```bash
python scripts/package_skill.py
# → 產生 dist/skill-safety-guard.zip（資料夾結構符合通用 Agent Skills 規範，
#   可直接上傳 claude.ai / 匯入支援 zip 安裝的環境）
```

### 方式 3：軟連結（開發模式）

```bash
ln -s "$(pwd)" ~/.claude/skills/skill-safety-guard
```

### 方式 4：作為 Pi Package 安裝（Pi 專屬可選）

```bash
pi install git:github.com/Wahero/Skill-safety-guard
```

## 工作原理

```
用戶要求掃描某 Skill / MCP
   ↓
Agent 加載本 SKILL.md（本 Skill 目錄 = SKILL.md 所在位置）
   ↓
python <skill-dir>/scripts/safety-check <target>
   ↓
三層掃描：
  ① Agent 全局（Pi 版本 + auth.json 權限；可選）
  ①' 本地高危服務（langflow / n8n / flowise / open-webui 已裝版本 CVE 檢查）
  ② Skill 內容（憑證 + Shell + 路徑 + Unicode + 注入）
  ③ Skill 依賴（MCP 服務器）
   ↓
Markdown 風險報告（帶風險等級 + 修復建議 + 置信度標記）
```

> `scripts/safety-check` 以自身所在位置解析同目錄的 `src/` 與 `src/skill_safety_guard/rules/`，
> 因此 Skill 被安裝到任意位置都能正確運行，**同一份代碼無需複製第二遍**。
> 若已 `pip install -e .`，也可直接用 `python -m skill_safety_guard <target>`。

## 安全保證

- **純靜態分析**——不下載依賴、不執行 Skill 代碼
- **白名單機制**——已知的誤報模式自動過濾
- **置信度分級**——🔴 高 / 🟡 中 / 🟢 低，避免噪音淹沒重要問題
- **規則庫開源**——社區可審計、可貢獻

## 當前狀態

**v3.10.0**（246 規則 / 13 類檢測 / 自掃 SAFE）：OWASP Top 10 + 原生檔案刪除 + 多框架配置 + CI/CD 安全 + Docker/K8s 安全 + Web UI 自動啟動 + 每日漏洞庫更新 + PR 安全審計 CI + **本地高危服務 CVE 檢查**（langflow/n8n/flowise/open-webui，如 CVE-2025-3248 Langflow 未授權 RCE）。

完整用法見 `USAGE.md`，路線圖見 `README.md` / `CHANGELOG.md`。
