> **[CAUTION] 建議：人工複查後決定**
>
> **目標**: `D:\AI\PiAgent\Skill-safety-guard\tests\fixtures\malicious\credential_leak`
> **警告**: 發現 4 個高風險問題。不建議安裝，除非你能解釋每個問題
>
> ---

# Skill Safety-guard 風險報告

> **掃描目標**: `D:\AI\PiAgent\Skill-safety-guard\tests\fixtures\malicious\credential_leak`  
> **掃描文件數**: 8  
> **發現問題數**: 4（🔴 0 | 🟠 4 | 🟡 0 | 🟢 0）

## 綜合風險等級：D

**🟠 較高風險**

---

## 第一層：Pi Agent 全局檢查

### Pi 版本
- **檢測到版本**: `0.84.2`
- ⚠️ 發現 1 個已知漏洞：
  - **CVE-2026-54327** (CRITICAL): 任意文件讀取漏洞：特定 SKILL.md frontmatter 可觸發讀取系統任意文件
    - 💡 升級 Pi 至 0.85.0 或更高版本

### auth.json 權限
- ✅ Windows ACL 符合安全要求（僅 Administrator 有讀寫權限）

---

## 第二層：Skill 內容檢測

### 🔑 憑證洩露
- 掃描文件: 2 個
- 發現問題: 4 個

### 🟠 OpenAI API Key
- **規則 ID**: `cred-openai`
- **嚴重度**: 🟠 HIGH | **置信度**: 🔴 high
- **位置**: `D:\AI\PiAgent\Skill-safety-guard\tests\fixtures\malicious\credential_leak\install.sh:6`
- **命中**: `sk-proj-abc123def456ghi789jkl012mno345pqr678stu901...`
- **說明**: 疑似 OpenAI API Key 洩露
- **建議**: 立即撤銷該密鑰，前往 https://platform.openai.com/api-keys 生成新密鑰

```text
echo "Setting up with key: sk-proj-abc123def456ghi789jkl012mno345pqr678stu901vwx234T3BlbkFJ1234567890abcdefghijklmnopqrstuvwxyz1234"
```

### 🟠 Anthropic API Key
- **規則 ID**: `cred-anthropic`
- **嚴重度**: 🟠 HIGH | **置信度**: 🔴 high
- **位置**: `D:\AI\PiAgent\Skill-safety-guard\tests\fixtures\malicious\credential_leak\install.sh:15`
- **命中**: `sk-ant-api03-1234567890abcdefghijklmnopqrstuvwxyz1...`
- **說明**: 疑似 Anthropic API Key 洩露
- **建議**: 立即撤銷該密鑰，前往 https://console.anthropic.com/settings/keys 生成新密鑰

```text
ant_key="sk-ant-api03-1234567890abcdefghijklmnopqrstuvwxyz1234567890abcdefghijkl"
```

### 🟠 OpenAI API Key
- **規則 ID**: `cred-openai`
- **嚴重度**: 🟠 HIGH | **置信度**: 🔴 high
- **位置**: `D:\AI\PiAgent\Skill-safety-guard\tests\fixtures\malicious\credential_leak\SKILL.md:19`
- **命中**: `sk-proj-abc123def456ghi789jkl012mno345pqr678stu901...`
- **說明**: 疑似 OpenAI API Key 洩露
- **建議**: 立即撤銷該密鑰，前往 https://platform.openai.com/api-keys 生成新密鑰

```text
OPENAI_API_KEY=sk-proj-abc123def456ghi789jkl012mno345pqr678stu901vwx234T3BlbkFJ1234567890abcdefghijklmnopqrstuvwxyz1234
```

### 🟠 OpenAI API Key
- **規則 ID**: `cred-openai`
- **嚴重度**: 🟠 HIGH | **置信度**: 🔴 high
- **位置**: `D:\AI\PiAgent\Skill-safety-guard\tests\fixtures\malicious\credential_leak\SKILL.md:30`
- **命中**: `sk-proj-abc123def456ghi789jkl012mno345pqr678stu901...`
- **說明**: 疑似 OpenAI API Key 洩露
- **建議**: 立即撤銷該密鑰，前往 https://platform.openai.com/api-keys 生成新密鑰

```text
openai.api_key = "sk-proj-abc123def456ghi789jkl012mno345pqr678stu901vwx234T3BlbkFJ1234567890abcdefghijklmnopqrstuvwxyz1234"
```

### 💀 危險 Shell 命令
- 掃描文件: 2 個
- 發現問題: 0 個
- ✅ 未發現問題

### 📁 敏感路徑訪問
- 掃描文件: 2 個
- 發現問題: 0 個
- ✅ 未發現問題

### 🕵️ Unicode 隱寫
- 掃描文件: 2 個
- 發現問題: 0 個
- ✅ 未發現問題

---

## 建議
- ⚠️ 不建議安裝，除非你能解釋每個發現

---

*本報告由 skill-safety-guard v0.1.0 自動生成*  
*規則庫開源：https://github.com/Wahero/Skill-safety-guard/blob/main/src/skill_safety_guard/rules/*  
*發現誤報？執行 `/safety-check --report-fp <rule-id>`*
