# 📋 skill-safety-guard 修訂掃描報告（v3.4.3 + 最新漏洞庫）

> **掃描目標**: [github.com/ct-jyjntc/pi-web](https://github.com/ct-jyjntc/pi-web)
> **掃描時間**: 2026-08-17
> **掃描工具**: skill-safety-guard **v3.4.3**（181 規則，9 類檢測）
> **漏洞庫**: OSV.dev 權威源（4 條最新 CVE，更新於 2026-08-17 15:49 UTC）
> **對比版本**: v1.5.0 報告（`SCAN_REPORT_pi-web_v1.5.md`）

---

## 一、本次修订的核心变化

### 1.1 使用最新权威漏洞库

| 项目 | v1.5.0（旧）| v3.4.3（本次）|
|------|------------|--------------|
| 漏洞库来源 | 内置硬编码（3 条）| **OSV.dev 权威源（4 条）** |
| 漏洞更新时间 | 静态 | **实时更新（GitHub Actions 每天）** |
| 漏洞数据准确性 | CVE-2026-54327 误写 `<0.85.0` | **权威数据 `<0.78.1`（修正）** |
| Pi 版本检查 | ❌ 误报漏洞 | ✅ **正确判断** |

### 1.2 权威数据修正（重要）

**之前（内置硬编码）**：
```
CVE-2026-54327: affected <0.85.0 → 0.84.2 被误报为受影响
```

**现在（OSV 权威）**：
```
CVE-2026-54327: affected <0.78.1 → 0.84.2 安全 ✅
```
> 接入权威源后纠正了内置库的错误数据。

---

## 二、總體掃描結果

### 殺手場景決策

```
🚫 [DANGER] 建議：不要安裝
發現 14 個嚴重問題。強烈建議不要安裝此 Skill
```

### 風險儀表板

| 指標 | v1.1.0 | v1.5.0 | **v3.4.3** |
|------|--------|--------|-----------|
| 掃描文件數 | 2112 | 2640 | **2640** |
| 發現問題總數 | 3 | 34 | **34** |
| 🔴 CRITICAL | 1 | 14 | **14** |
| 🟠 HIGH | 2 | 20 | **20** |
| 綜合風險等級 | F | F | **F** |
| 漏洞庫 | 硬編碼 2 | 硬編碼 3 | **OSV 權威 4** |

### 檢測類別覆蓋

| 類別 | 發現數 |
|------|--------|
| 🔑 憑證洩露 | 0 |
| 💀 危險 Shell | 0 |
| 📁 敏感路徑 | 20 |
| 🕵️ Unicode 隱寫 | 0 |
| 🚨 關鍵系統參數 | 14 |
| 💉 提示詞注入 | 0 |
| 🔌 MCP | 0 |

---

## 三、Pi Agent 全局檢查（使用最新漏洞庫）

### 本次結果

```
### Pi 版本
- 檢測到版本: 0.84.2
- 📡 漏洞庫: 4 條（來源: OSV.dev authoritative）
- ✅ 不在已知漏洞範圍

### auth.json 權限
- ✅ Windows ACL 符合安全要求
```

### 最新 4 條 CVE（OSV 權威）

| CVE | 影響版本 | 嚴重度 | 描述 |
|-----|---------|--------|------|
| CVE-2026-54326 | <0.78.1 | medium | XSS in HTML session exports |
| CVE-2026-54328 | <0.78.1 | medium | Predictable temp extension paths |
| CVE-2026-54325 | <0.79.0 | medium | Project-local extensions w/o approval |
| CVE-2026-54327 | <0.78.1 | medium | Race condition in auth.json writes |

> **0.84.2 > 所有修復版本 → 不在漏洞範圍** ✅

---

## 四、🚨 核心發現：自動修改全局 AGENTS.md（14 個 critical_paths）

### 4.1 直接寫入（critical-agents-md-write，3 處）

**文件**: `lib/ensure-subagent-delegation.ts`
```
第257行: writeFileSync(agentsMdPath, `${SUBAGENT_POLICY_BLOCK}\n`, "utf8")
第269行: writeFileSync(agentsMdPath, next, "utf8")
第274行: writeFileSync(agentsMdPath, `${existing}${separator}${SUBAGENT_POLICY_BLOCK}\n`, "utf8")
```

### 4.2 相關函數（implicit-agent-function，9 處）

| 函數 | 文件 |
|------|------|
| ensureAgentsMdPolicy | ensure-subagent-delegation.ts |
| ensureAgentOverride | ensure-subagent-delegation.ts |
| ensureSubagentDelegation | ensure-subagent-delegation.ts |
| syncAgent* / createAgent* / createSubagent* | 多文件 |

### 4.3 影響分析

- 啟動時自動寫入 `~/.pi/agent/AGENTS.md`
- 持久性 / 跨會話 / 跨項目影響
- 靜默（用戶未必知道行為被改變）

### 4.4 緩解建議

| 建議 | 說明 |
|------|------|
| 審查意圖 | 功能是 subagent 委託，非惡意，但應告知用戶 |
| 加開關 | 提供配置選項，默認不修改全局 AGENTS.md |
| 改項目內 | 用項目內 AGENTS.md 而非全局 |

---

## 五、MCP 依賴檢查

```
- MCP 配置文件: 0 個
- MCP 服務器: 0 個
- 工具枚舉: 0 個
```
> pi-web 未包含 MCP 配置文件（無 .mcp.json 等）。

---

## 六、與舊報告對比（v1.5.0 → v3.4.3）

| 維度 | v1.5.0 | v3.4.3 | 變化 |
|------|--------|--------|------|
| 漏洞庫 | 硬編碼 3 條 | **OSV 權威 4 條** | ✅ 更準確 |
| Pi 0.84.2 檢查 | ❌ 誤報 CVE-54327 | ✅ 安全 | ✅ 修正 |
| 掃描範圍 | 本地 clone | 本地 clone + 完整 | 一致 |
| MCP 檢查 | 未做 | ✅ --all 全掃 | ✅ 增強 |
| 發現數 | 34 | 34 | 穩定（規則一致）|
| 誤報 | 0 | 0 | ✅ |

---

## 七、最終結論

### 項目安全性評估

| 場景 | 判斷 |
|------|------|
| 作為普通 Skill 安裝 | ⚠️ 會靜默修改全局 AGENTS.md |
| 本地開發工具 | ✅ 可接受（subagent 委託功能）|
| 無知地自動修改 | ❌ 違反最小權限原則 |

### 給用戶的建議

```
✅ 可以：
  - 本地開發環境使用（了解 AGENTS.md 修改行為）
  - 閱讀 SECURITY_AUDIT.md 了解已知漏洞

⚠️ 建議：
  - 安裝前了解其 AGENTS.md 修改行為
  - 使用前備份 ~/.pi/agent/AGENTS.md

❌ 不要：
  - 生產環境直接運行（SECURITY_AUDIT 有未修復漏洞）
  - 共享機器使用（全局配置影響他人）
```

### 漏洞情報系統對本掃描的價值

1. **糾正了錯誤數據**：CVE-2026-54327 影響版本修正
2. **提供最新依據**：4 條 CVE 全部來自 OSV 權威源
3. **零配置更新**：GitHub Actions 每天自動更新 + 本地 TTL 檢查
4. **多源備援**：OSV → AVID → 加速代理

---

## 八、技術細節

| 項目 | 值 |
|------|-----|
| 工具版本 | skill-safety-guard v3.4.3 |
| 規則數 | 181（9 類）|
| 漏洞庫 | OSV.dev authoritative（4 條）|
| Python | 3.11.15 |
| 掃描方式 | git clone → 完整掃描（--all）|
| 輸出 | Markdown（本報告）|

---

*報告生成時間：2026-08-17 ｜ 漏洞庫更新：2026-08-17 15:49 UTC*

> **聲明**：本掃描為靜態分析，檢測模式層風險。項目意圖的最終判斷需結合人工審查。