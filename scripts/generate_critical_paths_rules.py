# -*- coding: utf-8 -*-
"""Generate critical_paths.yaml with literal regex strings.

v1.3.0: Added Cursor, Aider, OpenCode, Cline, Cody agent configs.
v1.3.0: Added package managers (npm, yarn, pnpm, cargo, pip, gem, etc.).
v1.3.0: Added persistence mechanisms (macOS LaunchAgents, Linux autostart).
"""
from pathlib import Path

TARGET_FILE = Path(__file__).resolve().parent.parent / "rules" / "critical_paths.yaml"

content = r'''# skill-safety-guard 規則庫：關鍵系統參數修改檢測
# v1.2 新增：覆蓋 AI Agent 全局配置文件、Shell init、SSH 等
# v1.3 新增：Cursor/Aider/OpenCode/Cline/Cody + 包管理器 + macOS/Linux 持久化

rules:

  # === Tier 1: Pi Agent 配置文件 ===

  - id: critical-agents-md-write
    name: Global AGENTS.md write
    pattern: "(writeFileSync|fs\\.writeFile|appendFileSync|fs\\.appendFile|createWriteStream|outputFile|writeFile|fs\\.promises\\.writeFile)\\s*\\([^)]*agents?[^)]*\\)"
    severity: critical
    confidence: high
    category: critical_paths
    description: 寫入全局 AGENTS.md（AI Agent 行為配置）
    remediation: 立即拒絕

  - id: critical-pi-config-write
    name: ~/.pi/agent/* write
    pattern: "(writeFileSync|fs\\.writeFile|appendFileSync|fs\\.appendFile|createWriteStream|outputFile)\\s*\\([^)]*\\.pi/agent/[^)]*\\)"
    severity: critical
    confidence: high
    category: critical_paths
    description: 寫入 ~/.pi/agent/ 目錄（auth.json, models.json, settings.json 等）
    remediation: 立即拒絕

  - id: critical-pi-config-unlink
    name: ~/.pi/agent/* delete
    pattern: "(unlink|unlinkSync|fs\\.unlink|fs\\.unlinkSync|rmSync|fs\\.rmSync|fs\\.rm|fs\\.promises\\.rm)\\s*\\([^)]*\\.pi/agent/[^)]*\\)"
    severity: critical
    confidence: high
    category: critical_paths
    description: 刪除 ~/.pi/agent/ 目錄下任何文件
    remediation: 立即拒絕

  # === Tier 1: Claude Code ===

  - id: critical-claude-md-write
    name: Claude Code config write
    pattern: "(writeFileSync|fs\\.writeFile|appendFileSync|fs\\.appendFile|createWriteStream|outputFile)\\s*\\([^)]*\\.claude/(CLAUDE\\.md|claude\\.json|settings\\.json)[^)]*\\)"
    severity: critical
    confidence: high
    category: critical_paths
    description: 寫入 Claude Code 配置（CLAUDE.md, claude.json, settings.json）
    remediation: 立即拒絕

  - id: critical-claude-md-shell-redirect
    name: Shell redirect to Claude config
    pattern: "(>>|>|tee\\s+-a)\\s*~?(/.claude/CLAUDE\\.md|/.claude\\.json|/.claude/settings\\.json)"
    severity: critical
    confidence: high
    category: critical_paths
    description: Shell 重定向到 Claude Code 配置
    remediation: 立即拒絕

  # === Tier 1: OpenAI Codex ===

  - id: critical-codex-config-write
    name: OpenAI Codex config write
    pattern: "(writeFileSync|fs\\.writeFile|appendFileSync|fs\\.appendFile)\\s*\\([^)]*\\.codex/[^)]*\\)"
    severity: critical
    confidence: high
    category: critical_paths
    description: 寫入 OpenAI Codex 配置
    remediation: 立即拒絕

  - id: critical-codex-instructions
    name: Codex instructions.md write
    pattern: "(writeFileSync|fs\\.writeFile|appendFileSync)\\s*\\([^)]*\\.codex/instructions\\.md[^)]*\\)"
    severity: critical
    confidence: high
    category: critical_paths
    description: 寫入 Codex instructions.md（行為指令）
    remediation: 立即拒絕

  # === Tier 1: Continue.dev ===

  - id: critical-continue-config-write
    name: Continue.dev config write
    pattern: "(writeFileSync|fs\\.writeFile|appendFileSync|fs\\.appendFile)\\s*\\([^)]*\\.continue/[^)]*\\)"
    severity: critical
    confidence: high
    category: critical_paths
    description: 寫入 Continue.dev 配置
    remediation: 立即拒絕

  # === Tier 1: Cursor (v1.3 新增) ===

  - id: critical-cursor-rules-write
    name: Cursor rules write
    pattern: "(writeFileSync|fs\\.writeFile|appendFileSync|fs\\.appendFile|createWriteStream|outputFile)\\s*\\([^)]*\\.cursor/(rules/|[^/]*\\.cursorrules)[^)]*\\)"
    severity: critical
    confidence: high
    category: critical_paths
    description: |
      寫入 Cursor AI 規則文件。
      Cursor 規則可注入 AI 行為指令，影響所有 Cursor 會話。
    remediation: 立即拒絕

  - id: critical-cursor-mcp-write
    name: Cursor MCP config write
    pattern: "(writeFileSync|fs\\.writeFile|appendFileSync)\\s*\\([^)]*\\.cursor/mcp\\.json[^)]*\\)"
    severity: critical
    confidence: high
    category: critical_paths
    description: 修改 Cursor MCP 服務器配置（可注入惡意 MCP 服務器）
    remediation: 立即拒絕

  - id: critical-cursor-extensions-write
    name: Cursor extensions write
    pattern: "(writeFileSync|fs\\.writeFile)\\s*\\([^)]*\\.cursor/extensions/[^)]*\\)"
    severity: high
    confidence: high
    category: critical_paths
    description: 寫入 Cursor 擴展目錄（可能安裝惡意擴展）
    remediation: 拒絕或要求用戶明確確認

  # === Tier 1: Aider (v1.3 新增) ===

  - id: critical-aider-config-write
    name: Aider config write
    pattern: "(writeFileSync|fs\\.writeFile|appendFileSync)\\s*\\([^)]*\\.aider(\\.conf\\.yml|\\.model\\.metadata\\.json)[^)]*\\)"
    severity: critical
    confidence: high
    category: critical_paths
    description: 寫入 Aider 配置（行為規則、模型映射）
    remediation: 立即拒絕

  # === Tier 1: OpenCode (v1.3 新增) ===

  - id: critical-opencode-config-write
    name: OpenCode config write
    pattern: "(writeFileSync|fs\\.writeFile|appendFileSync)\\s*\\([^)]*\\.config/opencode/[^)]*\\)"
    severity: critical
    confidence: high
    category: critical_paths
    description: 寫入 OpenCode 配置
    remediation: 立即拒絕

  # === Tier 1: Cline (v1.3 新增) ===

  - id: critical-cline-config-write
    name: Cline (VSCode extension) config write
    pattern: "(writeFileSync|fs\\.writeFile|appendFileSync)\\s*\\([^)]*(saoudrizwan\\.cline|cline-ai)[^)]*\\)"
    severity: critical
    confidence: high
    category: critical_paths
    description: 修改 Cline 擴展配置（VSCode 內）
    remediation: 立即拒絕

  # === Tier 1: Cody (v1.3 新增) ===

  - id: critical-cody-config-write
    name: Cody (Sourcegraph) config write
    pattern: "(writeFileSync|fs\\.writeFile|appendFileSync)\\s*\\([^)]*sourcegraph\\.cody[^)]*\\)"
    severity: critical
    confidence: high
    category: critical_paths
    description: 修改 Cody 擴展配置（Sourcegraph AI）
    remediation: 立即拒絕

  # === Tier 1: Shell init 文件 ===

  - id: critical-shell-init-write
    name: Shell init file write
    pattern: "(writeFileSync|fs\\.writeFile|appendFileSync|fs\\.appendFile|createWriteStream|outputFile)\\s*\\([^)]*(\\.bashrc|\\.bash_profile|\\.zshrc|\\.zshenv|\\.profile|\\.config/fish/)[^)]*\\)"
    severity: critical
    confidence: high
    category: critical_paths
    description: 修改 Shell init 文件 = 永久後門
    remediation: 立即拒絕

  - id: critical-shell-init-shell-redirect
    name: Shell redirect to init file
    pattern: "(>>|>|tee\\s+-a)\\s*~?(/.bashrc|/.bash_profile|/.zshrc|/.zshenv|/.profile)"
    severity: critical
    confidence: high
    category: critical_paths
    description: Shell 重定向到 init 文件
    remediation: 立即拒絕

  - id: critical-shell-init-unlink
    name: Shell init file delete
    pattern: "(unlink|unlinkSync|rm|rmSync)\\s*\\(?[^)]*(\\.bashrc|\\.bash_profile|\\.zshrc|\\.zshenv|\\.profile)[^)]*\\)"
    severity: critical
    confidence: high
    category: critical_paths
    description: 刪除 Shell init 文件
    remediation: 立即拒絕

  # === Tier 1: SSH / 認證 ===

  - id: critical-ssh-authorized-keys
    name: SSH authorized_keys write
    pattern: "(writeFileSync|fs\\.writeFile|appendFileSync|fs\\.appendFile|>>|>|tee\\s+-a)\\s*\\(?[^)]*\\.ssh/authorized_keys[^)]*\\)"
    severity: critical
    confidence: high
    category: critical_paths
    description: 寫入 SSH authorized_keys（永久後門）
    remediation: 立即拒絕

  - id: critical-ssh-config-write
    name: SSH config write
    pattern: "(writeFileSync|fs\\.writeFile|appendFileSync|fs\\.appendFile)\\s*\\(?[^)]*\\.ssh/config[^)]*\\)"
    severity: critical
    confidence: high
    category: critical_paths
    description: 修改 SSH config
    remediation: 立即拒絕

  - id: critical-aws-credentials-write
    name: AWS credentials write
    pattern: "(writeFileSync|fs\\.writeFile|appendFileSync)\\s*\\(?[^)]*\\.aws/credentials[^)]*\\)"
    severity: critical
    confidence: high
    category: critical_paths
    description: 寫入 AWS credentials（雲端賬號接管）
    remediation: 立即拒絕

  # === Tier 1: Crontab ===

  - id: critical-cron-write
    name: Crontab modification
    pattern: "(writeFileSync|fs\\.writeFile|appendFileSync)\\s*\\([^)]*(crontab|cron\\.d|/etc/cron|spool/cron)[^)]*\\)|\\bcrontab\\b"
    severity: critical
    confidence: high
    category: critical_paths
    description: 修改 crontab
    remediation: 立即拒絕

  # === Tier 1: 包管理器（v1.3 新增）===
  # 包管理器配置 = 依賴投毒向量

  - id: critical-npmrc-write
    name: npm config (.npmrc) write
    pattern: "(writeFileSync|fs\\.writeFile|appendFileSync)\\s*\\([^)]*\\.npmrc[^)]*\\)|(>>|>|tee\\s+-a)\\s*~?/\\.npmrc|\\bnpm\\s+config\\s+set\\s+(registry|auth-token|_auth)"
    severity: critical
    confidence: high
    category: critical_paths
    description: |
      寫入 .npmrc（npm 配置）。
      可注入：
        - registry: 切換到惡意鏡像（依賴投毒）
        - _authToken: 永久竊取 npm 認證
    remediation: 立即拒絕

  - id: critical-yarnrc-write
    name: Yarn config write
    pattern: "(writeFileSync|fs\\.writeFile|appendFileSync)\\s*\\([^)]*\\.yarnrc[^)]*\\)|(>>|>|tee\\s+-a)\\s*~?/\\.yarnrc"
    severity: critical
    confidence: high
    category: critical_paths
    description: 寫入 .yarnrc / .yarnrc.yml（Yarn 配置）
    remediation: 立即拒絕

  - id: critical-pip-conf-write
    name: pip config write
    pattern: "(writeFileSync|fs\\.writeFile|appendFileSync)\\s*\\([^)]*(pip\\.conf|pip\\.ini)[^)]*\\)|(>>|>|tee\\s+-a)\\s*~?(/.pip/pip\\.conf|/.config/pip/pip\\.conf)|\\bpip\\s+config\\s+set\\s+(index-url|extra-index-url|trusted-host)"
    severity: critical
    confidence: high
    category: critical_paths
    description: |
      寫入 pip 配置。
      可注入：
        - index-url: 切換到惡意 PyPI 鏡像（依賴投毒）
        - trusted-host: 繞過 HTTPS 驗證
    remediation: 立即拒絕

  - id: critical-cargo-config-write
    name: Cargo (Rust) config write
    pattern: "(writeFileSync|fs\\.writeFile|appendFileSync)\\s*\\([^)]*\\.cargo/(config|config\\.toml|credentials)[^)]*\\)|(>>|>|tee\\s+-a)\\s*~?/\\.cargo/(config|credentials)"
    severity: critical
    confidence: high
    category: critical_paths
    description: |
      寫入 Cargo 配置。
      可注入：
        - source replacement: crates.io 鏡像投毒
        - credentials: crates.io token 竊取
    remediation: 立即拒絕

  - id: critical-gemrc-write
    name: Ruby gem config write
    pattern: "(writeFileSync|fs\\.writeFile|appendFileSync)\\s*\\([^)]*\\.gemrc[^)]*\\)|(>>|>|tee\\s+-a)\\s*~?/\\.gemrc"
    severity: critical
    confidence: high
    category: critical_paths
    description: 寫入 Ruby gem 配置（可注入鏡像源）
    remediation: 立即拒絕

  - id: critical-composer-config-write
    name: PHP Composer config write
    pattern: "(writeFileSync|fs\\.writeFile|appendFileSync)\\s*\\([^)]*\\.composer/config\\.json[^)]*\\)|(>>|>|tee\\s+-a)\\s*~?/\\.composer/config\\.json"
    severity: critical
    confidence: high
    category: critical_paths
    description: 寫入 Composer 配置（PHP 包管理器）
    remediation: 立即拒絕

  - id: critical-maven-config-write
    name: Maven settings write
    pattern: "(writeFileSync|fs\\.writeFile|appendFileSync)\\s*\\([^)]*\\.m2/settings\\.xml[^)]*\\)|(>>|>|tee\\s+-a)\\s*~?/\\.m2/settings\\.xml"
    severity: critical
    confidence: high
    category: critical_paths
    description: 寫入 Maven 配置（可注入惡意 Maven 倉庫）
    remediation: 立即拒絕

  - id: critical-gradle-config-write
    name: Gradle config write
    pattern: "(writeFileSync|fs\\.writeFile|appendFileSync)\\s*\\([^)]*\\.gradle/(init\\.gradle|gradle\\.properties)[^)]*\\)"
    severity: critical
    confidence: high
    category: critical_paths
    description: 寫入 Gradle 配置（可注入初始化腳本）
    remediation: 立即拒絕

  - id: critical-bower-config-write
    name: Bower config write
    pattern: "(writeFileSync|fs\\.writeFile|appendFileSync)\\s*\\([^)]*\\.bowerrc[^)]*\\)"
    severity: critical
    confidence: high
    category: critical_paths
    description: 寫入 Bower 配置（前端包管理器）
    remediation: 立即拒絕

  # === Tier 1: 持久化機制（v1.3 新增）===

  - id: critical-macos-launchagents
    name: macOS LaunchAgent write
    pattern: "(writeFileSync|fs\\.writeFile|appendFileSync|fs\\.appendFile)\\s*\\([^)]*Library/LaunchAgents/[^)]*\\.plist[^)]*\\)|(>>|>|tee\\s+-a)\\s*~?/Library/LaunchAgents/"
    severity: critical
    confidence: high
    category: critical_paths
    description: |
      寫入 ~/Library/LaunchAgents/*.plist
      macOS 持久化機制：用戶登入時自動執行。
      這是 macOS 惡意軟件最常用的持久化方法之一。
    remediation: 立即拒絕

  - id: critical-macos-launchdaemons
    name: macOS LaunchDaemon write
    pattern: "(writeFileSync|fs\\.writeFile|appendFileSync|fs\\.appendFile)\\s*\\([^)]*(/Library/LaunchDaemons/|/System/Library/LaunchDaemons/)[^)]*\\.plist[^)]*\\)"
    severity: critical
    confidence: high
    category: critical_paths
    description: |
      寫入系統級 LaunchDaemon plist。
      系統啟動時自動執行，等同於 rootkit 級別持久化。
    remediation: 立即拒絕

  - id: critical-linux-autostart
    name: Linux autostart (.desktop) write
    pattern: "(writeFileSync|fs\\.writeFile|appendFileSync|fs\\.appendFile)\\s*\\([^)]*\\.config/autostart/[^)]*\\.desktop[^)]*\\)|(>>|>|tee\\s+-a)\\s*~?/\\.config/autostart/"
    severity: critical
    confidence: high
    category: critical_paths
    description: |
      寫入 ~/.config/autostart/*.desktop
      Linux 桌面登入時自動執行。
    remediation: 立即拒絕

  - id: critical-systemd-user-write
    name: Systemd user service write
    pattern: "(writeFileSync|fs\\.writeFile|appendFileSync)\\s*\\([^)]*\\.config/systemd/user/[^)]*\\.service[^)]*\\)"
    severity: critical
    confidence: high
    category: critical_paths
    description: 寫入 Systemd 用戶服務
    remediation: 立即拒絕

  # === Tier 2: 隱式檢測 ===

  - id: implicit-agent-function
    name: Function with Agent/Policy write semantics
    pattern: "function\\s+(ensure|sync|update|write|create|patch|deploy|install|apply|configure|modify)(Agent|agent|Subagent|subagent|Policy|policy|Config|config|Settings|settings)"
    severity: high
    confidence: medium
    category: critical_paths
    description: 函數名暗示修改 Agent/Policy/Config
    remediation: 確認函數意圖

  - id: implicit-agent-variable
    name: Variable named Agent/Policy/Config
    pattern: "(const|let|var)\\s+\\w*(AgentMdPath|agentMdPath|policyPath|configPath|settingsPath|agentsMdPath|agentsMdPath|npmrcPath|npmrc|awsCreds|sshKeys|aiderConf|claudePath|codexPath|cursorRulesPath|cursorMcpPath|cursorExtPath|opencodePath|clinePath|codyPath|yarnrcPath|gemrc|composerPath|mavenPath|gradlePath|cargoConfig|pipConf|launchAgentsPath|launchAgentPath|autostartPath|systemdPath)"
    severity: high
    confidence: medium
    category: critical_paths
    description: 變量名暗示存儲 Agent/包管理/持久化配置路徑
    remediation: 確認變量最終寫入路徑

  # === Tier 3: 多行模式 ===

  - id: implicit-write-then-chmod-exec
    name: Write file then make executable
    pattern: "(writeFileSync|fs\\.writeFile|appendFileSync)[\\s\\S]{0,500}?(chmod\\s+(\\+x|[0-7]*7)|fs\\.chmod[^)]*0?7[7])"
    severity: critical
    confidence: medium
    category: critical_paths
    description: 寫文件後立即 chmod +x = 後門模式
    remediation: 立即拒絕

  - id: implicit-homedir-write
    name: homedir() + write pattern
    pattern: "(homedir\\(\\)|process\\.env\\.(HOME|USERPROFILE))[\\s\\S]{0,1000}?(writeFileSync|fs\\.writeFile|appendFileSync|outputFile|writeFile)"
    severity: high
    confidence: medium
    category: critical_paths
    description: 從 homedir() 構造路徑後寫入
    remediation: 確認寫入目標
'''

TARGET_FILE.write_text(content, encoding="utf-8")
print(f"Generated: {TARGET_FILE}")

import yaml
data = yaml.safe_load(content)
print(f"Loaded {len(data['rules'])} rules")
by_sev = {}
for r in data['rules']:
    by_sev[r['severity']] = by_sev.get(r['severity'], 0) + 1
print(f"By severity: {by_sev}")