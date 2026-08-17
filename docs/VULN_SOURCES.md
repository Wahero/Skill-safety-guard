# 漏洞源调研与接入方案

> **文档目的**：记录 skill-safety-guard 漏洞情报系统的数据源调研结论、权威性评估、以及接入/回退方案。
> **版本**：v3.4.0 ｜ **更新日期**：2026-08-17

---

## 一、结论速览

| 漏洞源 | 权威性 | 自动可用 | 当前状态 |
|--------|--------|---------|---------|
| **OSV.dev**（主源）| ⭐⭐⭐⭐⭐ Google 官方 | ✅ | ✅ 已接入 |
| **GitHub Advisory** | ⭐⭐⭐⭐⭐ GitHub 官方 | ✅ | ✅ 已接入 |
| **本项目漏洞库** | ⭐⭐⭐⭐ 社区+自动更新 | ✅ | ✅ 已接入 |
| **CNNVD** | ⭐⭐⭐⭐⭐ 中国信息安全测评中心 | ❌ 需注册 | 📋 标记待接入 |
| **CNVD** | ⭐⭐⭐⭐⭐ 国家互联网应急中心 | ❌ 需注册 | 📋 标记待接入 |
| **NVD 镜像**（fkie-cad）| ⭐⭐⭐⭐ 社区维护 | ✅ 经代理 | ✅ 已接入 |
| ~~NVD API 2.0~~ | ❌ 已 EOL | — | ❌ 已移除 |

---

## 二、海外权威源

### 2.1 OSV.dev（主源）✅

| 项目 | 内容 |
|------|------|
| **运营方** | Google（开源安全团队）|
| **URL** | https://osv.dev |
| **API** | `POST /v1/query`（单包）/ `POST /v1/querybatch`（批量）|
| **认证** | 免费，无需 key |
| **权威性** | ⭐⭐⭐⭐⭐ 开源漏洞事实标准 |
| **优势** | ① 自动排除已撤销（withdrawn）CVE ② 支持按包名+版本精确查询 ③ 覆盖 npm/PyPI/Rust 等生态 |
| **局限** | 国内网络无法直接访问 |

**接入方式**：
```
POST https://api.osv.dev/v1/query
{
  "package": {"name": "@earendil-works/pi-coding-agent"}
}
```

**撤销清理**：OSV 查询结果**自动排除 withdrawn CVE**（官方行为），被撤销漏洞更新后自动从本地库消失。

### 2.2 GitHub Advisory Database ✅

| 项目 | 内容 |
|------|------|
| **运营方** | GitHub Security Lab |
| **URL** | https://github.com/advisories |
| **API** | GitHub GraphQL / REST |
| **认证** | 免费，GitHub token（公开数据无需）|
| **权威性** | ⭐⭐⭐⭐⭐ GitHub 生态官方 |

**覆盖**：GitHub 生态（npm 包、GitHub Actions、容器镜像等）。

### 2.3 ~~NVD~~（已弃用）❌

| 项目 | 内容 |
|------|------|
| **运营方** | 美国 NIST |
| **URL** | https://nvd.nist.gov |
| **状态** | ⚠️ **NVD API 2.0 已到达 EOL（2026 年停止服务）** |
| **原因** | 官方宣布停止支持，数据质量与可用性下降 |

> **决策**：不再使用 NVD API。改用 OSV.dev 为主源。NVD 历史数据通过社区镜像（fkie-cad）间接获取。

---

## 三、国内权威源（中国用户）

### 3.1 CNNVD 中国国家信息安全漏洞库

| 项目 | 内容 |
|------|------|
| **运营方** | 中国信息安全测评中心（国家级）|
| **URL** | https://www.cnnvd.org.cn |
| **编号格式** | `CNNVD-YYYYMM-NNNN` |
| **收录量** | ~22 万条（2023 年统计）|
| **权威性** | ⭐⭐⭐⭐⭐ 中国官方漏洞库 |

**接入现状**：
- ❌ **无公开免登录 API**
- 实测访问 `queryLds.tag` 返回 **403 Forbidden**（反爬）
- 数据下载需注册账号 + 登录
- 企业可通过「兼容性服务申请」获取数据（免费）

**可行性评估**：
- 自动化接入：**低**（需解决登录 + 反爬 + 验证码）
- 建议：标记为「需人工查询」源，供国内用户手动比对
- 若未来开放官方 API，可在 `DOMESTIC_SOURCES` 配置接入

### 3.2 CNVD 国家信息安全漏洞共享平台

| 项目 | 内容 |
|------|------|
| **运营方** | 国家互联网应急中心（CNCERT）|
| **URL** | https://www.cnvd.org.cn |
| **权威性** | ⭐⭐⭐⭐⭐ 国家级 |

**接入现状**：
- ❌ **无公开免登录 API**
- 实测访问返回 **521**（Cloudflare 反爬）
- 需注册账号 / 证书申请

**可行性评估**：同 CNNVD，自动化接入难度高，标记为「需人工」源。

### 3.3 NVD 镜像（GitHub）✅

| 项目 | 内容 |
|------|------|
| **维护方** | 社区（fkie-cad 等）|
| **URL** | https://github.com/fkie-cad/nvd-json-data-feeds |
| **格式** | NVD JSON 数据馈送（CVE-Modified 等）|
| **权威性** | ⭐⭐⭐⭐（数据源自 NVD，社区重构）|
| **访问** | 经 GitHub 加速代理（ghproxy 等）|

**接入方式**：本项目漏洞库本身就是「预筛选 + 精简」后的 NVD/OSV 数据，由 GitHub Actions 每天更新，国内用户经加速代理拉取即可。

---

## 四、访问链路与回退方案

### 4.1 自动更新回退链

```
更新漏洞库时依次尝试：
1. OSV.dev（Google 权威，自动排除 withdrawn）
2. GitHub raw 直连（本项目漏洞库）
3. 自定义加速代理（用户 --vuln-proxy 配置）
4. 内置代理（ghproxy.net / mirror.ghproxy.com / gh-proxy.com）
```

### 4.2 国内用户更新链路

```
GitHub Actions（每天 00:00 UTC）
    └─ 拉取 OSV.dev 权威源（海外服务器，无网络问题）
        └─ 合并/去重/排除 withdrawn
            └─ 更新 rules/vulnerabilities.json
                └─ 自动提交推送
                    ↓ 国内用户
              经 ghproxy 加速代理拉取仓库漏洞库
                    ↓
              本地缓存更新（自动/手动）
```

### 4.3 各场景行为

| 场景 | 行为 |
|------|------|
| 海外用户，OSV 可达 | 直接 OSV 实时查询（--osv）|
| 国内用户，GitHub 可达 | 拉取仓库漏洞库（经代理）|
| 完全离线 | 使用内置漏洞库（vulnerabilities.json）|
| OSV + 代理全失败 | 优雅降级，保留现有缓存 |

---

## 五、权威性评估方法

### 5.1 判断标准

| 维度 | 权重 | 说明 |
|------|------|------|
| 运营方权威 | 40% | 国家级/官方 > 商业公司 > 社区 |
| 数据及时性 | 25% | 每日更新 > 每周 > 手动 |
| 数据完整性 | 20% | 覆盖范围、字段完整度 |
| 可用性 | 15% | 是否免登录、是否反爬 |

### 5.2 评分结果

| 源 | 权威 | 及时 | 完整 | 可用 | 总分 |
|----|------|------|------|------|------|
| OSV.dev | 10 | 10 | 9 | 10 | **9.7** |
| CNNVD | 10 | 8 | 10 | 2 | **7.4** |
| CNVD | 10 | 8 | 10 | 2 | **7.4** |
| GitHub Advisory | 10 | 9 | 8 | 9 | **9.1** |
| NVD 镜像 | 9 | 8 | 8 | 6 | **7.9** |

---

## 六、未来扩展方向

### 6.1 CNNVD/CNVD 自动化（若开放 API）

```json
// DOMESTIC_SOURCES 配置中预留接入点
{
  "cnnvd": {
    "name": "CNNVD",
    "auto_usable": true,   // 开放 API 后改为 true
    "api_url": "待官方发布"
  }
}
```

### 6.2 多源对比与冲突解决

- 当多个源对同一 CVE 严重度评级不一致时：取最高（保守）
- 当 CNNVD/CNVD 与 OSV 描述冲突时：以更权威/更新的为准

### 6.3 漏洞摘要缓存

- 对已入库 CVE 缓存中文摘要（CNNVD/CNVD 翻译）
- 用户本地快速查看，无需重复拉取

---

## 七、附录：项目内相关实现

| 文件 | 作用 |
|------|------|
| `rules/vulnerabilities.json` | 内置漏洞库（GitHub Actions 每天更新）|
| `src/skill_safety_guard/vuln_feed.py` | 漏洞源管理（多源回退 + OSV 集成）|
| `.github/workflows/update-vulns.yml` | 每天 00:00 从权威源更新内置库 |
| `src/skill_safety_guard/pi_check/version.py` | 版本 CVE 检查（调用 vuln_feed）|

### 相关命令

```bash
# 查看漏洞库状态（数量/更新日期/缓存）
safety-check --vuln-status

# 查看所有漏洞源（含国内源）
safety-check --vuln-sources

# 设置 GitHub 加速代理（国内用户）
safety-check --vuln-proxy https://ghproxy.net/

# 手动更新
safety-check --update-vulns

# 设置更新频率
safety-check --vuln-frequency daily|weekly|monthly|off
```

---

*文档结束 ｜ 更新于 2026-08-17（v3.4.0）*