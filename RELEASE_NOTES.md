# skill-safety-guard v0.1.0 Release Notes

> 🎉 **首個公開版本！**
> 發布日期：2026-08-17

---

## 📦 簡介

`skill-safety-guard` 是一個**個人開發者安裝 Skill/MCP 前的安全守護者**。與 NVIDIA SkillSpector 等企業級工具不同，本項目專注於：

- 個人開發者工作流
- 對話式觸發（一句話 `/safety-check`）
- 開源規則庫（社區可審計、可貢獻）
- 三層檢查合一（Pi 全局 + Skill + MCP）

---

## ✨ 核心功能（v0.1.0）

### 三大檢測器

| 類別 | 規則數 | 檢出率 | 誤報率 |
|------|--------|--------|--------|
| 🔑 憑證洩露 | 10 | 100% | 0% |
| 💀 危險 Shell 命令 | 12 | 100% | 0% |
| 📁 敏感路徑訪問 | 9 | 100% | 0% |

### Pi Agent 全局檢查

- ✅ **Pi 版本 CVE 檢測**：當前已知 CVE-2026-54326 / CVE-2026-54327
- ✅ **auth.json 權限檢查**：Linux/Mac 用 POSIX、Windows 用 ACL

### 命令支持

```bash
# 默認掃描當前目錄
safety-check

# 掃描指定路徑
safety-check ./my-skill

# 只掃 Pi 全局
safety-check --pi

# JSON 輸出（給其他工具用）
safety-check ./my-skill --output json

# 報告誤報
safety-check --report-fp shell-curl-bash
```

---

## 📊 Phase 0 驗證結果

| 驗證項 | 結果 | 關鍵指標 |
|--------|------|---------|
| V-02 YAML 解析 | ✅ | 100% 正確 |
| V-03 Pi 版本檢測 | ✅ | 提取 `0.84.2` 準確 |
| **V-04 正則檢測** | ✅ | **100% 檢出率 (3/3)** |
| **V-06 誤報基線** | ✅ | **0% 誤報率 (0/5)** |

---

## 🛠️ 安裝

### 方式 1：獨立 CLI

```bash
git clone https://github.com/Wahero/Skill-safety-guard.git
cd Skill-safety-guard
pip install pyyaml
python scripts/safety-check <target>
```

### 方式 2：作為 Pi Skill

```bash
mkdir -p ~/.pi/agent/skills/skill-safety-guard
cp SKILL.md ~/.pi/agent/skills/skill-safety-guard/
ln -s "$(pwd)/src" ~/.pi/agent/skills/skill-safety-guard/src
```

之後在 Pi 對話框輸入 `/safety-check <target>` 即可觸發。

---

## 🐛 已知問題與限制

- **v0.1.0 不支持**：URL 遠端掃描、粘貼式掃描（Phase 1 計劃）
- **v0.1.0 不支持**：Unicode 隱寫檢測（Phase 2 計劃）
- **v0.1.0 不支持**：規則版提示詞注入檢測（Phase 2 計劃）
- **Windows ACL 檢測**：依賴 `icacls` 命令（已內建）

---

## 🤝 貢獻

- 提交 Bug：[Issue Tracker](https://github.com/Wahero/Skill-safety-guard/issues)
- 報告誤報：[False Positive Report](https://github.com/Wahero/Skill-safety-guard/issues/new?template=false_positive.md)
- 新增規則：見 [CONTRIBUTING.md](CONTRIBUTING.md)
- 文檔改進：歡迎 PR

---

## 📜 許可證

[MIT License](LICENSE)

---

## 🙏 致謝

- [OWASP AST10 (2026)](https://owasp.org) —— 行業威脅標準
- [MoltCheck](https://molt.bot) —— Freemium 商業模式參考
- [mcp-security-audit](https://github.com/) —— MCP 檢測邏輯參考
- [ClawHavoc 攻擊報告 (TrendMicro, 2026)](https://www.trendmicro.com/) —— 真實威脅數據

---

## 🔮 路線圖

| 版本 | 時間 | 主要內容 |
|------|------|---------|
| **v0.1.0** | ✅ 今天 | Phase 0 + 基礎 MVP |
| v1.0 | 2026-09 | URL/粘貼掃描 + 完整 P0 |
| v2.0 | 2026-10 | Unicode + 規則版提示詞注入 |
| v3.0 | 2026-12 | Freemium + Pro 訂閱 |

完整規劃見 [`docs/PRD_v4_聚焦个人开发者版.MD`](docs/PRD_v4_聚焦个人开发者版.MD)。

---

⭐ **如果覺得有幫助，給個 Star！**