# 社区推广材料（v2.0.0）

> 发布准备就绪，包含多平台推广文案 + 发布流程

---

## 📝 核心信息（所有平台通用）

**项目**：skill-safety-guard
**定位**：个人开发者安装 Skill/MCP 前的安全守护者
**版本**：v2.0.0（158 规则，8 类检测）
**Repo**：https://github.com/Wahero/Skill-safety-guard
**License**：MIT

---

## 🐦 Twitter / X（280 字符以内）

### 版本 1（英文）

```
🛡️ Just released skill-safety-guard v2.0 — a security scanner for AI Agent Skills & MCP servers.

158 rules across 8 categories:
• Prompt injection 💉
• Credential leaks 🔑
• Global config hijacking (AGENTS.md) 🚨
• Rootkit vectors
• MCP server risks

Scan any GitHub skill in 5 seconds:
safety-check https://github.com/user/repo

Free tier: 5 scans/week. MIT licensed.

https://github.com/Wahero/Skill-safety-guard

#AISecurity #LLM #OpenSource #AgentSecurity
```

### 版本 2（中文）

```
🛡️ 开源了 skill-safety-guard v2.0！

个人开发者安装 Skill/MCP 前的安全守护者。
158 条规则，8 大检测类别：
  • 提示词注入
  • 凭据泄露
  • 全局配置劫持（AGENTS.md）
  • Rootkit 向量
  • MCP 服务器风险

5 秒扫描任意 GitHub Skill：
safety-check <github-url>

免费 5 次/周，MIT 开源。

https://github.com/Wahero/Skill-safety-guard

#AISecurity #安全 #开源
```

---

## 👾 Reddit（r/LocalLLaMA / r/ArtificialIntelligence）

### 标题（3 个选项）

1. `[P] I built a security scanner for AI Agent Skills & MCP servers — catches prompt injection, credential theft, and AGENTS.md hijacking`
2. `[P] skill-safety-guard: scan any Skill/MCP before installing it (158 rules, 8 categories, MIT)`
3. `[P] Personal devs can now scan AI Skills in 5 seconds — here's how I detected silent AGENTS.md modification in a popular repo`

### 正文

```
I built skill-safety-guard — a static analyzer for AI Agent ecosystem security.

Why: The ClawHavoc attack (Jan 2026) showed 1,184 malicious skills stealing $2.3M. Traditional scanners have 0% detection on skill-based attacks because the attack vector is natural language, not code.

What it detects (158 rules / 8 categories):
- Prompt injection (ignore instructions, system prompt extraction, jailbreak)
- Credential leaks (OpenAI, AWS, GitHub tokens, etc.)
- Silent global config hijacking (AGENTS.md modification)
- Rootkit vectors (/etc/ld.so.preload, /etc/hosts)
- MCP server risks (npx -y unknown packages, curl|bash servers)
- Unicode steganography
- Sensitive path access
- Installed extension audit

Killer feature: scan any GitHub skill before installing:
    safety-check https://github.com/user/repo

Real-world validation: it detected silent AGENTS.md modification in a popular Pi Agent fork (ct-jyjntc/pi-web) that was invisible to my previous version.

Free tier: 5 scans/week. Pro: $4.99/mo. MIT license.

GitHub: https://github.com/Wahero/Skill-safety-guard
```

---

## 💬 V2EX

### 标题

`[分享] 开源了一个 AI Agent Skill 安全扫描工具（158 规则 / 8 类检测）`

### 正文

```
最近 AI Skill / MCP 生态的安全问题越来越严重。

背景：
- 2026 年 1 月 ClawHavoc 攻击：1184 个恶意 Skill，230 万美元被盗
- 传统安全工具对 Skill 攻击检出率为 0（攻击载体是自然语言，不是代码）
- 腾讯朱雀扫描 5 万个 Skill，25% 能读写文件

我开发了 skill-safety-guard：
- 对话式触发：/safety-check <github-url>，5 秒扫描远程 Skill
- 158 条规则，8 大检测类别
- 包括：提示词注入、凭据泄露、全局 AGENTS.md 劫持、Rootkit 向量、MCP 服务器风险
- 免费 5 次/周，Pro $4.99/月
- 完全开源（MIT）

实战验证：用它扫描了 ct-jyjntc/pi-web，检测到了其静默修改全局 AGENTS.md 的行为（之前版本完全漏检）。

仓库：https://github.com/Wahero/Skill-safety-guard

欢迎 Star / Issue / PR 贡献规则！
```

---

## 🚀 Hacker News（Show HN）

### 标题

`Show HN: skill-safety-guard – Scan AI Agent Skills and MCP servers before installing`

### 正文

```
Hi HN,

I built a static security scanner for the AI agent ecosystem, aimed at individual developers.

Background: The ClawHavoc attack (January 2026) demonstrated 1,184 malicious AI skills stealing $2.3M. Traditional scanners have 0% detection because skills attack via natural language instructions embedded in markdown, not executable code.

skill-safety-guard detects:
1. Prompt injection patterns (ignore-previous-instructions, system-prompt extraction, jailbreaks)
2. Silent modification of global agent configs (AGENTS.md, ~/.pi/agent/*, ~/.claude/*, ~/.cursor/*)
3. Rootkit vectors (/etc/ld.so.preload, /etc/hosts, DNS hijacking)
4. Credential leaks (OpenAI/AWS/GitHub/Slack/Stripe keys)
5. MCP server risks (npx -y unknown packages, curl|bash servers, credential-accessing tools)
6. Unicode steganography (zero-width chars, tag blocks)
7. Sensitive path access
8. Installed extension audit

Killer use case: scan any GitHub skill before you install it:
    git clone ... && cd ... && python scripts/safety-check https://github.com/user/repo
    # → SAFE / CAUTION / DANGER verdict in ~5 seconds

Real validation: it caught silent global AGENTS.md modification in ct-jyjntc/pi-web — a behavior completely invisible to regex-only scanners a week ago. The tool now tracks cross-function patterns, function-name heuristics, and multi-line constructs.

Tech: Python 3.11, regex + YAML rules, SARIF v2.1.0 output (GitHub Code Scanning compatible). 158 rules, 8 categories, MIT license.

Free: 5 scans/week. Pro: $4.99/mo.

GitHub: https://github.com/Wahero/Skill-safety-guard

Happy to discuss the detection strategy (what regex can/can't do vs AST-based tools like Semgrep/CodeQL) — I wrote up the tradeoffs in the docs.
```

---

## 📣 推广流程

### 发布日（今天）

| 时间 | 动作 |
|------|------|
| 立即 | GitHub Release v2.0.0 ✅（已完成）|
| +10min | Twitter（英文版 1 + 中文版 2）|
| +30min | Reddit r/LocalLLaMA（正文 2）|
| +1h | V2EX（分享帖）|
| +2h | HN（Show HN）|
| +1d | Linux.do / Pi Agent 社区帖 |

### 发布后 1 周

- 回复所有评论（24h 内）
- 处理第一波 Bug / 误报报告
- 统计 stars / issues / 下载
- 1 周后写「发布 1 周回顾」帖子

### 追踪指标

| 指标 | 1 周目标 |
|------|---------|
| GitHub Stars | 30-80 |
| Issues（含误报）| 5-15 |
| 规则 PR 贡献 | 1-3 |
| 活跃用户反馈 | 5-10 条 |

---

## 🎨 视觉素材

`demo/index.html` 是现成的展示页：
- 工作流图解（4 步杀手机场景）
- 真实扫描示例（危险 Shell / Unicode / 干净）
- 与 NVIDIA SkillSpector 对比表
- 性能数据

> 下一步：部署到 GitHub Pages（10 分钟），获得可分享的演示链接。

---

*最后更新：2026-08-17（v2.0.0）*