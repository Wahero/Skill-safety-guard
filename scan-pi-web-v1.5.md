[PRO] Unlimited scans · expires 2026-09-16

> **[DANGER] 建議：不要安裝**
>
> **目標**: `github.com/ct-jyjntc/pi-web`
> **危險**: 發現 14 個嚴重問題。強烈建議不要安裝此 Skill
>
> ---

# Skill Safety-guard 風險報告

> **掃描目標**: `C:\Users\ADMINI~1\AppData\Local\Temp\safety-scan-pi-web-hv04fvus`  
> **掃描文件數**: 2640  
> **發現問題數**: 34（🔴 14 | 🟠 20 | 🟡 0 | 🟢 0）

## 綜合風險等級：F

**🔴🔴 極高風險，建議不要使用**

---

## 第一層：Pi Agent 全局檢查

### Pi 版本
- **檢測到版本**: `0.84.2`
- ⚠️ 發現 1 個已知漏洞：
  - **CVE-2026-54327** (CRITICAL): 任意文件讀取漏洞：特定 SKILL.md frontmatter 可觸發讀取系統任意文件
    - 💡 升級 Pi 至 0.85.0 或更高版本

### auth.json 權限
- ✅ Windows ACL 符合安全要求（當前用戶/管理員有訪問權限，無 Everyone/Users）

---

## 第二層：Skill 內容檢測

### 🔑 憑證洩露
- 掃描文件: 528 個
- 發現問題: 0 個
- ✅ 未發現問題

### 💀 危險 Shell 命令
- 掃描文件: 528 個
- 發現問題: 0 個
- ✅ 未發現問題

### 📁 敏感路徑訪問
- 掃描文件: 528 個
- 發現問題: 20 個

### 🟠 Reference to global AGENTS.md (any code reference)
- **規則 ID**: `path-agents-md-ref`
- **嚴重度**: 🟠 HIGH | **置信度**: 🔴 high
- **位置**: `C:\Users\ADMINI~1\AppData\Local\Temp\safety-scan-pi-web-hv04fvus\docs\superpowers\plans\2026-08-02-lean-mode-implementation.md:22`
- **命中**: `~/.pi/agent/AGENTS.md`
- **說明**: 代碼中引用全局 AGENTS.md
- **建議**: 確認代碼意圖。如果目的是讀取可以，但要避免自動寫入。
如需修改全局 Agent 行為，要求用戶明確同意。


```text
- Rewriting `~/.pi/agent/AGENTS.md` for lean policy
```

### 🟠 Reference to global AGENTS.md (any code reference)
- **規則 ID**: `path-agents-md-ref`
- **嚴重度**: 🟠 HIGH | **置信度**: 🔴 high
- **位置**: `C:\Users\ADMINI~1\AppData\Local\Temp\safety-scan-pi-web-hv04fvus\docs\superpowers\plans\2026-08-02-lean-mode-implementation.md:328`
- **命中**: `~/.pi/agent/AGENTS.md`
- **說明**: 代碼中引用全局 AGENTS.md
- **建議**: 確認代碼意圖。如果目的是讀取可以，但要避免自動寫入。
如需修改全局 Agent 行為，要求用戶明確同意。


```text
| 9 | Enable lean | `stat ~/.pi/agent/AGENTS.md` before/after | Unchanged by lean feature |
```

### 🟠 Reference to global AGENTS.md (any code reference)
- **規則 ID**: `path-agents-md-ref`
- **嚴重度**: 🟠 HIGH | **置信度**: 🔴 high
- **位置**: `C:\Users\ADMINI~1\AppData\Local\Temp\safety-scan-pi-web-hv04fvus\docs\superpowers\specs\2026-08-02-lean-mode-design.md:36`
- **命中**: `~/.pi/agent/AGENTS.md`
- **說明**: 代碼中引用全局 AGENTS.md
- **建議**: 確認代碼意圖。如果目的是讀取可以，但要避免自動寫入。
如需修改全局 Agent 行為，要求用戶明確同意。


```text
- Writing lean policy into global `~/.pi/agent/AGENTS.md` (must not affect pi CLI / users who never enabled the switch)
```

### 🟠 Reference to global AGENTS.md (any code reference)
- **規則 ID**: `path-agents-md-ref`
- **嚴重度**: 🟠 HIGH | **置信度**: 🔴 high
- **位置**: `C:\Users\ADMINI~1\AppData\Local\Temp\safety-scan-pi-web-hv04fvus\docs\superpowers\specs\2026-08-02-lean-mode-design.md:286`
- **命中**: `~/.pi/agent/AGENTS.md`
- **說明**: 代碼中引用全局 AGENTS.md
- **建議**: 確認代碼意圖。如果目的是讀取可以，但要避免自動寫入。
如需修改全局 Agent 行為，要求用戶明確同意。


```text
6. Enabling never rewrites `~/.pi/agent/AGENTS.md` for lean policy.
```

### 🔴 Global AGENTS.md write access
- **規則 ID**: `path-agents-md-write`
- **嚴重度**: 🔴 CRITICAL | **置信度**: 🔴 high
- **位置**: `C:\Users\ADMINI~1\AppData\Local\Temp\safety-scan-pi-web-hv04fvus\lib\agent-bash-pty.ts:41`
- **命中**: `function createAgent`
- **說明**: 自動修改全局 AGENTS.md 或 agents/*.md（AI Agent 配置檔）
這是最高風險的攻擊之一：
- 持久性：修改後不會隨項目刪除而消失
- 跨 session：影響所有未來對話
- 跨項目：影響用戶的所有 AI 工作流
- 靜默：用戶未必知道 Agent 行為被改變

- **建議**: 立即拒絕。全局 Agent 配置修改是 skill 的重大越權行為。
如需為 Agent 提供指引，請：
  - 在專案內創建 AGENTS.md（不是全局）
  - 或在用戶明確同意下修改全局
任何「自動寫全局 AGENTS.md」的行為視為惡意。


```text
function createAgentPtyBashOperations(options?: {
```

### 🔴 Global AGENTS.md write access
- **規則 ID**: `path-agents-md-write`
- **嚴重度**: 🔴 CRITICAL | **置信度**: 🔴 high
- **位置**: `C:\Users\ADMINI~1\AppData\Local\Temp\safety-scan-pi-web-hv04fvus\lib\ensure-subagent-delegation.ts:255`
- **命中**: `function ensureAgent`
- **說明**: 自動修改全局 AGENTS.md 或 agents/*.md（AI Agent 配置檔）
這是最高風險的攻擊之一：
- 持久性：修改後不會隨項目刪除而消失
- 跨 session：影響所有未來對話
- 跨項目：影響用戶的所有 AI 工作流
- 靜默：用戶未必知道 Agent 行為被改變

- **建議**: 立即拒絕。全局 Agent 配置修改是 skill 的重大越權行為。
如需為 Agent 提供指引，請：
  - 在專案內創建 AGENTS.md（不是全局）
  - 或在用戶明確同意下修改全局
任何「自動寫全局 AGENTS.md」的行為視為惡意。


```text
function ensureAgentsMdPolicy(agentsMdPath: string): string | null {
```

### 🔴 Global AGENTS.md write access
- **規則 ID**: `path-agents-md-write`
- **嚴重度**: 🔴 CRITICAL | **置信度**: 🔴 high
- **位置**: `C:\Users\ADMINI~1\AppData\Local\Temp\safety-scan-pi-web-hv04fvus\lib\ensure-subagent-delegation.ts:257`
- **命中**: `writeFileSync(agentsMdPath, `${SUBAGENT_POLICY_BLOCK}\n`, "utf8")`
- **說明**: 自動修改全局 AGENTS.md 或 agents/*.md（AI Agent 配置檔）
這是最高風險的攻擊之一：
- 持久性：修改後不會隨項目刪除而消失
- 跨 session：影響所有未來對話
- 跨項目：影響用戶的所有 AI 工作流
- 靜默：用戶未必知道 Agent 行為被改變

- **建議**: 立即拒絕。全局 Agent 配置修改是 skill 的重大越權行為。
如需為 Agent 提供指引，請：
  - 在專案內創建 AGENTS.md（不是全局）
  - 或在用戶明確同意下修改全局
任何「自動寫全局 AGENTS.md」的行為視為惡意。


```text
writeFileSync(agentsMdPath, `${SUBAGENT_POLICY_BLOCK}\n`, "utf8");
```

### 🔴 Global AGENTS.md write access
- **規則 ID**: `path-agents-md-write`
- **嚴重度**: 🔴 CRITICAL | **置信度**: 🔴 high
- **位置**: `C:\Users\ADMINI~1\AppData\Local\Temp\safety-scan-pi-web-hv04fvus\lib\ensure-subagent-delegation.ts:269`
- **命中**: `writeFileSync(agentsMdPath, next, "utf8")`
- **說明**: 自動修改全局 AGENTS.md 或 agents/*.md（AI Agent 配置檔）
這是最高風險的攻擊之一：
- 持久性：修改後不會隨項目刪除而消失
- 跨 session：影響所有未來對話
- 跨項目：影響用戶的所有 AI 工作流
- 靜默：用戶未必知道 Agent 行為被改變

- **建議**: 立即拒絕。全局 Agent 配置修改是 skill 的重大越權行為。
如需為 Agent 提供指引，請：
  - 在專案內創建 AGENTS.md（不是全局）
  - 或在用戶明確同意下修改全局
任何「自動寫全局 AGENTS.md」的行為視為惡意。


```text
writeFileSync(agentsMdPath, next, "utf8");
```

### 🔴 Global AGENTS.md write access
- **規則 ID**: `path-agents-md-write`
- **嚴重度**: 🔴 CRITICAL | **置信度**: 🔴 high
- **位置**: `C:\Users\ADMINI~1\AppData\Local\Temp\safety-scan-pi-web-hv04fvus\lib\ensure-subagent-delegation.ts:274`
- **命中**: `writeFileSync(agentsMdPath, `${existing}${separator}${SUBAGENT_POLICY_BLOCK}\n`,...`
- **說明**: 自動修改全局 AGENTS.md 或 agents/*.md（AI Agent 配置檔）
這是最高風險的攻擊之一：
- 持久性：修改後不會隨項目刪除而消失
- 跨 session：影響所有未來對話
- 跨項目：影響用戶的所有 AI 工作流
- 靜默：用戶未必知道 Agent 行為被改變

- **建議**: 立即拒絕。全局 Agent 配置修改是 skill 的重大越權行為。
如需為 Agent 提供指引，請：
  - 在專案內創建 AGENTS.md（不是全局）
  - 或在用戶明確同意下修改全局
任何「自動寫全局 AGENTS.md」的行為視為惡意。


```text
writeFileSync(agentsMdPath, `${existing}${separator}${SUBAGENT_POLICY_BLOCK}\n`, "utf8");
```

### 🔴 Global AGENTS.md write access
- **規則 ID**: `path-agents-md-write`
- **嚴重度**: 🔴 CRITICAL | **置信度**: 🔴 high
- **位置**: `C:\Users\ADMINI~1\AppData\Local\Temp\safety-scan-pi-web-hv04fvus\lib\ensure-subagent-delegation.ts:278`
- **命中**: `function ensureAgent`
- **說明**: 自動修改全局 AGENTS.md 或 agents/*.md（AI Agent 配置檔）
這是最高風險的攻擊之一：
- 持久性：修改後不會隨項目刪除而消失
- 跨 session：影響所有未來對話
- 跨項目：影響用戶的所有 AI 工作流
- 靜默：用戶未必知道 Agent 行為被改變

- **建議**: 立即拒絕。全局 Agent 配置修改是 skill 的重大越權行為。
如需為 Agent 提供指引，請：
  - 在專案內創建 AGENTS.md（不是全局）
  - 或在用戶明確同意下修改全局
任何「自動寫全局 AGENTS.md」的行為視為惡意。


```text
function ensureAgentOverride(agentsDir: string, filename: string, content: string): string | null {
```

### 🔴 Global AGENTS.md write access
- **規則 ID**: `path-agents-md-write`
- **嚴重度**: 🔴 CRITICAL | **置信度**: 🔴 high
- **位置**: `C:\Users\ADMINI~1\AppData\Local\Temp\safety-scan-pi-web-hv04fvus\lib\ensure-subagent-delegation.ts:315`
- **命中**: `function ensureSubagent`
- **說明**: 自動修改全局 AGENTS.md 或 agents/*.md（AI Agent 配置檔）
這是最高風險的攻擊之一：
- 持久性：修改後不會隨項目刪除而消失
- 跨 session：影響所有未來對話
- 跨項目：影響用戶的所有 AI 工作流
- 靜默：用戶未必知道 Agent 行為被改變

- **建議**: 立即拒絕。全局 Agent 配置修改是 skill 的重大越權行為。
如需為 Agent 提供指引，請：
  - 在專案內創建 AGENTS.md（不是全局）
  - 或在用戶明確同意下修改全局
任何「自動寫全局 AGENTS.md」的行為視為惡意。


```text
export function ensureSubagentDelegation(): string[] {
```

### 🔴 Global AGENTS.md write access
- **規則 ID**: `path-agents-md-write`
- **嚴重度**: 🔴 CRITICAL | **置信度**: 🔴 high
- **位置**: `C:\Users\ADMINI~1\AppData\Local\Temp\safety-scan-pi-web-hv04fvus\lib\ensure-subagent-delegation.ts:347`
- **命中**: `function syncAgent`
- **說明**: 自動修改全局 AGENTS.md 或 agents/*.md（AI Agent 配置檔）
這是最高風險的攻擊之一：
- 持久性：修改後不會隨項目刪除而消失
- 跨 session：影響所有未來對話
- 跨項目：影響用戶的所有 AI 工作流
- 靜默：用戶未必知道 Agent 行為被改變

- **建議**: 立即拒絕。全局 Agent 配置修改是 skill 的重大越權行為。
如需為 Agent 提供指引，請：
  - 在專案內創建 AGENTS.md（不是全局）
  - 或在用戶明確同意下修改全局
任何「自動寫全局 AGENTS.md」的行為視為惡意。


```text
export function syncAgentModelsFromRoles(settings?: WebSettings): string[] {
```

### 🟠 Reference to global AGENTS.md (any code reference)
- **規則 ID**: `path-agents-md-ref`
- **嚴重度**: 🟠 HIGH | **置信度**: 🔴 high
- **位置**: `C:\Users\ADMINI~1\AppData\Local\Temp\safety-scan-pi-web-hv04fvus\lib\ensure-subagent-delegation.ts:16`
- **命中**: `~/.pi/agent/AGENTS.md`
- **說明**: 代碼中引用全局 AGENTS.md
- **建議**: 確認代碼意圖。如果目的是讀取可以，但要避免自動寫入。
如需修改全局 Agent 行為，要求用戶明確同意。


```text
*  1. A managed block in ~/.pi/agent/AGENTS.md tells the parent to delegate.
```

### 🟠 Reference to global AGENTS.md (any code reference)
- **規則 ID**: `path-agents-md-ref`
- **嚴重度**: 🟠 HIGH | **置信度**: 🔴 high
- **位置**: `C:\Users\ADMINI~1\AppData\Local\Temp\safety-scan-pi-web-hv04fvus\lib\ensure-subagent-delegation.ts:258`
- **命中**: `~/.pi/agent/AGENTS.md`
- **說明**: 代碼中引用全局 AGENTS.md
- **建議**: 確認代碼意圖。如果目的是讀取可以，但要避免自動寫入。
如需修改全局 Agent 行為，要求用戶明確同意。


```text
return "Created ~/.pi/agent/AGENTS.md with subagent delegation policy";
```

### 🟠 Reference to global AGENTS.md (any code reference)
- **規則 ID**: `path-agents-md-ref`
- **嚴重度**: 🟠 HIGH | **置信度**: 🔴 high
- **位置**: `C:\Users\ADMINI~1\AppData\Local\Temp\safety-scan-pi-web-hv04fvus\lib\ensure-subagent-delegation.ts:270`
- **命中**: `~/.pi/agent/AGENTS.md`
- **說明**: 代碼中引用全局 AGENTS.md
- **建議**: 確認代碼意圖。如果目的是讀取可以，但要避免自動寫入。
如需修改全局 Agent 行為，要求用戶明確同意。


```text
return "Updated subagent delegation policy in ~/.pi/agent/AGENTS.md";
```

### 🟠 Reference to global AGENTS.md (any code reference)
- **規則 ID**: `path-agents-md-ref`
- **嚴重度**: 🟠 HIGH | **置信度**: 🔴 high
- **位置**: `C:\Users\ADMINI~1\AppData\Local\Temp\safety-scan-pi-web-hv04fvus\lib\ensure-subagent-delegation.ts:275`
- **命中**: `~/.pi/agent/AGENTS.md`
- **說明**: 代碼中引用全局 AGENTS.md
- **建議**: 確認代碼意圖。如果目的是讀取可以，但要避免自動寫入。
如需修改全局 Agent 行為，要求用戶明確同意。


```text
return "Appended subagent delegation policy to ~/.pi/agent/AGENTS.md";
```

### 🔴 Global AGENTS.md write access
- **規則 ID**: `path-agents-md-write`
- **嚴重度**: 🔴 CRITICAL | **置信度**: 🔴 high
- **位置**: `C:\Users\ADMINI~1\AppData\Local\Temp\safety-scan-pi-web-hv04fvus\lib\global-agent-mode.ts:20`
- **命中**: `function syncGlobalAgent`
- **說明**: 自動修改全局 AGENTS.md 或 agents/*.md（AI Agent 配置檔）
這是最高風險的攻擊之一：
- 持久性：修改後不會隨項目刪除而消失
- 跨 session：影響所有未來對話
- 跨項目：影響用戶的所有 AI 工作流
- 靜默：用戶未必知道 Agent 行為被改變

- **建議**: 立即拒絕。全局 Agent 配置修改是 skill 的重大越權行為。
如需為 Agent 提供指引，請：
  - 在專案內創建 AGENTS.md（不是全局）
  - 或在用戶明確同意下修改全局
任何「自動寫全局 AGENTS.md」的行為視為惡意。


```text
export function syncGlobalAgentModeEffects(mode: AgentMode): void {
```

### 🔴 Global AGENTS.md write access
- **規則 ID**: `path-agents-md-write`
- **嚴重度**: 🔴 CRITICAL | **置信度**: 🔴 high
- **位置**: `C:\Users\ADMINI~1\AppData\Local\Temp\safety-scan-pi-web-hv04fvus\lib\resolve-pi-cli.ts:98`
- **命中**: `function ensureSubagent`
- **說明**: 自動修改全局 AGENTS.md 或 agents/*.md（AI Agent 配置檔）
這是最高風險的攻擊之一：
- 持久性：修改後不會隨項目刪除而消失
- 跨 session：影響所有未來對話
- 跨項目：影響用戶的所有 AI 工作流
- 靜默：用戶未必知道 Agent 行為被改變

- **建議**: 立即拒絕。全局 Agent 配置修改是 skill 的重大越權行為。
如需為 Agent 提供指引，請：
  - 在專案內創建 AGENTS.md（不是全局）
  - 或在用戶明確同意下修改全局
任何「自動寫全局 AGENTS.md」的行為視為惡意。


```text
export function ensureSubagentSpawnEnv(): {
```

### 🟠 Reference to global AGENTS.md (any code reference)
- **規則 ID**: `path-agents-md-ref`
- **嚴重度**: 🟠 HIGH | **置信度**: 🔴 high
- **位置**: `C:\Users\ADMINI~1\AppData\Local\Temp\safety-scan-pi-web-hv04fvus\lib\web-settings.ts:98`
- **命中**: `~/.pi/agent/AGENTS.md`
- **說明**: 代碼中引用全局 AGENTS.md
- **建議**: 確認代碼意圖。如果目的是讀取可以，但要避免自動寫入。
如需修改全局 Agent 行為，要求用戶明確同意。


```text
* Default off. Does not rewrite ~/.pi/agent/AGENTS.md.
```

### 🔴 Global AGENTS.md write access
- **規則 ID**: `path-agents-md-write`
- **嚴重度**: 🔴 CRITICAL | **置信度**: 🔴 high
- **位置**: `C:\Users\ADMINI~1\AppData\Local\Temp\safety-scan-pi-web-hv04fvus\lib\first-party\subagents\index.ts:67`
- **命中**: `function createSubagent`
- **說明**: 自動修改全局 AGENTS.md 或 agents/*.md（AI Agent 配置檔）
這是最高風險的攻擊之一：
- 持久性：修改後不會隨項目刪除而消失
- 跨 session：影響所有未來對話
- 跨項目：影響用戶的所有 AI 工作流
- 靜默：用戶未必知道 Agent 行為被改變

- **建議**: 立即拒絕。全局 Agent 配置修改是 skill 的重大越權行為。
如需為 Agent 提供指引，請：
  - 在專案內創建 AGENTS.md（不是全局）
  - 或在用戶明確同意下修改全局
任何「自動寫全局 AGENTS.md」的行為視為惡意。


```text
export function createSubagentsInlineExtension(): InlineExtension {
```

### 🕵️ Unicode 隱寫
- 掃描文件: 528 個
- 發現問題: 0 個
- ✅ 未發現問題

### 🚨 關鍵系統參數修改
- 掃描文件: 528 個
- 發現問題: 14 個

### 🟠 homedir() + write pattern
- **規則 ID**: `implicit-homedir-write`
- **嚴重度**: 🟠 HIGH | **置信度**: 🟡 medium
- **位置**: `C:\Users\ADMINI~1\AppData\Local\Temp\safety-scan-pi-web-hv04fvus\app\api\skills\route.ts:42`
- **命中**: `homedir(), ".agents", "skills");
    if (existsSync(globalSkillsDir)) allowedRoots.add(globalSkillsD...`
- **說明**: 從 homedir() 構造路徑後寫入
- **建議**: 確認寫入目標

```text

```

### 🟠 Function with Agent/Policy write semantics
- **規則 ID**: `implicit-agent-function`
- **嚴重度**: 🟠 HIGH | **置信度**: 🟡 medium
- **位置**: `C:\Users\ADMINI~1\AppData\Local\Temp\safety-scan-pi-web-hv04fvus\lib\agent-bash-pty.ts:41`
- **命中**: `function createAgent`
- **說明**: 函數名暗示修改 Agent/Policy/Config
- **建議**: 確認函數意圖

```text

```

### 🟠 Variable named Agent/Policy/Config
- **規則 ID**: `implicit-agent-variable`
- **嚴重度**: 🟠 HIGH | **置信度**: 🟡 medium
- **位置**: `C:\Users\ADMINI~1\AppData\Local\Temp\safety-scan-pi-web-hv04fvus\lib\ensure-builtin-packages.ts:58`
- **命中**: `const settingsPath`
- **說明**: 變量名暗示存儲 Agent/包管理/持久化配置路徑
- **建議**: 確認變量最終寫入路徑

```text

```

### 🔴 Global AGENTS.md write
- **規則 ID**: `critical-agents-md-write`
- **嚴重度**: 🔴 CRITICAL | **置信度**: 🔴 high
- **位置**: `C:\Users\ADMINI~1\AppData\Local\Temp\safety-scan-pi-web-hv04fvus\lib\ensure-subagent-delegation.ts:257`
- **命中**: `writeFileSync(agentsMdPath, `${SUBAGENT_POLICY_BLOCK}\n`, "utf8")`
- **說明**: 寫入全局 AGENTS.md（AI Agent 行為配置）
- **建議**: 立即拒絕

```text

```

### 🔴 Global AGENTS.md write
- **規則 ID**: `critical-agents-md-write`
- **嚴重度**: 🔴 CRITICAL | **置信度**: 🔴 high
- **位置**: `C:\Users\ADMINI~1\AppData\Local\Temp\safety-scan-pi-web-hv04fvus\lib\ensure-subagent-delegation.ts:269`
- **命中**: `writeFileSync(agentsMdPath, next, "utf8")`
- **說明**: 寫入全局 AGENTS.md（AI Agent 行為配置）
- **建議**: 立即拒絕

```text

```

### 🔴 Global AGENTS.md write
- **規則 ID**: `critical-agents-md-write`
- **嚴重度**: 🔴 CRITICAL | **置信度**: 🔴 high
- **位置**: `C:\Users\ADMINI~1\AppData\Local\Temp\safety-scan-pi-web-hv04fvus\lib\ensure-subagent-delegation.ts:274`
- **命中**: `writeFileSync(agentsMdPath, `${existing}${separator}${SUBAGENT_POLICY_BLOCK}\n`, "utf8")`
- **說明**: 寫入全局 AGENTS.md（AI Agent 行為配置）
- **建議**: 立即拒絕

```text

```

### 🟠 Function with Agent/Policy write semantics
- **規則 ID**: `implicit-agent-function`
- **嚴重度**: 🟠 HIGH | **置信度**: 🟡 medium
- **位置**: `C:\Users\ADMINI~1\AppData\Local\Temp\safety-scan-pi-web-hv04fvus\lib\ensure-subagent-delegation.ts:255`
- **命中**: `function ensureAgent`
- **說明**: 函數名暗示修改 Agent/Policy/Config
- **建議**: 確認函數意圖

```text

```

### 🟠 Function with Agent/Policy write semantics
- **規則 ID**: `implicit-agent-function`
- **嚴重度**: 🟠 HIGH | **置信度**: 🟡 medium
- **位置**: `C:\Users\ADMINI~1\AppData\Local\Temp\safety-scan-pi-web-hv04fvus\lib\ensure-subagent-delegation.ts:278`
- **命中**: `function ensureAgent`
- **說明**: 函數名暗示修改 Agent/Policy/Config
- **建議**: 確認函數意圖

```text

```

### 🟠 Function with Agent/Policy write semantics
- **規則 ID**: `implicit-agent-function`
- **嚴重度**: 🟠 HIGH | **置信度**: 🟡 medium
- **位置**: `C:\Users\ADMINI~1\AppData\Local\Temp\safety-scan-pi-web-hv04fvus\lib\ensure-subagent-delegation.ts:315`
- **命中**: `function ensureSubagent`
- **說明**: 函數名暗示修改 Agent/Policy/Config
- **建議**: 確認函數意圖

```text

```

### 🟠 Function with Agent/Policy write semantics
- **規則 ID**: `implicit-agent-function`
- **嚴重度**: 🟠 HIGH | **置信度**: 🟡 medium
- **位置**: `C:\Users\ADMINI~1\AppData\Local\Temp\safety-scan-pi-web-hv04fvus\lib\ensure-subagent-delegation.ts:347`
- **命中**: `function syncAgent`
- **說明**: 函數名暗示修改 Agent/Policy/Config
- **建議**: 確認函數意圖

```text

```

### 🟠 Function with Agent/Policy write semantics
- **規則 ID**: `implicit-agent-function`
- **嚴重度**: 🟠 HIGH | **置信度**: 🟡 medium
- **位置**: `C:\Users\ADMINI~1\AppData\Local\Temp\safety-scan-pi-web-hv04fvus\lib\model-runtime.ts:26`
- **命中**: `function createConfig`
- **說明**: 函數名暗示修改 Agent/Policy/Config
- **建議**: 確認函數意圖

```text

```

### 🟠 Function with Agent/Policy write semantics
- **規則 ID**: `implicit-agent-function`
- **嚴重度**: 🟠 HIGH | **置信度**: 🟡 medium
- **位置**: `C:\Users\ADMINI~1\AppData\Local\Temp\safety-scan-pi-web-hv04fvus\lib\permission-policy.ts:210`
- **命中**: `function applyAgent`
- **說明**: 函數名暗示修改 Agent/Policy/Config
- **建議**: 確認函數意圖

```text

```

### 🟠 Function with Agent/Policy write semantics
- **規則 ID**: `implicit-agent-function`
- **嚴重度**: 🟠 HIGH | **置信度**: 🟡 medium
- **位置**: `C:\Users\ADMINI~1\AppData\Local\Temp\safety-scan-pi-web-hv04fvus\lib\resolve-pi-cli.ts:98`
- **命中**: `function ensureSubagent`
- **說明**: 函數名暗示修改 Agent/Policy/Config
- **建議**: 確認函數意圖

```text

```

### 🟠 Function with Agent/Policy write semantics
- **規則 ID**: `implicit-agent-function`
- **嚴重度**: 🟠 HIGH | **置信度**: 🟡 medium
- **位置**: `C:\Users\ADMINI~1\AppData\Local\Temp\safety-scan-pi-web-hv04fvus\lib\first-party\subagents\index.ts:67`
- **命中**: `function createSubagent`
- **說明**: 函數名暗示修改 Agent/Policy/Config
- **建議**: 確認函數意圖

```text

```

---

## 建議
- 🚫 強烈建議不要安裝此 Skill
- 🔍 可嘗試聯繫作者修復，或尋找替代品
- 💬 可使用 `/safety-check --report-fp <rule-id>` 報告誤報

---

*本報告由 skill-safety-guard v0.1.0 自動生成*  
*規則庫開源：https://github.com/Wahero/Skill-safety-guard/blob/main/rules/*  
*發現誤報？執行 `/safety-check --report-fp <rule-id>`*
