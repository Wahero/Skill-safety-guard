# skill-safety-guard

> **個人開發者安裝 Skill / MCP 前的安全守護者**

[![Version](https://img.shields.io/badge/version-2.0.0-orange.svg)]()
[![Rules](https://img.shields.io/badge/rules-158-blue.svg)]()
[![Phase](https://img.shields.io/badge/phase-2%20complete-green.svg)]()
[![License](https://img.shields.io/badge/license-MIT-green.svg)]()

---

## 這是做什麼的？

`skill-safety-guard` 是一個**對話式觸發**的安全掃描 Skill，專門保護**個人開發者**在安裝第三方 Skill/MCP 前做安全檢查。

在 Pi Agent 中輸入：

```
/safety-check https://github.com/someone/sketchy-skill
```

即可在**不安裝、不執行**的前提下，掃描這個 Skill 是否包含：
- 🔑 憑證洩露（API Key、Token、私鑰）
- 💀 危險 Shell 命令（`curl | bash`、反向 Shell、磁盤擦除）
- 📁 敏感路徑訪問（`~/.ssh`、`/etc/passwd`、`.env`）
- 🕵️ Unicode 隱寫（Phase 2）

並檢查 Pi Agent 全局：
- ⚠️ Pi 版本是否在已知漏洞範圍（CVE-2026-54326 / 54327）
- 🔒 `auth.json` 文件權限是否過寬

---

## 為什麼需要這個？

**真實案例**（2026 年 1 月）：ClawHavoc 攻擊——**1,184 個惡意 Skill、230 萬美元被盜**。

傳統安全工具**對 Skill 攻擊的檢出率為 0.00%**，因為 Skill 的攻擊載體是「自然語言指令」，不是可執行代碼。

`skill-safety-guard` 專門為這個**新型攻擊載體**設計：直接掃描 SKILL.md 的內容，用正則+規則庫識別可疑模式。

---

## 與競品的差異

| 維度 | NVIDIA SkillSpector | MoltCheck | **skill-safety-guard** |
|------|---------------------|-----------|----------------------|
| 形態 | 企業 CLI 工具 | 付費掃描服務 | **Pi Agent 對話式 Skill** |
| 目標用戶 | 企業安全團隊 | 付費個人用戶 | **個人開發者** |
| 觸發方式 | 手動命令行 | 網頁提交 | **對話中一句話** |
| 規則庫 | 閉源 | 閉源 | **🆕 開源（社區可貢獻）** |
| 免費策略 | 社區版功能受限 | 完全付費 | **每週 5 次免費** |
| 誤報治理 | 用戶配置 | 人工審核 | **🆕 置信度分級 + 反饋渠道** |

> **核心差異化**：避開大廠正面競爭，**只服務個人開發者用 Skill 層的需求**。

---

## 快速開始

### 安裝

```bash
git clone https://github.com/Wahero/Skill-safety-guard.git
cd Skill-safety-guard

# 安裝依賴（可選，建議虛擬環境）
pip install pyyaml

# 安裝為 Skill
mkdir -p ~/.pi/agent/skills/skill-safety-guard
cp SKILL.md ~/.pi/agent/skills/skill-safety-guard/
ln -s "$(pwd)/src" ~/.pi/agent/skills/skill-safety-guard/src

# 或獨立使用（無需 Pi Agent）
python -m skill_safety_guard ./tests/fixtures/malicious/dangerous_shell
```

### 使用

```bash
# 掃描當前目錄
python -m skill_safety_guard

# 掃描指定路徑
python -m skill_safety_guard ./my-skill

# 掃描 Pi 全局
python -m skill_safety_guard --pi

# JSON 輸出（給其他工具用）
python -m skill_safety_guard ./my-skill --output json

# 報告誤報
python -m skill_safety_guard --report-fp shell-curl-bash
```

---

## 檢測能力（v2.0.0 / 158 條規則 / 8 類檢測）

### 🚨 關鍵系統參數修改（最高優先級）

| 類別 | 覆蓋 |
|------|------|
| **AI Agent 配置** | Pi / Claude / Cursor / Codex / Continue / Aider / OpenCode / Cline / Cody |
| **Shell init** | ~/.bashrc, ~/.zshrc, ~/.profile（寫入/重定向/刪除）|
| **包管理器** | npm / Yarn / pip / Cargo / gem / Composer / Maven / Gradle / Bower |
| **持久化** | macOS LaunchAgents/Daemons, Linux autostart, Systemd |
| **編輯器** | VSCode / Vim / Emacs / Neovim / nano |
| **Git** | .gitconfig（含 core.sshCommand / hooksPath / credential.helper）|
| **歷史篡改** | bash/zsh/python_history, history -c |
| **Rootkit** | /etc/ld.so.preload, /etc/hosts, /etc/resolv.conf |
| **數據庫** | .pgpass, .my.cnf, .mongoshrc.js |

### 🔑 憑證洩露

| 檢測項 |
|--------|
| OpenAI / Anthropic / AWS / GitHub / Slack / Stripe / Google / JWT / PEM 私鑰 |

### 💀 危險 Shell 命令

| 檢測項 |
|--------|
| `curl\|bash`、反向 Shell、`rm -rf /`、`dd`、fork bomb、base64 混淆、chmod 777 |

### 💉 提示詞注入

| 檢測項 |
|--------|
| Ignore previous instructions、系統提示提取、越獄、角色劫持、數據外洩（中英文）|

### 🔌 MCP 依賴檢查（--all）

| 檢測項 |
|--------|
| npx -y 未知名包、curl\|bash、工具名暗示憑證/Shell/文件、HTTP 明文、可疑 URL |

### 🕵️ Unicode 隱寫

| 檢測項 |
|--------|
| 零寬字符、Tag 字符區塊、不可見運算符、混合隱寫 |

### 第一層：Pi Agent 全局

| 檢測項 | 說明 |
|--------|------|
| ⚠️ Pi 版本 CVE | 檢查版本是否在 CVE-2026-54326/54327 受影響範圍 |
| 🔒 auth.json 權限 | 檢查權限（Windows ACL / Linux POSIX）|

---

## 路線圖

| 版本 | 狀態 | 內容 |
|------|------|------|
| **v0.1.0** | ✅ 已完成 | Phase 0 通過 + 基礎 MVP |
| **v1.0.0** | ✅ 已完成 | 安裝前掃描殺手場景（URL/粘貼/決策）|
| **v1.1.0** | ✅ 已完成 | Unicode 隱寫 + Demo 包 |
| **v1.2.0** | ✅ 已完成 | 全局 AGENTS.md 檢測 |
| **v1.3.0** | ✅ 已完成 | AI Agent 全覆蓋 + 包管理 + 持久化 |
| **v1.4.0** | ✅ 已完成 | 編輯器 + Git + 歷史 + Rootkit |
| **v1.5.0** | ✅ 已完成 | Freemium + SARIF + 提示詞注入 |
| **v1.6.0** | ✅ 已完成 | MCP 依賴檢查 + --all 完整掃描 |
| **v2.0.0** | 🚀 最新 | Phase 2 全部完成（8 類檢測，158 條規則）|
| v3.0 | 📋 規劃 | LLM 輔助檢測 + MCP 注入深度檢測 |

詳細規劃見 [`docs/PRD_v4_聚焦个人开发者版.MD`](docs/PRD_v4_聚焦个人开发者版.MD)。

---

## 誤報處理（重要）

> **原則**：誤報率 > 檢出率。一個誤報會讓用戶卸載插件，影響遠大於漏報。

### 如果你遇到了誤報

**快速修復**：使用 `--min-confidence` 只看高置信度：

```bash
safety-check ./your-skill --min-confidence high
```

**正式反饋**：使用 `--report-fp` 命令：

```bash
safety-check --report-fp <rule-id>
```

該命令會生成 GitHub issue 鏈接，附帶處理流程和本地白名單模板。

### 置信度分級

| 級別 | 含义 | 建議行為 |
|------|------|---------|
| 🔴 高置信度 | 明確危險模式，推累為真實威脅 | 必須處理 |
| 🟡 中置信度 | 有可疑特徵但可能誤報 | 人工複查 |
| 🟢 低置信度 | 複雜上下文才會觸發 | 可能是 false positive |

### 本地白名單

在 `rules/whitelist.yaml` 中添加：

```yaml
whitelisted_patterns:
  - rule_id: rule-that-misfires
    pattern: "your-specific-text-to-whitelist"
    reason: 為什麼是誤報
```

詳細指南見 [CONTRIBUTING.md](CONTRIBUTING.md)。

### 處理時間承諾

- 🔴 Critical 誤報：48 小時內修復
- 🟡 Medium 誤報：1 週內修復
- 🟢 Low 誤報：下一個版本處理

---

## 測試套件

### 自動測試

```bash
python tests/test_phase0.py
```

預期結果：
```
=== V-02: YAML 解析驗證 ===        [OK]
=== V-04: 正則檢測驗證 ===        [PASS] 100% 檢出率
=== V-06: 誤報基線測試 ===        [PASS] 0% 誤報率
>>> Phase 0 全部通過！
```

### 手動測試

詳見 [TESTING.md](TESTING.md) —— 含 5/15/30 分鐘分層測試。

---

## 社區與貢獻

- 🐛 **報告 Bug**：[GitHub Issues](https://github.com/Wahero/Skill-safety-guard/issues/new?template=bug_report.md)
- 🚫 **報告誤報**：[False Positive Report](https://github.com/Wahero/Skill-safety-guard/issues/new?template=false_positive.md)
- 💡 **貢獻代碼**：詳見 [CONTRIBUTING.md](CONTRIBUTING.md)
- 📜 **行為準則**：[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- 🔔 **Release**：[v0.1.0](https://github.com/Wahero/Skill-safety-guard/releases/tag/v0.1.0)

---

## 貢獻

歡迎貢獻新規則！流程：

1. Fork 本 repo
2. 在 `rules/` 中新增 YAML 規則（含正則 + 樣本）
3. 在 `tests/fixtures/` 新增對應樣本
4. 提交 PR（自動觸發測試）

---

## 許可證

MIT License —— 詳見 [LICENSE](LICENSE) 文件。

---

## 致謝

- [OWASP AST10 (2026)](https://owasp.org) —— 行業威脅標準
- [MoltCheck](https://molt.bot) —— Freemium 商業模式參考
- [mcp-security-audit](https://github.com/) —— MCP 檢測邏輯參考
- ClawHavoc 攻擊報告 (TrendMicro, 2026) —— 真實威脅數據

---

> 由 **個人開發者** 為 **個人開發者** 構建 🛡️