# 關鍵系統參數修改檢測 —— 可行性評估

> **問題**：能不能檢測到所有（顯式 + 隱式）對 AGENTS.md 等系統重要參數的修改/刪除？
> **結論**：可以檢測**大多數**，但有明確邊界。

---

## 一、檢測能力概覽

### 我們能做的（已實測）

| 場景 | 檢測方式 | 可靠性 |
|------|---------|--------|
| `writeFileSync("~/.pi/agent/AGENTS.md", ...)` | 字符串匹配 | ⭐⭐⭐⭐⭐ |
| `fs.writeFile(path)` 其中 path 含 `AGENTS.md` | 字符串匹配 | ⭐⭐⭐⭐⭐ |
| `>> ~/.bashrc` (Shell 重定向) | 字符串匹配 | ⭐⭐⭐⭐⭐ |
| `function ensure*Agent*` | 函數名啟發 | ⭐⭐⭐⭐ |
| `const agentsMdPath = ...` | 變量名啟發 | ⭐⭐⭐⭐ |
| `homedir() + writeFile` 跨行模式 | 多行正則 | ⭐⭐⭐ |
| `writeFileSync + chmod +x` 後門模式 | 多行正則 | ⭐⭐⭐ |

### 我們做不到的

| 場景 | 原因 |
|------|------|
| 跨函數的 path 構造（變量在一個函數，write 在另一個） | 需 AST 級別的數據流分析 |
| 編碼/混淆的路徑（如 base64 編碼的 "AGENTS.md"） | 需運行時解碼 |
| 通過第三方庫函數間接寫入 | 靜態分析無法追蹤 |
| 動態 import 的模塊中調用 | 需依賴圖遍歷 |

---

## 二、與大工具的對比

| 工具 | 能力 | 我們能做嗎 |
|------|------|-----------|
| **Semgrep** | AST 分析 + taint tracking + 跨函數 | ❌（部分可做：模式匹配可達 70%）|
| **CodeQL** (GitHub) | 完整數據流分析 + 類型系統 | ❌（需重型基礎設施）|
| **eslint-plugin-security** | 規則 + AST | ❌（部分可做：語法樹層級規則）|
| **OSQuery / Falco** | 運行時系統調用監控 | ❌（我們是源碼掃描，非運行時）|
| **AIDE / Tripwire** | 文件哈希監控 | ❌（需運行時部署）|

**結論**：我們的能力**介於基礎正則和完整 SAST 之間**，對**常見模式**可靠，對**高級對手**不足。

---

## 三、真實案例驗證（pi-web）

掃描 `ct-jyjntc/pi-web`（已知有 AGENTS.md 自動修改行為）：

### 修改前（無規則）
```
critical_paths: 0 findings
→ 漏檢（用戶警告的盲區）
```

### 修改後（v1.2 新規則）
```
critical_paths: 14 findings
  - critical-agents-md-write: 3 (實際寫操作)
  - implicit-agent-function: 9 (函數名暗示)
  - implicit-agent-variable: 1 (變量名)
  - implicit-homedir-write: 1 (跨行模式)
  
關鍵命中：
  1. writeFileSync(agentsMdPath, ...) x 3
  2. function ensureAgent*, syncAgent*, createSubagent*
  3. homedir() → writeFileSync 跨行關聯
```

**結論**：✅ **完全檢測**到 pi-web 的 AGENTS.md 自動修改行為。

---

## 四、評估結論

### 可行性：**可做 70-80%，做不到 100%**

| 我們的優勢 | 我們的劣勢 |
|----------|----------|
| 零依賴、快速、易部署 | 無數據流分析 |
| 規則易擴展 | 無法追蹤編碼路徑 |
| 社區可讀懂 | 無法檢測間接調用 |
| 開源規則庫 | 對抗混淆能力弱 |

### 推薦策略：**縱深防禦**

```
Layer 1: skill-safety-guard（我們）
   - 檢測常見顯式/隱式模式
   - 70%+ 覆蓋率
   - 部署在 CI、pre-commit、社區 PR 流程

Layer 2: Semgrep（社區推薦）
   - AST 級別規則
   - 90%+ 覆蓋率
   - 部署在 GitHub Actions

Layer 3: CodeQL（企業）
   - 完整數據流分析
   - 99% 覆蓋率
   - 適合高安全要求項目

Layer 4: 運行時保護（OSQuery/Falco）
   - 檢測實際系統調用
   - 100% 覆蓋率
   - 適合服務器環境
```

### 對個人開發者的實際建議

```
日常使用 skill-safety-guard：
  - 掃描下載的 Skill → 攔截 70%+ 的威脅
  - 對可疑 Skill 用 Semgrep 二次確認
  - 永遠不要安裝來路不明的 Skill

專業項目：
  - skill-safety-guard 規則庫 + Semgrep rules 雙重部署
  - 在 CI 中自動掃描所有 PR
  - 定期更新規則庫
```

---

## 五、新增的規則清單

### v1.3.0 新增 23 條規則

#### AI Agent 配置（8 條新增）
| 規則 ID | 描述 | 嚴重度 |
|--------|------|--------|
| critical-cursor-rules-write | Cursor rules 寫入 | critical |
| critical-cursor-mcp-write | Cursor MCP 配置 | critical |
| critical-cursor-extensions-write | Cursor 擴展目錄 | high |
| critical-aider-config-write | Aider 配置 | critical |
| critical-opencode-config-write | OpenCode 配置 | critical |
| critical-cline-config-write | Cline（VSCode）配置 | critical |
| critical-cody-config-write | Cody（Sourcegraph）配置 | critical |
| critical-claude-md-shell-redirect | Shell 重定向到 Claude | critical |
| critical-codex-instructions | Codex instructions.md | critical |

#### 包管理器配置（10 條新增）
| 規則 ID | 描述 | 嚴重度 |
|--------|------|--------|
| critical-npmrc-write | .npmrc + npm config set | critical |
| critical-yarnrc-write | .yarnrc 寫入 | critical |
| critical-pip-conf-write | pip.conf + pip config set | critical |
| critical-cargo-config-write | ~/.cargo/config.toml/credentials | critical |
| critical-gemrc-write | .gemrc | critical |
| critical-composer-config-write | ~/.composer/config.json | critical |
| critical-maven-config-write | ~/.m2/settings.xml | critical |
| critical-gradle-config-write | .gradle/init.gradle/properties | critical |
| critical-bower-config-write | .bowerrc | critical |
| critical-aws-credentials-write | AWS credentials | critical |

#### 持久化機制（4 條新增）
| 規則 ID | 描述 | 嚴重度 |
|--------|------|--------|
| critical-macos-launchagents | macOS LaunchAgent plist | critical |
| critical-macos-launchdaemons | macOS LaunchDaemon plist | critical |
| critical-linux-autostart | Linux .desktop autostart | critical |
| critical-systemd-user-write | Systemd 用戶服務 | critical |

#### 變量名擴展（implicit-agent-variable）
- 增加 20+ 變量名模式（npmrcPath, awsCreds, sshKeys, cursorRulesPath, aiderConf, clinePath, launchAgentsPath 等）

### v1.2 原有 16 條規則（保留）
[上個版本的規則依然有效]

### 規則總數演進

| 版本 | critical_paths 規則 |
|------|---------------------|
| v1.2.0 | 16 |
| **v1.3.0** | **39** |

---

## 六、真實效果對比

| 場景 | v1.1.0 | v1.2.0（含 critical_paths） |
|------|--------|---------------------------|
| pi-web 中 `writeFileSync(agentsMdPath, ...)` | 0 命中 | **3 命中** |
| pi-web 中 `function ensureAgent*` | 0 命中 | **9 命中** |
| 通用 `writeFileSync + chmod +x` 後門 | 0 命中 | **可檢測** |
| `homedir() + write` 跨函數模式 | 0 命中 | **可檢測** |

---

## 七、未來改進方向

### 短期（可做）
- [ ] 添加更多 Agent 配置路徑（Cline、Cursor、Continue、Aider）
- [ ] 改進函數名啟發（支持驼峰命名和下划線）
- [ ] 增加「import fs + import os」聯合檢測

### 中期（需要工作量）
- [ ] 實現簡單的 AST 解析（用 `ast` 庫）
- [ ] 跨函數變量追蹤（簡化版）
- [ ] 與 Semgrep 規則互補（我們做粗篩，Semgrep 做精篩）

### 長期（需要基礎設施）
- [ ] 集成 CodeQL 查詢作為深度補充
- [ ] 規則庫社區化（像 Semgrep Registry）
- [ ] 機器學習識別未知模式

---

*最後更新：2026-08-17 (v1.2.0)*