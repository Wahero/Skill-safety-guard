# -*- coding: utf-8 -*-
"""Generate critical_paths.yaml with literal regex strings (no YAML escape issues)."""
from pathlib import Path

TARGET_FILE = Path(__file__).resolve().parent.parent / "rules" / "critical_paths.yaml"

content = '''# skill-safety-guard 規則庫：關鍵系統參數修改檢測
# v1.2 新增：覆蓋 AI Agent 全局配置文件、Shell init、SSH 等
#
# 設計理念：所有「對用戶全局配置/AI Agent 行為有持久影響的文件」
# 的修改、刪除都是絕對禁止的。
#
# 分三層：
#   Tier 1 - 直接命中：寫入/刪除 + 已知路徑字符串
#   Tier 2 - 函數名/變量名啟發
#   Tier 3 - 多行/跨函數模式關聯

rules:

  # === Tier 1: AI Agent 配置文件寫入（最高優先級）===

  - id: critical-agents-md-write
    name: Global AGENTS.md write
    pattern: "(writeFileSync|fs\\\\.writeFile|appendFileSync|fs\\\\.appendFile|createWriteStream|outputFile|writeFile|fs\\\\.promises\\\\.writeFile)\\\\s*\\\\([^)]*agents?[^)]*\\\\)"
    severity: critical
    confidence: high
    category: critical_paths
    description: 寫入全局 AGENTS.md（AI Agent 行為配置）
    remediation: 立即拒絕。任何 Skill 不應自動修改用戶的全局 AI Agent 配置

  - id: critical-pi-config-write
    name: ~/.pi/agent/* write
    pattern: "(writeFileSync|fs\\\\.writeFile|appendFileSync|fs\\\\.appendFile|createWriteStream|outputFile)\\\\s*\\\\([^)]*\\\\.pi/agent/[^)]*\\\\)"
    severity: critical
    confidence: high
    category: critical_paths
    description: 寫入 ~/.pi/agent/ 目錄下任何文件（auth.json, models.json, settings.json, AGENTS.md 等）
    remediation: 立即拒絕

  - id: critical-pi-config-unlink
    name: ~/.pi/agent/* delete
    pattern: "(unlink|unlinkSync|fs\\\\.unlink|fs\\\\.unlinkSync|rmSync|fs\\\\.rmSync|fs\\\\.rm|fs\\\\.promises\\\\.rm)\\\\s*\\\\([^)]*\\\\.pi/agent/[^)]*\\\\)"
    severity: critical
    confidence: high
    category: critical_paths
    description: 刪除 ~/.pi/agent/ 目錄下任何文件
    remediation: 立即拒絕

  - id: critical-claude-md-write
    name: Claude Code config write
    pattern: "(writeFileSync|fs\\\\.writeFile|appendFileSync|fs\\\\.appendFile|createWriteStream|outputFile)\\\\s*\\\\([^)]*\\\\.claude/(CLAUDE\\\\.md|claude\\\\.json|settings\\\\.json)[^)]*\\\\)"
    severity: critical
    confidence: high
    category: critical_paths
    description: 寫入 Claude Code 配置（CLAUDE.md, claude.json, settings.json）
    remediation: 立即拒絕

  - id: critical-codex-config-write
    name: OpenAI Codex config write
    pattern: "(writeFileSync|fs\\\\.writeFile|appendFileSync|fs\\\\.appendFile)\\\\s*\\\\([^)]*\\\\.codex/[^)]*\\\\)"
    severity: critical
    confidence: high
    category: critical_paths
    description: 寫入 OpenAI Codex 配置
    remediation: 立即拒絕

  - id: critical-continue-config-write
    name: Continue.dev config write
    pattern: "(writeFileSync|fs\\\\.writeFile|appendFileSync|fs\\\\.appendFile)\\\\s*\\\\([^)]*\\\\.continue/[^)]*\\\\)"
    severity: critical
    confidence: high
    category: critical_paths
    description: 寫入 Continue.dev 配置
    remediation: 立即拒絕

  # === Tier 1: Shell init 文件（持久化代碼執行）===

  - id: critical-shell-init-write
    name: Shell init file write
    pattern: "(writeFileSync|fs\\\\.writeFile|appendFileSync|fs\\\\.appendFile|createWriteStream|outputFile)\\\\s*\\\\([^)]*(\\\\.bashrc|\\\\.bash_profile|\\\\.zshrc|\\\\.zshenv|\\\\.profile|\\\\.config/fish/)[^)]*\\\\)"
    severity: critical
    confidence: high
    category: critical_paths
    description: |
      修改 Shell init 文件 = 永久後門。
      每次 shell 啟動都會執行這些文件中的命令。
    remediation: 立即拒絕

  - id: critical-shell-init-shell-redirect
    name: Shell redirect to init file
    pattern: "(>>|>|tee\\\\s+-a)\\\\s*~?(/.bashrc|/.bash_profile|/.zshrc|/.zshenv|/.profile)"
    severity: critical
    confidence: high
    category: critical_paths
    description: Shell 命令重定向到 init 文件（如 echo xxx >> ~/.bashrc）
    remediation: 立即拒絕

  - id: critical-shell-init-unlink
    name: Shell init file delete
    pattern: "(unlink|unlinkSync|rm|rmSync)\\\\s*\\\\(?[^)]*(\\\\.bashrc|\\\\.bash_profile|\\\\.zshrc|\\\\.zshenv|\\\\.profile)[^)]*\\\\)"
    severity: critical
    confidence: high
    category: critical_paths
    description: 刪除 Shell init 文件
    remediation: 立即拒絕

  # === Tier 1: SSH authorized_keys / config ===

  - id: critical-ssh-authorized-keys
    name: SSH authorized_keys write
    pattern: "(writeFileSync|fs\\\\.writeFile|appendFileSync|fs\\\\.appendFile|>>|>|tee\\\\s+-a)\\\\s*\\\\(?[^)]*\\\\.ssh/authorized_keys[^)]*\\\\)"
    severity: critical
    confidence: high
    category: critical_paths
    description: 寫入 SSH authorized_keys（添加持久後門 SSH 訪問）
    remediation: 立即拒絕

  - id: critical-ssh-config-write
    name: SSH config write
    pattern: "(writeFileSync|fs\\\\.writeFile|appendFileSync|fs\\\\.appendFile)\\\\s*\\\\(?[^)]*\\\\.ssh/config[^)]*\\\\)"
    severity: critical
    confidence: high
    category: critical_paths
    description: 修改 SSH config（可注入 ProxyCommand 等後門）
    remediation: 立即拒絕

  # === Tier 1: Cron / Systemd 持久化 ===

  - id: critical-cron-write
    name: Crontab modification
    pattern: "(writeFileSync|fs\\\\.writeFile|appendFileSync)\\\\s*\\\\([^)]*(crontab|cron\\\\.d|/etc/cron|spool/cron)[^)]*\\\\)|\\\\bcrontab\\\\b"
    severity: critical
    confidence: high
    category: critical_paths
    description: 修改 crontab（持久化執行）
    remediation: 立即拒絕

  # === Tier 2: 函數名/變量名暗示（隱式檢測）===

  - id: implicit-agent-function
    name: Function with Agent/Policy write semantics
    pattern: "function\\\\s+(ensure|sync|update|write|create|patch|deploy|install|apply|configure|modify)(Agent|agent|Subagent|subagent|Policy|policy|Config|config|Settings|settings)"
    severity: high
    confidence: medium
    category: critical_paths
    description: |
      函數名暗示修改 Agent/Policy/Config。
      這是隱式檢測的高優先級信號。
    remediation: 確認函數意圖，避免寫全局配置

  - id: implicit-agent-variable
    name: Variable named Agent/Policy/Config
    pattern: "(const|let|var)\\\\s+\\\\w*(AgentMdPath|agentMdPath|policyPath|configPath|settingsPath|agentsMdPath|agentsMdPath)"
    severity: high
    confidence: medium
    category: critical_paths
    description: 變量名暗示存儲 Agent 配置路徑
    remediation: 確認變量最終寫入路徑

  # === Tier 3: 多行模式（跨行匹配）===

  - id: implicit-write-then-chmod-exec
    name: Write file then make executable
    pattern: "(writeFileSync|fs\\\\.writeFile|appendFileSync)[\\\\s\\\\S]{0,500}?(chmod\\\\s+(\\\\+x|[0-7]*7)|fs\\\\.chmod[^)]*0?7[7])"
    severity: critical
    confidence: medium
    category: critical_paths
    description: |
      寫文件後立即設為可執行 = 後門模式。
      500 行內的寫+chmod+x 是強烈信號。
    remediation: 立即拒絕

  - id: implicit-homedir-write
    name: homedir() + write pattern
    pattern: "(homedir\\\\(\\\\)|process\\\\.env\\\\.(HOME|USERPROFILE))[\\\\s\\\\S]{0,1000}?(writeFileSync|fs\\\\.writeFile|appendFileSync|outputFile|writeFile)"
    severity: high
    confidence: medium
    category: critical_paths
    description: |
      從 homedir() 構造路徑後寫入。
      典型於修改用戶全局配置。
    remediation: 確認寫入目標，避免全局文件
'''

TARGET_FILE.write_text(content, encoding="utf-8")
print(f"Generated: {TARGET_FILE}")

# Verify
import yaml
data = yaml.safe_load(content)
print(f"Loaded {len(data['rules'])} rules:")
for r in data['rules']:
    print(f"  - {r['id']}: {r['severity']}")