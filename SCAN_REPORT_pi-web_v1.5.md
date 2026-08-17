# 📋 skill-safety-guard 全面檢測報告（v1.5.0）

> **掃描目標**: [github.com/ct-jyjntc/pi-web](https://github.com/ct-jyjntc/pi-web)
> **掃描時間**: 2026-08-17
> **掃描工具**: skill-safety-guard **v1.5.0**（142 條規則，7 個檢測類別）
> **對比版本**: v1.1.0 首次掃描（45 條規則）

---

## 一、項目背景

| 屬性 | 值 |
|------|-----|
| **名稱** | Pi Web |
| **描述** | Local coding-agent workspace（Pi Agent 衍生作品）|
| **技術棧** | Next.js · Electron · Node.js ≥ 22.19 |
| **許可證** | MIT |
| **特性** | Streaming chat · Skills · MCP · Git Review · Worktrees · LSP |

---

## 二、總體掃描結果

### 殺手場景決策

```
🚫 [DANGER] 建議：不要安裝
發現 14 個嚴重問題。強烈建議不要安裝此 Skill
```

### 風險儀表板

| 指標 | v1.1.0 | **v1.5.0** |
|------|--------|-----------|
| 掃描文件數 | 2112 | **2640** |
| 發現問題總數 | 3 | **34** |
| 🔴 CRITICAL | 1 | **14** |
| 🟠 HIGH | 2 | **20** |
| 🟡 MEDIUM | 0 | **0** |
| 綜合風險等級 | F | **F** |
| 掃描耗時 | 1分14秒 | **~40 秒** |

### 檢測類別覆蓋（v1.5.0）

| 類別 | 發現數 |
|------|--------|
| 🔑 憑證洩露 | 0 |
| 💀 危險 Shell | 0 |
| 📁 敏感路徑 | 20 |
| 🕵️ Unicode 隱寫 | 0 |
| 🚨 關鍵系統參數 | 14 |
| 💉 提示詞注入 | 0 |
| 🔌 已安裝擴展 | 0 |

---

## 三、🚨 核心發現：自動修改全局 AGENTS.md

這是本次掃描**最重要的發現**（v1.1.0 完全漏檢，v1.5.0 精確捕獲）。

### 3.1 直接寫入（critical-agents-md-write，3 處）

**文件**: `lib/ensure-subagent-delegation.ts`

```
第257行: writeFileSync(agentsMdPath, `${SUBAGENT_POLICY_BLOCK}\n`, "utf8")
第269行: writeFileSync(agentsMdPath, next, "utf8")
第274行: writeFileSync(agentsMdPath, `${existing}${separator}${SUBAGENT_POLICY_BLOCK}\n`, "utf8")
```

**行为**：启动时自动写入/更新 `~/.pi/agent/AGENTS.md`。

### 3.2 相关函数（implicit-agent-function，9 处）

| 函数 | 文件 | 行为 |
|------|------|------|
| `ensureAgentsMdPolicy` | ensure-subagent-delegation.ts | 写入 AGENTS.md 策略块 |
| `ensureAgentOverride` | ensure-subagent-delegation.ts | 写入 agents/*.md |
| `ensureSubagentDelegation` | ensure-subagent-delegation.ts | 部署 agent 文件 |
| `syncAgent*` | 多文件 | 同步 agent 配置 |
| `createAgent*` | agent-bash-pty.ts 等 | 创建 agent |
| `createSubagent*` | index.ts | 创建 subagent |

### 3.3 影响分析

| 维度 | 影响 |
|------|------|
| **持久性** | 写入后不随项目删除而消失 |
| **跨会话** | 影响所有未来对话 |
| **跨项目** | 影响用户所有 AI 工作流 |
| **静默性** | 用户未必知道行为被改变 |
| **具体内容** | 注入 subagent 委托策略（让主 agent 主动委托）|

### 3.4 缓解建议

| 建议 | 说明 |
|------|------|
| **审查意图** | 该行为是功能设计（subagent 委托），非恶意，但应明确告知用户 |
| **加开关** | 建议提供配置选项，默认不修改全局 AGENTS.md |
| **改项目内** | 改为在项目内创建 AGENTS.md，而非全局 |
| **明确同意** | 修改全局前应征得用户明确同意 |

---

## 四、敏感路径发现（20 处）

### 4.1 引用全局 AGENTS.md（path-agents-md-ref，9 处）

分布在：
- `docs/superpowers/plans/*.md`（4 处）— 设计文档
- `lib/ensure-subagent-delegation.ts`（3 处）— 注释
- `lib/web-settings.ts`（1 处）— 配置

> 均为文档/注释引用，非实际写操作。

### 4.2 全局 AGENTS.md 写入（path-agents-md-write，11 处）

主要来自 `ensure-subagent-delegation.ts`（与 3.1 重叠）。

---

## 五、Pi Agent 全局检查（用户机器）

| 项目 | 状态 |
|------|------|
| Pi 版本 | 0.84.2 |
| ⚠️ CVE-2026-54327 | **受影响**（CRITICAL）|
| auth.json 权限 | ✅ 安全（Windows ACL 正确）|

> 注：这是用户机器状态，与 pi-web 项目本身无关。

---

## 六、v1.1.0 vs v1.5.0 能力对比

| 能力 | v1.1.0 | v1.5.0 | 提升 |
|------|--------|--------|------|
| 规则总数 | 45 | **142** | +97 |
| 检测类别 | 4 | **7** | +3 |
| AGENTS.md 写检测 | ❌ 0 | ✅ **14** | 完全捕获 |
| 提示词注入 | ❌ | ✅ 14 规则 | 新增 |
| 扩展审计 | ❌ | ✅ 11 规则 | 新增 |
| SARIF 输出 | ❌ | ✅ | 新增 |
| Freemium | ❌ | ✅ | 新增 |

---

## 七、误报分析

### 首次扫描（v1.1.0）的 3 个误报已消除

| 误报规则 | 来源 | v1.5.0 状态 |
|---------|------|------------|
| shell-curl-bash | SECURITY_AUDIT.md 漏洞描述 | ✅ 白名单过滤 |
| path-etc-passwd | SECURITY_AUDIT.md | ✅ 白名单过滤 |
| path-env-file | SECURITY_AUDIT.md | ✅ 白名单过滤 |

### 当前 34 个发现的真实性

| 类别 | 数量 | 真实性 |
|------|------|--------|
| critical-agents-md-write | 3 | ✅ **真实**（代码确认）|
| path-agents-md-write | 11 | ✅ **真实**（包含上述 3 处 + 函数定义）|
| implicit-agent-function | 9 | ✅ 真实（函数名暗示）|
| path-agents-md-ref | 9 | ⚠️ 部分为文档引用 |
| implicit-homedir-write | 1 | ✅ 真实 |
| implicit-agent-variable | 1 | ✅ 真实 |

**核心发现全部为真实命中**，无虚假警报。

---

## 八、最终结论

### 该项目是否危险？

**取决于使用场景**：

| 场景 | 判断 |
|------|------|
| 作为普通 Skill 安装 | ⚠️ **注意**：会静默修改全局 AGENTS.md |
| 作为本地开发工具 | ✅ 可接受（功能是 subagent 委托）|
| 无知晓地自动修改 | ❌ **违反最小权限原则** |

### 给用户的建议

```
✅ 可以：
  - 本地开发环境使用（了解其会修改全局 AGENTS.md）
  - 阅读 SECURITY_AUDIT.md 了解已知漏洞

⚠️ 建议：
  - 安装前了解其 AGENTS.md 修改行为
  - 使用前备份 ~/.pi/agent/AGENTS.md
  - 关注其后续版本是否提供「不修改全局」选项

❌ 不要：
  - 在生产环境直接运行（SECURITY_AUDIT 有未修复漏洞）
  - 在共享机器使用（全局配置影响他人）
```

---

## 九、技术细节

| 项目 | 值 |
|------|-----|
| 工具版本 | skill-safety-guard v1.5.0 |
| Python | 3.11.15 |
| 扫描方式 | Git clone → 静态扫描 |
| 规则数 | 142（7 类）|
| 输出格式 | Markdown（本报告）+ JSON + SARIF |

---

*报告生成时间：2026-08-17*
*工具：skill-safety-guard v1.5.0*

> **声明**：本扫描为静态分析，仅检测模式层风险。对项目意图的最终判断需结合人工审查。