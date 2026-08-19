# Changelog

All notable changes to skill-safety-guard will be documented in this file.

## [3.5.0] - 2026-08-19

### Added
**GitHub URL 掃描自動生成 MD 報告（預設行為）**：
- 掃描目標為 GitHub URL 時，自動把完整 Markdown 掃描報告寫入當前工作目錄，檔名 `scan-report-<repo>.md`
- 新增 `--output-file <path>` 參數，可覆蓋預設路徑
- 報告同時印到終端與寫入檔案
- 本地路徑掃描不自動寫檔（需用 `--output-file` 顯式指定）

**誤報自動識別 + 掃描結論區塊**：
- `path-env-file` 規則誤報自動判定：命中 `os.environ.get()` / `os.getenv()` 等環境變數讀取模式時，判定為誤報（憑證不寫入原始碼是安全做法），不計入風險評分
- 報告尾段「📌 掃描結論」升級為統一三部分格式：① 文字結論（可安裝/複查/拒裝） ② 結論說明（風險來源分析 + 誤報說明） ③ 漏洞數字卡片（嚴重度統計表）
- 誤報項在報告中標示 ✅ 誤報判定，統計與風險等級自動排除誤報

**Pi Package 化（單一來源，無需兩份代碼）**：
- 根目錄新增 `package.json`（pi manifest：`"pi": {"skills": ["./SKILL.md"]}` + `pi-package` keyword）
- `SKILL.md` 改用 `{baseDir}/scripts/safety-check` 自引用調用（克隆即可跑）
- 新增 `docs/PI_PACKAGE.md`（發布指南：git/npm/pi.dev gallery/檢查清單/FAQ）
- 新增 `docs/PACKAGE_INTRO.md`（pi.dev gallery 雙語 EN/ZH 項目介紹，痛點驅動文案）
- `scripts/safety-check` 增加 pyyaml 缺失友好提示

### Fixed
- Windows 路徑跳過失效：`"tests/fixtures" in str(Path)` 在反斜杠路徑下永不命中 → 改用 `as_posix()` + 目錄組件匹配（自掃 242 → 113 發現）
- 白名單覆蓋自指內容：demo/、rules/ 規則定義、docs 評估文檔、掃描報告等加入 whitelisted_paths（自掃 113 → 0，SAFE/A 級）
- `critical_paths` context_line 空字串 → 改為填充實際行內容（修復 match_context 白名單對 critical_paths 無效）
- pytest 假通過：測試函數 `return True/False` 改為 `assert`（檢出率 0/8 也顯示 PASS 的 bug）
- 補 `docs/PACKAGE_INTRO.md` 入路徑白名單（ClawHavoc 攻擊手法示例誤報）
- reporter 報告版本號從硬編碼 v1.5.0 改為讀取 `__version__`

### 版本同步（A-001）
- `src/skill_safety_guard/__init__.py` / `package.json` / `pyproject.toml` / `SKILL.md` frontmatter 統一為 v3.5.0

## [3.0.0] - 2026-08-17

### Added (v3.0.0 / Phase 3)
**MCP 注入模式檢測（F-039）**：
- 22 條注入模式規則
- SQL 注入（7 種：拼接/UNION/注釋/引號逃逸/時間盲注/堆疊/報錯）
- 命令注入（7 種：分號/子命令/管道/參數/env讀取/寫後執行/SSRF）
- 路徑遍歷（5 種：../、編碼/絕對路徑/符號鏈接/敏感文件）
- 邏輯注入（3 種：認證繞過/權限覆蓋/競態）

**MCP 傳輸安全（F-040）**：
- 明文 HTTP 檢測
- 內網/雲元數據地址（SSRF）
- 未知傳輸方式

**LLM 輔助提示詞注入檢測（F-037，Pro 限定）**：
- --pro 參數（需 Pro 許可證）
- 支持 DeepSeek API / OpenAI API / Pi auth.json key
- 識別 5 類注入：直接/隱式/多步/數據外泄/持久化
- 結果併入 Markdown（第四層）/ JSON / SARIF

### 規則總數
v1.6.0: 158 → v3.0.0: **181**（+23）

### Tests
- MCP 乾淨 fixture：0 誤報（修復 mcp-tool-file-write 等過寬規則）
- 全部 15 個 fixtures 通過

## [1.6.0] - 2026-08-17

### Added (v1.6.0)
**MCP 依賴檢查（F-029~F-032）**：
- MCP 配置靜態分析（.mcp.json, mcp.json, .cursor/mcp.json 等）
- 服務器枚舉：名稱/命令/參數/傳輸方式
- 工具枚舉：聲明工具 + 從命令推斷
- 工具風險分類：SHELL/FILE/DATABASE/NETWORK/CREDENTIAL/SAFE
- 16 條 MCP 安全規則（npx -y、curl|bash、工具名暗示、憑證資源、HTTP 明文等）
- MCP 結果併入報告（Markdown 第三層 + JSON + SARIF）

**--all 完整掃描（F-025）**：
- Pi 全局 + Skill 內容 + MCP 依賴一次完成
- MCP findings 計入綜合風險等級

**掃描進度顯示（F-026）**：
- "正在掃描 Skill 內容..." → "正在檢查 Pi Agent 全局..." → "正在檢查 MCP 依賴..."

### Changed
- 報告 footer 版本號更新為 v1.5.0

### Tests
- 新增惡意樣本：tests/fixtures/malicious/mcp_servers/.mcp.json
- 新增乾淨樣本：tests/fixtures/clean/mcp_safe/.mcp.json
- 全部通過，無誤報

## [1.4.0] - 2026-08-17

### Added (v1.4.0)
**編輯器配置檢測（6 條）**：
- VSCode：~/.config/Code/User/settings.json, keybindings.json
- Vim：~/.vimrc, ~/.vim/{plugin,autoload,ftplugin}/
- Emacs：~/.emacs.d/init.el, ~/.emacs
- Neovim：~/.config/nvim/init.vim, init.lua
- nano：~/.nanorc

**Git 配置檢測（4 條）**：
- ~/.gitconfig
- ~/.git-credentials
- core.sshCommand/hooksPath/gitProxy/credential.helper 賦值
- include.path 配置注入

**歷史記錄篡改檢測（6 條）**：
- ~/.bash_history, ~/.zsh_history, ~/.python_history
- ~/.viminfo, ~/.wget-hsts
- Shell 命令：`history -c && rm`、`unset HISTFILE`、`echo > ~/.bash_history`

**數據庫客戶端配置（4 條）**：
- ~/.pgpass (PostgreSQL 明文密碼)
- ~/.my.cnf (MySQL 客戶端配置)
- ~/.rediscli_history
- ~/.mongoshrc.js（MongoDB Shell 啟動執行 JavaScript）

**Rootkit 向量（8 條）**：
- /etc/ld.so.preload（最高危險 - 所有進程預加載）
- /etc/ld.so.conf, /etc/ld.so.conf.d/
- /etc/hosts（DNS 劫持）
- /etc/resolv.conf（DNS 服務器劫持）
- /etc/environment（系統環境變量）
- /etc/profile.d/（全用戶 shell 初始化）

**規則總數**：v1.3.0 39 → v1.4.0 **67** (+28)

### Tests
- 新增惡意樣本：tests/fixtures/malicious/editor_git_rootkit/SKILL.md
- 9 個攻擊類別、30+ 攻擊向量
- 掃描結果：**43 findings**, 32 critical_paths

## [1.3.0] - 2026-08-17

### Added (v1.3.0)
**AI Agent 配置全面覆蓋**：
- Cursor AI：~/.cursor/rules/, ~/.cursor/.cursorrules, ~/.cursor/mcp.json, ~/.cursor/extensions/
- Aider：~/.aider.conf.yml, ~/.aider.model.metadata.json
- OpenCode：~/.config/opencode/opencode.json
- Cline（VSCode 擴展）：saoudrizwan.cline-dev
- Cody（Sourcegraph）：sourcegraph.cody-ai

**包管理器配置檢測**：
- npm：.npmrc, npm config set
- Yarn：.yarnrc, .yarnrc.yml
- pip：pip.conf, pip config set
- Cargo（Rust）：.cargo/config.toml, .cargo/credentials
- Ruby gem：.gemrc
- PHP Composer：.composer/config.json
- Maven：.m2/settings.xml
- Gradle：.gradle/init.gradle, .gradle/gradle.properties
- Bower：.bowerrc

**持久化機制檢測**：
- macOS LaunchAgents：~/Library/LaunchAgents/*.plist
- macOS LaunchDaemons：/Library/LaunchDaemons/*.plist
- Linux autostart：~/.config/autostart/*.desktop
- Systemd 用戶服務：~/.config/systemd/user/*.service

**變量名啟發擴展**：
- 增加 20+ 變量名模式（npmrcPath, awsCreds, sshKeys, etc.）

**新規則數**：v1.2.0 16 → v1.3.0 39 (+23)

### Changed
- paths 檢測器默認 case-insensitive（Windows 路徑兼容）

### Tests
- 新增惡意樣本：tests/fixtures/malicious/package_persistence/SKILL.md
- 12+ 個攻擊向量全部檢測

## [2.0.0] - 2026-08-17（歷史歸檔）

### Added (v2 系列：Unicode 隱寫 + 工具完善)
- Unicode 隱寫檢測（F-022）：14 條規則
  - 零寬字符檢測（U+200B/C/D、U+FEFF）
  - Tag 字符區塊（U+E0000-U+E007F）檢測
  - 不可見運算符檢測（U+2060-U+2064）
  - 混合隱寫檢測
- GitHub Issue 模板：feature_request.md、question.md
- Pull Request 模板
- 腳本：scripts/generate_unicode_rules.py
- 腳本：scripts/fix_auth_permissions.py

### Fixed
- Windows auth.json 權限檢測（os.stat 不反映 ACL，改用 icacls）
- YAML 對 Unicode 高位字符的處理（ `\u` 只支援 4 位 hex，U+E0000 需要字面字符）
- Unicode 檢測需要單文件掃描支援

## [1.0.0] - 2026-08-17

### Added
- **杀手場景**（v4 P0 最高優先級）
  - F-007 URL/註冊名解析：支援 4 種 GitHub URL
  - F-008 預覽式掃描：sub_path 只取子目錄
  - F-009 粘貼式掃描：支援 'paste' 從 stdin 讀取
  - F-010 三級決策：SAFE / CAUTION / DANGER
- **誤報治理**（F-015）
  - `--min-confidence` 過濾（high/medium/low）
  - `--confidence-detail` 顯示分級原因
  - `--report-fp` 改進含本地白名單模板
- **跨平台 auth.json 檢測**
  - Linux/Mac POSIX 權限
  - Windows ACL 檢測（修本機 0o666 誤報）

## [0.1.0] - 2026-08-17

### Phase 0 完成 ✅

#### Added
- **核心架構**
  - SKILL.md 完整 manifest
  - Python 包結構（`src/skill_safety_guard/`）
  - 獨立 CLI 包裝（`scripts/safety-check`）
  - pyproject.toml 配置

- **檢測器**（P0 必含）
  - 憑證洩露檢測器（10 條規則）
  - 危險 Shell 命令檢測器（12 條規則）
  - 敏感路徑訪問檢測器（9 條規則）

- **Pi Agent 全局檢查**
  - Pi 版本 CVE 檢測（CVE-2026-54326/54327）
  - auth.json 文件權限檢查

- **命令支持**
  - `safety-check` 默認掃描當前目錄
  - `--pi` 只掃描 Pi 全局
  - `--output json` 結構化輸出
  - `--report-fp <rule-id>` 報告誤報
  - `--help` 幫助信息

- **白名單機制（F-014）**
  - 已知誤報模式過濾
  - 置信度分級降級
  - 路徑白名單

- **測試**
  - 3 個惡意樣本（credential_leak, dangerous_shell, sensitive_path）
  - 5 個乾淨樣本（hello-world, data-formatter, git-helper, code-snippet, markdown-table）
  - 自動化測試套件（V-02, V-04, V-06）

- **文檔**
  - README.md（中英對照）
  - PRD v3.0 與 v4.0
  - 討論記錄
  - Phase 0 驗證報告
  - Issue 模板（誤報 + Bug）

### Verified
- ✅ V-02: YAML 解析 - 100% 正確
- ✅ V-03: Pi 版本檢測 - 提取 `0.84.2` 準確
- ✅ V-04: 正則檢測 - **100% 檢出率**（3/3 惡意樣本）
- ✅ V-06: 誤報基線 - **0% 誤報率**（0/5 乾淨樣本）
- ⚠️ V-05: 安裝前攔截 - 降級為手動 URL 掃描（Pi Agent 無 hook API）

### Known Issues
- Pi 0.84.2 在當前環境檢出 CVE-2026-54327（需升級到 0.85.0+）
- auth.json 權限 0o666 不安全（建議改為 600）

## [Unreleased]

### 歷史計劃（已全部完成，僅存檔）
- F-007~F-010: 殺手場景「安裝前 URL 掃描」 → ✅ 已實現（手動 URL 掃描）
- F-014~F-017: 白名單擴展 + 置信度分級完善 → ✅ 已實現
- F-018~F-021: 報告優化 + 端到端測試 → ✅ 已實現

詳見 `docs/PRD_v4_聚焦个人开发者版.MD`。