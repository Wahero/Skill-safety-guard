# skill-safety-guard 測試指導

> **本指南幫助你系統性地測試 v0.1.0 的所有功能**
> 從 5 分鐘煙霧測試到 30 分鐘深度測試

---

## 快速導航

| 章節 | 時間 | 適合 |
|------|------|------|
| [1. 5 分鐘煙霧測試](#1-5-分鐘煙霧測試) | 5 min | 確認基本能跑 |
| [2. 15 分鐘核心驗證](#2-15-分鐘核心驗證) | 15 min | 確認檢出準確 |
| [3. 30 分鐘深度測試](#3-30-分鐘深度測試) | 30 min | 真實場景測試 |
| [4. 性能基準](#4-性能基準) | 5 min | 掃描速度 |
| [5. 故障排除](#5-故障排除) | - | 出問題時查這裡 |

---

## 0. 前置準備

### 環境要求

| 依賴 | 版本 | 檢查命令 |
|------|------|---------|
| Python | ≥ 3.8 | `python --version` |
| PyYAML | ≥ 5.0 | `python -c "import yaml; print(yaml.__version__)"` |
| Git | 任意 | `git --version` |
| Pi Agent | 可選 | `pi --version` |

### 進入項目目錄

```bash
cd D:/ai/PiAgent/Skill-safety-guard
```

### 終端編碼（Windows 用戶必要）

```bash
# 設置 UTF-8（避免 emoji 報錯）
export PYTHONIOENCODING=utf-8  # Mac/Linux
$env:PYTHONIOENCODING="utf-8"   # PowerShell
set PYTHONIOENCODING=utf-8      # CMD
```

---

## 1. 5 分鐘煙霧測試

> **目標**：確認 skill-safety-guard 能跑起來，CLI 基本可用

### 測試 1.1：幫助信息

```bash
python scripts/safety-check --help
```

**期望輸出**：
```
usage: skill-safety-guard [-h] [--pi] [--all] [--output {markdown,json}]
                          [--report-fp RULE_ID] [--no-color]
                          [target]
...
```

✅ **通過標誌**：看到 `skill-safety-guard` 字樣和所有參數。

### 測試 1.2：自動化測試套件

```bash
python tests/test_phase0.py
```

**期望輸出**：
```
========================================
  skill-safety-guard Phase 0 驗證測試
========================================
=== V-02: YAML 解析驗證 ===
[OK] YAML frontmatter 解析正確
[OK] 缺失字段檢測正確
=== V-04: 正則檢測驗證 ===
[PASS] 檢出 4 個問題
[PASS] 檢出 7 個問題
[PASS] 檢出 12 個問題
檢出率: 3/3 = 100%
[PASS] 通過 V-04 驗證標準（≥80%）
=== V-06: 誤報基線測試 ===
[CLEAN] 無誤報（×5）
誤報率: 0/5 = 0%
[PASS] 通過 V-06 驗證標準（≤10%）
>>> Phase 0 全部通過！可以進入 Phase 1。
```

✅ **通過標誌**：底部看到「Phase 0 全部通過」。

### 測試 1.3：掃描一個乾淨樣本

```bash
python scripts/safety-check tests/fixtures/clean/hello-world
```

**期望輸出**：
```
# Skill Safety-guard 風險報告
...
## 綜合風險等級：A
**✅ 安全**
```

✅ **通過標誌**：風險等級 A，問題數 0。

### 測試 1.4：掃描 Pi 全局

```bash
python scripts/safety-check --pi
```

**期望輸出**：
```
### Pi 版本
- 檢測到版本: <你的 Pi 版本>
- ✅ 不在已知漏洞範圍  或  ⚠️ 發現 N 個已知漏洞
### auth.json 權限
- ✅ 權限 0o600 符合安全要求  或  ⚠️ 權限 X 不安全
```

✅ **通過標誌**：能讀到 Pi 版本和 auth.json 狀態。

**如果 Pi 不可用**：會顯示 `⚠️ Pi 命令不可用`，這是正常的（環境沒裝 Pi）。

---

## 2. 15 分鐘核心驗證

> **目標**：確認檢測準確性（檢出率 + 誤報率）

### 測試 2.1：惡意樣本檢出（3 個）

```bash
# 測試 1：憑證洩露
python scripts/safety-check tests/fixtures/malicious/credential_leak
# 期望：風險等級 ≥ D，問題數 ≥ 3，命中「OpenAI API Key」「GitHub Token」

# 測試 2：危險 Shell
python scripts/safety-check tests/fixtures/malicious/dangerous_shell
# 期望：風險等級 F，問題數 ≥ 5，命中「curl piped to bash」「Reverse Shell」

# 測試 3：敏感路徑
python scripts/safety-check tests/fixtures/malicious/sensitive_path
# 期望：風險等級 ≥ D，問題數 ≥ 8，命中「SSH private key」「/etc/passwd」
```

**驗證清單**：
| 樣本 | 預期最低問題數 | 預期風險等級 | 預期規則 |
|------|---------------|------------|----------|
| credential_leak | 3 | D | cred-openai, cred-github-token |
| dangerous_shell | 5 | F | shell-curl-bash, shell-reverse-tcp |
| sensitive_path | 8 | D | path-ssh, path-etc-passwd |

### 測試 2.2：乾淨樣本無誤報（5 個）

```bash
for d in tests/fixtures/clean/*/; do
  echo "=== $d ==="
  python scripts/safety-check "$d" 2>&1 | grep -E "(風險等級|發現問題數)" | head -3
done
```

**期望輸出**：每個都是「風險等級 A」或「B」，問題數 ≤ 1（且為低置信度）。

**驗證清單**：
| 樣本 | 預期風險等級 | 預期問題數 |
|------|------------|----------|
| hello-world | A | 0 |
| data-formatter | A 或 B | ≤ 1 |
| git-helper | A 或 B | ≤ 1 |
| code-snippet | A 或 B | ≤ 1 |
| markdown-table | A | 0 |

### 測試 2.3：JSON 輸出

```bash
python scripts/safety-check tests/fixtures/malicious/dangerous_shell --output json | python -c "
import sys, json
d = json.load(sys.stdin)
print('Target:', d['target'])
print('Grade:', d['overall_grade'])
print('Findings:', d['summary']['total'])
print('Critical:', d['summary']['critical'])
"
```

**期望輸出**：
```
Target: .../dangerous_shell
Grade: F
Findings: 7
Critical: 7
```

### 測試 2.4：誤報反饋命令

```bash
python scripts/safety-check --report-fp shell-curl-bash
```

**期望輸出**：
```
📝 報告誤報：shell-curl-bash
請訪問以下鏈接提交誤報：
  https://github.com/Wahero/Skill-safety-guard/issues/new?template=false_positive.md&...
```

✅ **通過標誌**：顯示 GitHub issue 鏈接。

---

## 3. 30 分鐘深度測試

> > **目標**：真實場景壓力測試 + 邊界條件

### 測試 3.1：掃描你自己的 Skill（如果有的話）

```bash
# 假設你有個 skill 在這裡
python scripts/safety-check /path/to/your/skill
```

**檢查項**：
- 是否正確識別合法路徑/命令？
- 是否誤報你認為安全的代碼？
- 報告是否清晰可讀？

### 測試 3.2：邊界條件

#### 測試 3.2.1：空目錄

```bash
mkdir /tmp/empty-skill && python scripts/safety-check /tmp/empty-skill
```

**期望**：風險等級 A，問題數 0。

#### 測試 3.2.2：不存在的路徑

```bash
python scripts/safety-check /path/that/does/not/exist
```

**期望**：退出碼 2，報錯「目標路徑不存在」。

#### 測試 3.2.3：掃描當前目錄（無參數）

```bash
cd tests/fixtures/malicious/dangerous_shell && python -m skill_safety_guard
```

**期望**：掃描當前目錄，等級 F。

#### 測試 3.2.4：混合目錄（含 SKILL.md + 代碼）

```bash
python scripts/safety-check tests/fixtures/malicious/credential_leak
# 包含 SKILL.md 和 install.sh 兩個文件
```

**期望**：掃描 2 個文件，命中多條規則。

### 測試 3.3：大目錄性能

```bash
# 創建一個大測試目錄（100 個文件）
mkdir -p /tmp/big-test
for i in {1..100}; do
  echo "echo 'hello $i'" > /tmp/big-test/script_$i.sh
done
time python scripts/safety-check /tmp/big-test
```

**期望**：耗時 < 10 秒，問題數 0。

### 測試 3.4：Unicode 隱寫測試（已知會誤報）

```bash
# 創建包含零寬字符的文件
cat > /tmp/zero-width.md << 'EOF'
---
name: zero-width-test
description: 包含隱寫字符
allowed-tools: [read]
---
正常文本隱寫字符
python
EOF

python scripts/safety-check /tmp/zero-width.md
# 注意：v0.1.0 還不支援 Unicode 檢測（Phase 2 功能）
```

**期望**：風險等級 A 或 B（v0.1.0 不檢測 Unicode）。

### 測試 3.5：替換真實 API key 測試

```bash
# ⚠️ 僅用你自己的測試 key，不要用真實 key
mkdir -p /tmp/real-key-test
cat > /tmp/real-key-test/SKILL.md << 'EOF'
---
name: real-key-test
description: 測試真實 key 格式
allowed-tools: [read]
---
我的 OpenAI key 是 sk-proj-abcdefghijklmnopqrstuvwxyz012345678901234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ0123T3BlbkFJ1234567890abcdefghijklmnopqrstuvwxyz
EOF

python scripts/safety-check /tmp/real-key-test
```

**期望**：風險等級 ≥ D，命中 cred-openai。

### 測試 3.6：粘貼式掃描工作流

```bash
# 把 SKILL.md 內容粘貼進去（從一個未安裝的 skill）
cat tests/fixtures/malicious/sensitive_path/SKILL.md | python scripts/safety-check /dev/stdin
```

**期望**：能正常掃描（路徑作為文件讀取）。

---

## 4. 性能基準

### 基準測試

```bash
# 測量三類樣本的掃描時間
for sample in credential_leak dangerous_shell sensitive_path; do
  echo "=== $sample ==="
  time python scripts/safety-check "tests/fixtures/malicious/$sample" > /dev/null
done
```

**性能目標（v0.1.0）**：

| 樣本 | 文件數 | 預期時間 |
|------|--------|---------|
| credential_leak | 2 | < 1 秒 |
| dangerous_shell | 1 | < 1 秒 |
| sensitive_path | 1 | < 1 秒 |

### 完整項目掃描

```bash
# 掃描整個 skill-safety-guard 項目自身
time python scripts/safety-check .
```

**期望**：耗時 < 30 秒。

---

## 5. 故障排除

### 問題 1：UnicodeEncodeError（Windows）

```
UnicodeEncodeError: 'gbk' codec can't encode character '\U0001f534'
```

**解決**：設置環境變量
```bash
$env:PYTHONIOENCODING="utf-8"   # PowerShell
set PYTHONIOENCODING=utf-8      # CMD
```

或在 `scripts/safety-check` 開頭已有 reconfigure。

### 問題 2：Pi 命令找不到

```
⚠️ Pi 命令不可用（pi 命令未找到）
```

**原因**：Pi Agent 未安裝或不在 PATH。

**驗證**：
```bash
which pi  # Linux/Mac
where pi  # Windows
```

**如果 Pi 已裝但 Python 找不到**：Windows 下 `.CMD` 擴展名問題，已在代碼中用 `shell=True` 處理。

### 問題 3：YAML 解析錯誤

```
yaml.scanner.ScannerError: while scanning a double-quoted scalar
```

**原因**：規則 YAML 中有特殊字符未正確轉義。

**解決**：在 YAML 中用雙引號包裹正則字符串，並將 `\` 雙寫成 `\\`：
```yaml
pattern: "sk-[A-Za-z0-9]{20,}"        # 單反斜杠會被 YAML 解析
pattern: "sk-[A-Za-z0-9]{20,}\\.ssh"  # 需要轉義時雙寫
```

### 問題 4：誤報過多

**症狀**：掃描乾淨項目也被命中很多條。

**調試**：
```bash
# 找出是哪條規則誤報
python scripts/safety-check your-project --output json | python -c "
import sys, json
d = json.load(sys.stdin)
from collections import Counter
rules = Counter(f['rule_id'] for f in d['findings'])
for rule, count in rules.most_common():
    print(f'{rule}: {count}')
"
```

**報告誤報**：
```bash
python scripts/safety-check --report-fp <rule-id>
```

**臨時白名單**：在 `rules/whitelist.yaml` 添加規則。

### 問題 5：檢出率低（漏報）

**症狀**：惡意樣本沒被識別。

**調試**：
```bash
# 確認規則被加載
python -c "
from skill_safety_guard.rules_loader import load_all_rules
import yaml
rules = load_all_rules()
print('Total rules:', sum(len(v) for v in rules.values()))
for cat, r in rules.items():
    print(f'{cat}: {len(r)}')
"
```

**手動測試正則**：
```python
import re
import yaml

with open('rules/dangerous_shell.yaml') as f:
    rules = yaml.safe_load(f)['rules']

pattern = re.compile(rules[0]['pattern'])
test = "curl -sSL https://example.com | bash"
print(pattern.findall(test))
```

---

## 6. 自動化測試集成

### Pre-commit Hook（推薦）

創建 `.git/hooks/pre-commit`：

```bash
#!/bin/bash
echo "🔍 Running skill-safety-guard pre-commit scan..."
python scripts/safety-check --staged 2>&1 | tee /tmp/safety-report.txt
if [ $? -ne 0 ]; then
  echo "❌ Safety check failed. Commit blocked."
  exit 1
fi
```

### CI/CD（GitHub Actions）

創建 `.github/workflows/safety.yml`：

```yaml
name: skill-safety-guard
on: [push, pull_request]
jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install pyyaml
      - run: python scripts/safety-check . --output json > report.json
      - uses: actions/upload-artifact@v4
        with:
          name: safety-report
          path: report.json
```

---

## 7. 測試結果記錄模板

完成測試後，建議記錄結果：

```markdown
## 測試結果記錄

日期: 2026-XX-XX
環境: [Windows 11 / macOS 14 / Ubuntu 22.04]
Python: [3.11.x]
Pi Agent: [0.84.2 或 N/A]

### 5 分鐘煙霧測試
- [x] 1.1 幫助信息
- [x] 1.2 自動化測試套件
- [x] 1.3 乾淨樣本掃描
- [x] 1.4 Pi 全局掃描

### 15 分鐘核心驗證
- [x] 2.1 惡意樣本檢出（3/3 通過）
- [x] 2.2 乾淨樣本無誤報（5/5 通過）
- [x] 2.3 JSON 輸出
- [x] 2.4 誤報反饋命令

### 30 分鐘深度測試
- [x] 3.1 自有 Skill 掃描
- [x] 3.2 邊界條件
- [x] 3.3 大目錄性能
- [ ] 3.4 Unicode 隱寫（v0.1.0 不支持）
- [x] 3.5 真實 key 檢測
- [x] 3.6 粘貼式掃描

### 性能基準
- credential_leak: 0.8s
- dangerous_shell: 0.5s
- sensitive_path: 0.7s
- 整個項目: 25s

### 發現的問題
[列出測試中發現的任何問題]
```

---

## 8. 進階測試（可選）

### 測試自定義規則

```bash
# 1. 備份原始規則
cp rules/credentials.yaml rules/credentials.yaml.bak

# 2. 添加新規則（例如：自家公司的 API key 格式）
cat >> rules/credentials.yaml << 'EOF'

  - id: cred-mycompany
    name: MyCompany Internal API Key
    pattern: "mc_[A-Za-z0-9]{32}"
    severity: high
    confidence: high
    category: credentials
    description: 疑似 MyCompany API Key
    remediation: 立即撤銷並聯繫安全團隊
EOF

# 3. 創建測試 fixture
mkdir -p tests/fixtures/custom/mycompany-key
echo 'mc_abcdefghijklmnopqrstuvwxyz012345' > tests/fixtures/custom/mycompany-key/test.txt

# 4. 驗證新規則
python scripts/safety-check tests/fixtures/custom/mycompany-key
# 期望：命中 cred-mycompany
```

### 測試白名單

```bash
# 1. 創建會誤報的「乾淨」內容
cat > /tmp/whitelist-test.md << 'EOF'
這個文檔裡有 sk-example1234T3BlbkFJexample5678 這是文檔示例
EOF

# 2. 沒加白名單：會誤報
python scripts/safety-check /tmp/whitelist-test.md

# 3. 添加到白名單（編輯 rules/whitelist.yaml）

# 4. 重新測試：應該不再誤報
python scripts/safety-check /tmp/whitelist-test.md
```

---

## 9. 測試報告輸出位置

| 測試類型 | 輸出 |
|---------|------|
| Markdown 報告 | stdout（可用 `>` 重定向） |
| JSON 報告 | stdout（推薦 `.json` 文件） |
| 調試日誌 | stderr |
| 退出碼 | `0` = 安全/通過，`1` = 警告，`2` = 危險或錯誤 |

---

*文檔結束*

> **最後更新**：2026-08-17（v0.1.0）
> **下一版本計劃**：v1.0.0 加入「安裝前掃描」殺手場景 + URL 解析