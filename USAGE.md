# skill-safety-guard 用户手册

> **完整使用指南**（v3.0.0）
> 从安装到进阶，覆盖所有功能

---

## 目录

1. [安装](#1-安装)
2. [快速开始](#2-快速开始)
3. [扫描目标](#3-扫描目标)
4. [检测类别](#4-检测类别)
5. [命令参考](#5-命令参考)
6. [输出格式](#6-输出格式)
7. [Freemium 许可](#7-freemium-许可)
8. [误报处理](#8-误报处理)
9. [进阶用法](#9-进阶用法)
10. [故障排除](#10-故障排除)

---

## 1. 安装

### 环境要求

| 依赖 | 版本 | 检查 |
|------|------|------|
| Python | ≥ 3.8 | `python --version` |
| PyYAML | ≥ 5.0 | `python -c "import yaml"` |
| Git | 任意 | `git --version` |

### 安装步骤

```bash
# 1. 克隆仓库
git clone https://github.com/Wahero/Skill-safety-guard.git
cd Skill-safety-guard

# 2. 安装依赖（推荐虚拟环境）
python -m venv .venv
source .venv/bin/activate  # Mac/Linux
.venv\Scripts\activate     # Windows
pip install pyyaml

# 3. 验证安装
python scripts/safety-check --help
```

### 作为 Pi Agent Skill 使用

```bash
# 方式 1：复制到 skills 目录
mkdir -p ~/.pi/agent/skills/skill-safety-guard
cp SKILL.md ~/.pi/agent/skills/skill-safety-guard/

# 方式 2：软链接（开发模式）
ln -s "$(pwd)" ~/.pi/agent/skills/skill-safety-guard
```

然后在 Pi Agent 对话中输入 `/safety-check <目标>`。

---

## 2. 快速开始

### 2.1 扫描一个本地目录

```bash
python scripts/safety-check ./my-skill
```

### 2.2 扫描一个 GitHub 仓库（杀手机场景）

```bash
# 扫描整个仓库
python scripts/safety-check https://github.com/user/repo

# 扫描仓库子目录
python scripts/safety-check https://github.com/user/repo/tree/main/skills/foo

# 扫描单个文件
python scripts/safety-check https://github.com/user/repo/blob/main/SKILL.md
```

### 2.3 粘帖扫描（不下载）

```bash
cat SKILL.md | python scripts/safety-check paste
```

### 2.4 完整扫描（含 MCP）

```bash
python scripts/safety-check ./my-skill --all
```

### 2.5 只看高风险

```bash
python scripts/safety-check ./my-skill --min-confidence high
```

---

## 3. 扫描目标

| 目标类型 | 示例 | 说明 |
|---------|------|------|
| 本地目录 | `./my-skill` | 递归扫描所有文本文件 |
| 本地文件 | `./SKILL.md` | 扫描单个文件 |
| GitHub 仓库 | `https://github.com/user/repo` | 克隆后扫描 |
| GitHub 子目录 | `.../tree/main/path` | 只扫描子目录 |
| GitHub 单文件 | `.../blob/main/SKILL.md` | 只扫描文件 |
| raw 文件 | `https://raw.githubusercontent.com/...` | 直接下载 |
| 粘帖内容 | `paste` | 从 stdin 读取 |
| 当前目录 | `.`（默认） | 无参数时 |

---

## 4. 检测类别

skill-safety-guard v3.0.0 覆盖 **9 大检测类别，181 条规则**：

### 🚨 关键系统参数修改（67 条）

检测对以下文件/位置的修改、删除：

| 类别 | 覆盖 |
|------|------|
| AI Agent 配置 | Pi / Claude / Cursor / Codex / Continue / Aider / OpenCode / Cline / Cody |
| Shell init | ~/.bashrc, ~/.zshrc, ~/.profile 等 |
| 包管理器 | npm / Yarn / pip / Cargo / gem / Composer / Maven / Gradle / Bower |
| 持久化 | macOS LaunchAgents, Linux autostart, Systemd |
| 编辑器 | VSCode / Vim / Emacs / Neovim / nano |
| Git | .gitconfig（含 core.sshCommand）|
| 历史篡改 | bash/zsh/python_history |
| Rootkit | /etc/ld.so.preload, /etc/hosts |
| 数据库 | .pgpass, .my.cnf, .mongoshrc.js |

### 💉 提示词注入（14 条）

- Ignore previous instructions
- 系统提示提取
- 越狱 / 角色劫持
- 数据外泄（中英文）

### 🔌 MCP 基础（17 条）

- npx -y 未知名包
- curl|bash 服务器
- 工具名暗示危险操作
- HTTP 明文传输

### 💥 MCP 注入模式（22 条）

- SQL 注入（7 种）
- 命令注入（7 种）
- 路径遍历（5 种）
- 逻辑注入（3 种）

### 其他类别

| 类别 | 规则 | 说明 |
|------|------|------|
| 🔑 凭据泄露 | 10 | OpenAI/AWS/GitHub/Slack/Stripe/JWT/PEM |
| 💀 危险 Shell | 12 | curl\|bash/反向 Shell/rm -rf/fork bomb |
| 📁 敏感路径 | 14 | ~/.ssh/.env/.aws/Docker/K8s |
| 🕵️ Unicode 隐写 | 14 | 零宽字符/Tag 区块 |
| 🔌 已安装扩展审计 | 11 | eval/exec/写主目录 |

---

## 5. 命令参考

| 命令 | 说明 |
|------|------|
| `safety-check` | 扫描当前目录 |
| `safety-check <target>` | 扫描指定目标 |
| `safety-check --pi` | 只检查 Pi 全局 |
| `safety-check --all` | 完整扫描（Pi + Skill + MCP）|
| `safety-check --no-pi` | 跳过 Pi 检查（加速）|
| `safety-check --pro` | 启用 LLM 辅助检测（Pro）|
| `safety-check --min-confidence <level>` | 置信度过滤 |
| `safety-check --confidence-detail` | 显示置信度原因 |
| `safety-check --output <fmt>` | 输出格式（markdown/json/sarif）|
| `safety-check --report-fp <rule-id>` | 报告误报 |
| `safety-check --generate-pro-key` | 生成测试 Pro 密钥 |
| `safety-check --activate-pro <key>` | 激活 Pro |
| `safety-check --license-status` | 查看许可状态 |
| `safety-check --help` | 帮助 |

---

## 6. 输出格式

### Markdown（默认）

```bash
python scripts/safety-check ./my-skill
```

包含：
- 综合风险等级（A-F）
- 杀手机场景决策（SAFE/CAUTION/DANGER）
- 各层检测结果
- 修复建议
- 置信度标记

### JSON（机器可读）

```bash
python scripts/safety-check ./my-skill --output json
```

适合 CI/CD 集成。

### SARIF（GitHub Code Scanning）

```bash
python scripts/safety-check ./my-skill --output sarif > report.sarif
```

可在 GitHub Security 标签页查看。

---

## 7. Freemium 许可

### 免费层

- **每 5 次扫描/周**
- 所有基础检测功能
- 无到期时间

### Pro 层（$4.99/月）

- **无限扫描**
- **LLM 辅助提示词注入检测**
- 即将推出更多高级功能

### 测试 Pro 功能

```bash
# 生成测试密钥
python scripts/safety-check --generate-pro-key
# 输出: [PRO KEY GENERATED] ssg-pro-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX

# 激活
python scripts/safety-check --activate-pro ssg-pro-XXXX-...
# 输出: [PRO ACTIVATED] pro

# 查看状态
python scripts/safety-check --license-status
# 输出: Tier: PRO, Expires: ...

# 使用 Pro 功能
python scripts/safety-check ./my-skill --pro
```

> ⚠️ 注意：`--generate-pro-key` 是本地生成，仅供测试。生产环境密钥应从官方渠道获取。

---

## 8. 误报处理

### 原则

> 误报率 > 检出率。一个误报会让用户失去信任。

### 快速修复

```bash
# 只看高置信度
python scripts/safety-check ./my-skill --min-confidence high
```

### 报告误报

```bash
python scripts/safety-check --report-fp <rule-id>
```

会生成 GitHub issue 链接。

### 本地白名单

编辑 `rules/whitelist.yaml`：

```yaml
whitelisted_patterns:
  - rule_id: rule-that-misfires
    pattern: "你的具体误报文本"
    reason: 为什么是误报
```

### 置信度降级

```yaml
confidence_demotions:
  - rule_id: path-env-file
    context: '\.env\.example'
    new_confidence: low
    reason: 可能是模板文件
```

---

## 9. 进阶用法

### 9.1 在 CI 中使用

```yaml
# .github/workflows/security.yml
jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install pyyaml
      - run: python scripts/safety-check . --all --output sarif > report.sarif
      - uses: actions/upload-artifact@v4
        with:
          path: report.sarif
```

### 9.2 作为 Pre-commit hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: skill-safety
        name: Skill Safety Scan
        entry: python scripts/safety-check --no-pi
        language: system
        pass_filenames: false
```

### 9.3 批量扫描

```bash
# 扫描多个 Skill
for skill in skills/*/; do
  python scripts/safety-check "$skill" --output json > "reports/$(basename $skill).json"
done
```

### 9.4 环境变量

| 变量 | 用途 |
|------|------|
| `DEEPSEEK_API_KEY` | LLM 辅助检测 |
| `OPENAI_API_KEY` | LLM 辅助检测（备选）|
| `SSG_LICENSE_SECRET` | 自定义许可密钥 |

### 9.5 Windows 编码

```bash
# Windows 终端中文乱码时
set PYTHONIOENCODING=utf-8
```

---

## 10. 故障排除

### 问题 1：UnicodeEncodeError

```
UnicodeEncodeError: 'gbk' codec can't encode character
```

**解决**：`set PYTHONIOENCODING=utf-8`（Windows）

### 问题 2：Pi 版本检测慢/失败

```bash
# 跳过 Pi 检查
python scripts/safety-check ./my-skill --no-pi
```

### 问题 3：GitHub 仓库太大

```bash
# 扫描特定子目录（更小更快）
python scripts/safety-check https://github.com/user/repo/tree/main/specific/dir
```

### 问题 4：LLM 检测不可用

```
LLM 分析失败：未配置 API key
```

**解决**：设置 `DEEPSEEK_API_KEY` 或 `OPENAI_API_KEY`

### 问题 5：免费额度用尽

```
[FREE TIER LIMIT REACHED]
```

**解决**：等下周重置，或激活 Pro

### 问题 6：误报过多

- 用 `--min-confidence high` 过滤
- 报告误报 `--report-fp <rule-id>`
- 本地白名单

---

## 附：常用命令速查

```bash
# 最常用
python scripts/safety-check <github-url>          # 扫描远程 Skill
python scripts/safety-check ./my-skill --all     # 完整扫描
cat SKILL.md | python scripts/safety-check paste  # 粘帖扫描

# 输出
--output json     # JSON
--output sarif    # SARIF
--min-confidence high  # 只看高风险

# 许可
--generate-pro-key  # 测试密钥
--activate-pro KEY  # 激活
--license-status    # 状态

# 其他
--no-pi     # 跳过 Pi 检查
--pro       # LLM 检测
--help      # 帮助
```

---

*最后更新：2026-08-17（v3.0.0）*
*仓库：https://github.com/Wahero/Skill-safety-guard*