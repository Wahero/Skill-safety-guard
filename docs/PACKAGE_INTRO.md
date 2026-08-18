# skill-safety-guard

> **裝 Skill 之前，先掃一掃。**
> **Scan before you trust — install anything.**

---

## 短描述（Gallery Card / package.json description）

**EN**: Security guard before installing third-party Skills/MCPs. One command scans for credential leaks, dangerous shell, prompt injection, and checks your Pi Agent global security — 181 rules, 9 categories, open-source rule library.

**中文**: 安裝第三方 Skill/MCP 前的安全守護者。一條命令掃描憑證洩露、危險 Shell、提示詞注入，並檢查 Pi Agent 全局安全——181 條規則、9 大類別、規則庫開源。

---

# 🇬🇧 English

## The Problem

**Skills are the new attack surface — and traditional tools can't see it.**

In January 2026, the ClawHavoc campaign distributed **1,184 malicious Skills** and stole **$2.3M**. Malicious Skills don't ship malware binaries — they ship *natural-language instructions* that trick the agent into exfiltrating credentials, rewriting `~/.pi/agent/AGENTS.md`, or piping `curl | bash` straight into a reverse shell.

Traditional security scanners report a **0.00% detection rate** against this attack class. They scan code; Skills attack through *prompt text*. So how do you know a Skill is safe before you install it?

**You can't. Until now.**

## The Solution

`safety-check` — a conversation-triggered security scan, built for individual developers, that answers one question in seconds:

> **"Is it safe to install this Skill?"**

```
/safety-check https://github.com/someone/sketchy-skill
```

Pure static analysis. **Nothing is downloaded to your agent, nothing is executed.** The scan happens in an isolated clone, then reports back with a clear verdict.

## What It Detects

**181 rules across 9 categories:**

| Category | What it catches |
|----------|----------------|
| 🔑 Credential leaks | OpenAI / Anthropic / AWS / GitHub / Slack / Stripe keys, JWT, PEM private keys |
| 💀 Dangerous shell | `curl \| bash`, reverse shells, `rm -rf /`, fork bombs, base64 obfuscation |
| 🚨 System hijacking | Writes to `~/.pi/agent/AGENTS.md`, shell init files, cron, systemd, LaunchAgents, Git hooks, `/etc/ld.so.preload` |
| 💉 Prompt injection | "Ignore previous instructions", system-prompt exfiltration, jailbreaks, role hijacking |
| 🔌 MCP dependency abuse | `npx -y` unknown packages, SQL/command injection, path traversal, plaintext HTTP servers |
| 🕵️ Unicode steganography | Zero-width characters, tag blocks, invisible operators hiding malicious intent |

Plus **Pi Agent global checks**: your Pi version against known CVEs, and `auth.json` ACL permissions.

## Three-Second Decision

No 50-page report to interpret. Every scan ends with a verdict:

- 🟢 **SAFE** — install it
- 🟡 **CAUTION** — review these N findings first
- 🔴 **DANGER** — do not install

## Daily-Fresh Vulnerability Intelligence

The engine pairs regex rules with a **self-updating vulnerability feed** — OSV.dev (Google) as primary source, AVID as automatic fallback, CAIVD for the Chinese ecosystem, refreshed daily via GitHub Actions. If your Pi has a known CVE, you'll know before you run anything.

## Open-Source Rule Library

Security tools are only as trustworthy as their rules. Ours are **auditable, forkable, and community-contributable** — the exact opposite of a black-box scanner. Spot a missed pattern? Open a PR, add a rule, ship it.

## Built for Real World False-Positive Fatigue

The tool that cries wolf gets uninstalled. So we invest in trust:

- **Confidence tiers** (🔴 high / 🟡 medium / 🟢 low) so noise never buries signal
- **Whitelist engine** with path + pattern matching — known-safe patterns are filtered, precisely
- **One-command false-positive reporting** (`--report-fp <rule-id>`) that opens a GitHub issue for you
- **Dogfooded to zero**: the tool scans its own repository clean — 0 findings, grade A

## Technical Snapshot

| | |
|---|---|
| Detection rate | 8/8 malicious fixtures (100%) |
| False-positive baseline | 0% on clean fixtures |
| Output formats | Markdown / JSON / SARIF (GitHub Code Scanning) |
| Performance | ~0.6s typical scan (cached rules + version check) |
| Runtime | Pure static analysis — no dependency install, no code execution |
| License | MIT, free tier 5 scans/week, Pro $4.99/mo |

## Install & Use

```bash
pi install git:github.com/Wahero/Skill-safety-guard
# then, anywhere:
/safety-check https://github.com/user/any-skill
```

One source of truth — the repo *is* the package. No duplicated codebase to maintain, no pip install required.

---

# 🇨🇳 中文

## 痛點：Skill 就是新的攻擊面，傳統工具卻看不見

**2026 年 1 月，ClawHavoc 攻擊：1,184 個惡意 Skill、230 萬美元被盜。**

惡意 Skill 不攜帶可執行文件——它們攜帶的是**自然語言指令**：騙 Agent 外洩憑證、改寫 `~/.pi/agent/AGENTS.md`、或是 `curl | bash` 一條管道直接接上反向 Shell。

傳統安全掃描器對這類攻擊的**檢出率是 0.00%**。它們掃代碼；Skill 通過「提示詞文本」攻擊。那麼問題來了：

> **安裝一個 Skill 之前，你怎麼知道它安不安全？**

**以前不知道。現在可以。**

## 解決方案：一句話掃描

`safety-check`——為個人開發者設計的對話式安全掃描：

```
/safety-check https://github.com/someone/sketchy-skill
```

**純靜態分析。不下載到你的 Agent、不執行任何代碼。** 掃描在隔離的臨時克隆中完成，然後給你一個明確結論。

## 檢測什麼

**181 條規則、9 大類別：**

| 類別 | 捕捉什麼 |
|------|---------|
| 🔑 憑證洩露 | OpenAI / Anthropic / AWS / GitHub / Slack / Stripe 金鑰、JWT、PEM 私鑰 |
| 💀 危險 Shell | `curl \| bash`、反向 Shell、`rm -rf /`、fork bomb、base64 混淆 |
| 🚨 系統劫持 | 寫入 `~/.pi/agent/AGENTS.md`、Shell init、cron、systemd、LaunchAgents、Git hooks、`/etc/ld.so.preload` |
| 💉 提示詞注入 | 「忽略之前的指令」、系統提示提取、越獄、角色劫持 |
| 🔌 MCP 依賴濫用 | `npx -y` 未知名包、SQL/命令注入、路徑遍歷、明文 HTTP 伺服器 |
| 🕵️ Unicode 隱寫 | 零寬字符、Tag 區塊、不可見運算符藏匿惡意意圖 |

外加 **Pi Agent 全局檢查**：你的 Pi 版本是否命中已知 CVE、`auth.json` ACL 權限是否過寬。

## 三秒決策，不用讀 50 頁報告

每次掃描都以明確結論收尾：

- 🟢 **SAFE** — 可以裝
- 🟡 **CAUTION** — 先人工複查這 N 個發現
- 🔴 **DANGER** — 不要安裝

## 每日更新的漏洞情報

正則規則之外，引擎配備**自動更新的漏洞庫**——OSV.dev（Google 官方）為主源、AVID 自動回退、CAIVD 覆蓋國內生態，GitHub Actions 每天刷新。你的 Pi 有已知漏洞？在運行任何東西之前你就會知道。

## 規則庫開源，可審計、可貢獻

安全工具的價值取決於規則是否可信。我們的規則**可審計、可 fork、可社區貢獻**——和黑盒掃描器正好相反。發現漏網模式？開個 PR、加條規則、上線。

## 認真對待誤報——因為亂叫的工具會被卸載

我們把功夫花在建立信任上：

- **置信度分級**（🔴 高 / 🟡 中 / 🟢 低），噪音永遠蓋不住重點
- **白名單引擎**（路徑 + 模式精準匹配），已知安全模式被精確過濾
- **一鍵誤報反饋**（`--report-fp <rule-id>`），自動生成 GitHub issue
- **Dogfooding 到零**：工具掃描自己的倉庫——0 發現、A 級

## 技術一覽

| | |
|---|---|
| 檢出率 | 惡意樣本 8/8（100%） |
| 誤報基線 | 乾淨樣本 0% |
| 輸出格式 | Markdown / JSON / SARIF（GitHub Code Scanning） |
| 性能 | 典型掃描 ~0.6s（規則編譯緩存 + 版本緩存） |
| 運行方式 | 純靜態分析——不安裝依賴、不執行代碼 |
| 許可 | MIT，免費每週 5 次，Pro $4.99/月 |

## 安裝與使用

```bash
pi install git:github.com/Wahero/Skill-safety-guard
# 然後在任何地方：
/safety-check https://github.com/user/any-skill
```

**單一來源**——倉庫本身就是 package。沒有第二份代碼要維護，也不需要 pip install。

---

## Install / 安裝

```bash
pi install git:github.com/Wahero/Skill-safety-guard
# or from npm after publishing
pi install npm:skill-safety-guard
```

> **Security note / 安全提示**: Pi packages run with full system access. skill-safety-guard itself only performs static analysis — but as with any third-party package, review the source first. 本工具只做靜態分析，但和其他第三方包一樣，請先審閱源碼再安裝。

---

*English · 中文 ｜ MIT License ｜ [GitHub](https://github.com/Wahero/Skill-safety-guard)*
