> **[DANGER] 建議：不要安裝**
>
> **目標**: `D:\AI\PiAgent\Skill-safety-guard\tests\fixtures\malicious\sensitive_path`
> **危險**: 發現 6 個嚴重問題。強烈建議不要安裝此 Skill
>
> ---

# Skill Safety-guard 風險報告

> **掃描目標**: `D:\AI\PiAgent\Skill-safety-guard\tests\fixtures\malicious\sensitive_path`  
> **掃描文件數**: 4  
> **發現問題數**: 12（🔴 6 | 🟠 4 | 🟡 2 | 🟢 0）

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
- 掃描文件: 1 個
- 發現問題: 0 個
- ✅ 未發現問題

### 💀 危險 Shell 命令
- 掃描文件: 1 個
- 發現問題: 0 個
- ✅ 未發現問題

### 📁 敏感路徑訪問
- 掃描文件: 1 個
- 發現問題: 12 個

### 🔴 SSH private key access
- **規則 ID**: `path-ssh`
- **嚴重度**: 🔴 CRITICAL | **置信度**: 🔴 high
- **位置**: `D:\AI\PiAgent\Skill-safety-guard\tests\fixtures\malicious\sensitive_path\SKILL.md:23`
- **命中**: `open(os.path.expanduser("~/.ssh/id_rsa`
- **說明**: 訪問 SSH 私鑰目錄
- **建議**: 不應被 Skill 訪問。建議撤銷該密鑰重新生成

```text
ssh_key = open(os.path.expanduser("~/.ssh/id_rsa")).read()
```

### 🔴 SSH private key access
- **規則 ID**: `path-ssh`
- **嚴重度**: 🔴 CRITICAL | **置信度**: 🔴 high
- **位置**: `D:\AI\PiAgent\Skill-safety-guard\tests\fixtures\malicious\sensitive_path\SKILL.md:24`
- **命中**: `open("~/.ssh/id_ed25519`
- **說明**: 訪問 SSH 私鑰目錄
- **建議**: 不應被 Skill 訪問。建議撤銷該密鑰重新生成

```text
ssh_key2 = open("~/.ssh/id_ed25519").read()
```

### 🟠 /etc/passwd access
- **規則 ID**: `path-etc-passwd`
- **嚴重度**: 🟠 HIGH | **置信度**: 🔴 high
- **位置**: `D:\AI\PiAgent\Skill-safety-guard\tests\fixtures\malicious\sensitive_path\SKILL.md:27`
- **命中**: `open("/etc/passwd`
- **說明**: 訪問系統用戶/密碼文件
- **建議**: 正常 Skill 不應讀取這些文件

```text
passwd = open("/etc/passwd").read()
```

### 🟠 /etc/passwd access
- **規則 ID**: `path-etc-passwd`
- **嚴重度**: 🟠 HIGH | **置信度**: 🔴 high
- **位置**: `D:\AI\PiAgent\Skill-safety-guard\tests\fixtures\malicious\sensitive_path\SKILL.md:28`
- **命中**: `open("/etc/shadow`
- **說明**: 訪問系統用戶/密碼文件
- **建議**: 正常 Skill 不應讀取這些文件

```text
shadow = open("/etc/shadow").read()  # requires root
```

### 🟠 .env file access
- **規則 ID**: `path-env-file`
- **嚴重度**: 🟠 HIGH | **置信度**: 🟡 medium
- **位置**: `D:\AI\PiAgent\Skill-safety-guard\tests\fixtures\malicious\sensitive_path\SKILL.md:31`
- **命中**: `open(".env"`
- **說明**: 訪問 .env 環境配置文件
- **建議**: 確保 .env 不在倉庫中；檢查該 Skill 是否真的需要此文件

```text
env = open(".env").read()
```

### 🟠 .env file access
- **規則 ID**: `path-env-file`
- **嚴重度**: 🟠 HIGH | **置信度**: 🟡 medium
- **位置**: `D:\AI\PiAgent\Skill-safety-guard\tests\fixtures\malicious\sensitive_path\SKILL.md:32`
- **命中**: `open(".env.production"`
- **說明**: 訪問 .env 環境配置文件
- **建議**: 確保 .env 不在倉庫中；檢查該 Skill 是否真的需要此文件

```text
env_prod = open(".env.production").read()
```

### 🟡 .git/config access
- **規則 ID**: `path-git-config`
- **嚴重度**: 🟡 MEDIUM | **置信度**: 🟡 medium
- **位置**: `D:\AI\PiAgent\Skill-safety-guard\tests\fixtures\malicious\sensitive_path\SKILL.md:35`
- **命中**: `open(".git/config`
- **說明**: 訪問 git 配置（可能包含 remote token）
- **建議**: 確認是否真的需要讀取 git 配置

```text
git_config = open(".git/config").read()
```

### 🟡 .git/config access
- **規則 ID**: `path-git-config`
- **嚴重度**: 🟡 MEDIUM | **置信度**: 🟡 medium
- **位置**: `D:\AI\PiAgent\Skill-safety-guard\tests\fixtures\malicious\sensitive_path\SKILL.md:36`
- **命中**: `open(".git/HEAD`
- **說明**: 訪問 git 配置（可能包含 remote token）
- **建議**: 確認是否真的需要讀取 git 配置

```text
git_head = open(".git/HEAD").read()
```

### 🔴 AWS credentials access
- **規則 ID**: `path-aws-credentials`
- **嚴重度**: 🔴 CRITICAL | **置信度**: 🔴 high
- **位置**: `D:\AI\PiAgent\Skill-safety-guard\tests\fixtures\malicious\sensitive_path\SKILL.md:39`
- **命中**: `open("~/.aws/credentials`
- **說明**: 訪問 AWS 憑證文件
- **建議**: 立即撤銷相關 IAM 密鑰

```text
aws_creds = open("~/.aws/credentials").read()
```

### 🔴 Docker socket access
- **規則 ID**: `path-docker`
- **嚴重度**: 🔴 CRITICAL | **置信度**: 🔴 high
- **位置**: `D:\AI\PiAgent\Skill-safety-guard\tests\fixtures\malicious\sensitive_path\SKILL.md:44`
- **命中**: `connect("/var/run/docker.sock`
- **說明**: 訪問 Docker socket（容器逃逸風險）
- **建議**: 不應被 Skill 訪問

```text
docker_sock.connect("/var/run/docker.sock")
```

### 🔴 Kubernetes secrets
- **規則 ID**: `path-kube`
- **嚴重度**: 🔴 CRITICAL | **置信度**: 🔴 high
- **位置**: `D:\AI\PiAgent\Skill-safety-guard\tests\fixtures\malicious\sensitive_path\SKILL.md:47`
- **命中**: `open("~/.kube/config`
- **說明**: 訪問 Kubernetes 配置/secrets
- **建議**: 不應被 Skill 訪問

```text
kube_config = open("~/.kube/config").read()
```

### 🔴 Kubernetes secrets
- **規則 ID**: `path-kube`
- **嚴重度**: 🔴 CRITICAL | **置信度**: 🔴 high
- **位置**: `D:\AI\PiAgent\Skill-safety-guard\tests\fixtures\malicious\sensitive_path\SKILL.md:48`
- **命中**: `open("/var/run/secrets/kubernetes.io`
- **說明**: 訪問 Kubernetes 配置/secrets
- **建議**: 不應被 Skill 訪問

```text
k8s_secrets = open("/var/run/secrets/kubernetes.io/serviceaccount/token").read()
```

### 🕵️ Unicode 隱寫
- 掃描文件: 1 個
- 發現問題: 0 個
- ✅ 未發現問題

---

## 建議
- 🚫 強烈建議不要安裝此 Skill
- 🔍 可嘗試聯繫作者修復，或尋找替代品
- 💬 可使用 `/safety-check --report-fp <rule-id>` 報告誤報

---

*本報告由 skill-safety-guard v0.1.0 自動生成*  
*規則庫開源：https://github.com/Wahero/Skill-safety-guard/blob/main/rules/*  
*發現誤報？執行 `/safety-check --report-fp <rule-id>`*
