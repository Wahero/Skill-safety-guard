# skill-safety-guard Demo 指南

> **如何向社區展示這個工具**
> 本目錄包含完整的展示材料和示例輸出

---

## 📦 包含什麼

```
demo/
├── DEMO.md                 # 本文件（展示指南）
├── index.html              # 互動式 HTML 展示頁面（深色主題）
├── generate_samples.sh     # 自動生成所有示例輸出
└── outputs/                # 真實掃描輸出（運行腳本後生成）
```

---

## 🎯 三種展示方式

### 方式 1：HTML 展示頁面（推薦）

適合在 Twitter / Reddit / 社區論壇貼鏈接：

1. 打開 `index.html` 在瀏覽器中查看
2. 包含：
   - 工作流圖解
   - 3 個真實示例（危險 Shell / Unicode 隱寫 / 乾淨樣本）
   - 與 NVIDIA SkillSpector 等對比表
   - 試用代碼片段

**部署到 GitHub Pages**：
- 1. 把 `index.html` 移到 `docs/index.html`
- 2. 在 repo Settings → Pages 啟用
- 3. 訪問 `https://wahero.github.io/Skill-safety-guard/`

### 方式 2：命令行示例（適合開發者）

運行 `generate_samples.sh` 生成所有真實掃描輸出：

```bash
cd demo
./generate_samples.sh
```

生成的 6 個 Markdown 報告：
- `01-pi-global.md` —— Pi 全局檢查
- `02-malicious-shell.md` —— 危險 Shell 檢測（Grade F）
- `03-credential-leak.md` —— 憑證洩露檢測（Grade D）
- `04-sensitive-path.md` —— 敏感路徑檢測（Grade F）
- `05-unicode-stego.md` —— Unicode 隱寫檢測（Grade F）
- `06-clean-sample.md` —— 乾淨樣本（Grade A）

### 方式 3：Twitter / 短文推廣

精簡版推廣文案（280 字符以內）：

```
🛡️ 開源了 skill-safety-guard v1.0！

個人開發者安裝 Skill 前的安全守護者。
3 行命令檢測 5 大類威脅：
  • 憑證洩露
  • 危險 Shell 命令
  • 敏感路徑訪問
  • Unicode 隱寫（v2.0 新功能）
  • Pi Agent 全局漏洞

殺手場景：/safety-check <github-url>，5 秒出結果。

https://github.com/Wahero/Skill-safety-guard

#AI #Security #OpenSource
```

---

## 🎬 社區發布 checklist

### 發布前

- [ ] 運行 `./generate_samples.sh` 確保所有示例可用
- [ ] 在瀏覽器打開 `index.html` 預覽展示頁
- [ ] 檢查所有鏈接可訪問

### 發布渠道

| 渠道 | 內容 | 時機 |
|------|------|------|
| **GitHub Release v1.0.0** | 完整 CHANGELOG + | 立即 |
| **Twitter** | 280 字推廣 + 截圖 | v1.0.0 發布當天 |
| **Reddit r/LocalLLaMA** | "I built a security scanner for AI Skills" | 發布後 1-2 天 |
| **V2EX** | "開源了 Skill 安全掃描工具" | 發布當天 |
| **Hacker News** | Show HN: skill-safety-guard | 發布當天（需準備英文版） |
| **Pi Agent 社區** | Skill 介紹帖 | 發布當天 |

### 發布後

- [ ] 回覆社區評論（24 小時內）
- [ ] 處理第一波 Bug 報告
- [ ] 統計 GitHub stars / issues / downloads
- [ ] 1 週後寫「發布 1 週回顧」

---

## 📸 截圖建議

如果你有截圖工具（PowerShell / Snipping Tool），建議截：

1. **首頁**：`index.html` 在瀏覽器中
2. **危險檢測**：`02-malicious-shell.md` 的開頭（顯示 DANGER verdict）
3. **Unicode 隱寫**：`05-unicode-stego.md` 的開頭（展示 v2.0 新功能）
4. **CLI 輸出**：在終端運行 `safety-check` 命令的截圖

把截圖保存到 `demo/screenshots/` 並在 README 中引用。

---

## 🔄 更新流程

當有新功能時：
1. 更新 `index.html` 的示例和表格
2. 重新運行 `generate_samples.sh`
3. 提交到 git，部署到 GitHub Pages

---

## 📊 預期效果

| 指標 | v1.0.0 發布後 1 週 |
|------|------------------|
| GitHub Stars | 20-50 |
| Issues | 5-10（含誤報報告） |
| 規則貢獻 | 1-3 條 |
| 社區反饋 | 3-5 條 |

如果 1 個月內沒有任何 engagement，可能需要：
- 重新評估目標用戶
- 改變推廣渠道
- 調整核心功能（過於複雜？過於簡單？）

---

*最後更新：2026-08-17 (v1.0.0)*