# Contributing to skill-safety-guard

> **歡迎參與 skill-safety-guard 的開發！**
> 本文檔介紹如何貢獻代碼、新規則、修復 Bug。

---

## 快速開始

```bash
# 1. Fork 本倉庫
# 2. 克隆你的 fork
git clone https://github.com/<your-name>/Skill-safety-guard.git
cd Skill-safety-guard

# 3. 安裝依賴（推薦虛擬環境）
python -m venv .venv
source .venv/bin/activate  # Mac/Linux
.venv\Scripts\activate     # Windows
pip install pyyaml

# 4. 運行測試確保一切正常
python tests/test_phase0.py

# 5. 創建你的功能分支
git checkout -b feature/your-feature
```

---

## 貢獻類型

### 1. 新增檢測規則（最常見）

規則定義在 `rules/` 目錄的 YAML 文件中。

#### 規則格式

```yaml
- id: your-rule-id              # 唯一 ID，kebab-case
  name: Human Readable Name      # 給用戶顯示
  pattern: "regex_pattern_here"   # Python 正則表達式
  severity: critical            # critical / high / medium / low
  confidence: high              # high / medium / low
  category: credentials         # credentials / shell / paths / your-category
  description: 規則描述         # 一句話解釋
  remediation: 修復建議          # 給用戶的具體行動
```

#### YAML 注意事項

正則字符串必須用**雙引號**包裹，反斜杠雙寫：

```yaml
# 正確
pattern: "sk-[A-Za-z0-9]{40,}"
pattern: "curl\\s+[^|]*\\|\\s*sh"

# 錯誤（單引號會被 YAML 解析吃掉）
pattern: 'sk-[A-Za-z0-9]{40,}'
pattern: 'curl\s+[^|]*\|\s*sh'
```

#### 貢獻流程

1. **選擇正確的文件**：
   - `rules/credentials.yaml` —— API key、私鑰
   - `rules/dangerous_shell.yaml` —— 危險 Shell 命令
   - `rules/sensitive_paths.yaml` —— 敏感路徑訪問
   - 或新建文件（如 `rules/prompt_injection.yaml`）

2. **創建測試 fixture**：
   ```bash
   mkdir -p tests/fixtures/malicious/your-rule-name
   echo "觸發新規則的內容" > tests/fixtures/malicious/your-rule-name/test.txt
   ```

3. **驗證你的規則能工作**：
   ```bash
   python scripts/safety-check tests/fixtures/malicious/your-rule-name
   ```

4. **運行完整測試套件**：
   ```bash
   python tests/test_phase0.py
   ```

5. **提交 PR**：
   - 規則 ID 必須唯一
   - 必須包含至少 1 個能觸發的惡意樣本
   - 必須包含對應的乾淨樣本（避免誤報）

#### 規則設計原則

✅ **好的規則**：
- 誤報率低（< 5%）
- 高置信度
- 易於理解
- 有明確的補救建議

❌ **避免**：
- 過於寬鬆（如 `password` 任意字符串）
- 過於狹窄（如特定公司專用格式，除非社區共用）
- 與已有規則重疊

---

### 2. 修復誤報

**流程**：

1. 確認誤報：運行檢測找出命中規則
   ```bash
   python scripts/safety-check <your-skill> --output json
   ```

2. 在 `rules/whitelist.yaml` 中添加白名單條目：
   ```yaml
   whitelisted_patterns:
     - rule_id: rule-that-misfires
       pattern: "your-specific-text-to-whitelist"
       reason: 文檔示例中的占位符
   ```

3. 或者在 `rules/whitelist.yaml` 中降低置信度：
   ```yaml
   confidence_demotions:
     - rule_id: rule-that-misfires
       context: "特定上下文標記"
       new_confidence: low
       reason: 在該上下文中可能是誤報
   ```

4. 驗證：重新運行檢測，確認不再誤報

---

### 3. 修復 Bug / 新增功能

請先創建 issue 討論，再提交 PR。

**提交前檢查清單**：

- [ ] 代碼遵循 PEP 8
- [ ] 函數有 docstring
- [ ] 新增功能有測試
- [ ] 現有測試仍然通過
- [ ] 提交信息清晰（建議用 Conventional Commits）
- [ ] PR 描述說明改動動機和測試方法

---

## 開發環境

### Python 版本

- Python ≥ 3.8
- 推薦 Python 3.11+

### 依賴

| 依賴 | 用途 |
|------|------|
| `pyyaml` | YAML 規則加載 |
| `pytest` | 測試（推薦） |
| `pre-commit` | 代碼質量（推薦） |

### 目錄結構

```
skill-safety-guard/
├── src/skill_safety_guard/    # 核心代碼
│   ├── detectors/             # 三類檢測器
│   ├── pi_check/              # Pi Agent 全局檢查
│   ├── cli.py                 # CLI 入口
│   ├── parser.py              # YAML 解析
│   └── reporter.py            # 報告生成
├── rules/                     # 檢測規則（YAML）
├── tests/
│   ├── fixtures/
│   │   ├── malicious/         # 應觸發的樣本
│   │   └── clean/             # 不應觸發的樣本
│   └── test_phase0.py         # 自動化測試
├── docs/                      # 文檔
├── scripts/                   # 輔助腳本
└── pyproject.toml
```

---

## 測試要求

### 單元測試

每個新檢測器應有對應的測試：

```python
def test_your_detector():
    from skill_safety_guard.detectors.your_detector import YourDetector
    detector = YourDetector(rules=[])
    findings = detector.detect_file(Path("test.md"), "test content")
    assert len(findings) > 0
```

### 集成測試

修改核心代碼後，必須運行 Phase 0 測試：

```bash
python tests/test_phase0.py
```

所有測試必須通過，**且檢出率不能低於現版本**。

---

## 提交約定

### Commit 格式

使用 [Conventional Commits](https://www.conventionalcommits.org/)：

```
<type>(<scope>): <subject>

<body>

<footer>
```

類型：
- `feat` —— 新功能
- `fix` —— Bug 修復
- `docs` —— 文檔變更
- `style` —— 代碼格式（無功能影響）
- `refactor` —— 重構
- `test` —— 測試變更
- `chore` —— 構建/工具變更

範例：
```
feat(rules): add Slack token detection

Add new rule cred-slack-pro to identify Slack Pro tokens
in format xoxp-XXXX-XXXX-XXXX-XXXX.

Detection covers workspace tokens used for full Slack app
integration.

Closes #123
```

### PR 流程

1. 從 `main` 分支創建新分支
2. 提交 PR 到 `main`
3. 等待 CI 通過
4. 等待至少 1 位 reviewer approve
5. Squash merge

---

## 行為準則

- ✅ 尊重所有貢獻者
- ✅ 提供建設性反饋
- ✅ 聚焦技術討論
- ❌ 拒絕人身攻擊
- ❌ 拒絕無關政治討論

詳見 [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)。

---

## 問題反饋

- **Bug**：[GitHub Issues](https://github.com/Wahero/Skill-safety-guard/issues/new?template=bug_report.md)
- **誤報**：[False Positive Report](https://github.com/Wahero/Skill-safety-guard/issues/new?template=false_positive.md)
- **功能建議**：[GitHub Discussions](https://github.com/Wahero/Skill-safety-guard/discussions)

---

## 許可證

貢獻的代碼將以 MIT 許可證發布。

---

*最後更新：2026-08-17 (v0.1.0)*