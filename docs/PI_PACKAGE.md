# Pi Package 發布指南

> **skill-safety-guard 作為 Pi Package 的結構與發布流程**
> 核心原則：**單一來源**——同一份代碼既服務手動安裝（SKILL.md 複製/junction），也服務 `pi install`，不需要維護兩份代碼。

---

## 1. 為什麼不需要兩份代碼

Pi Package 是**同一倉庫的薄聲明層**：`package.json` 的 `pi` manifest 告訴 pi「這個包的技能在 `./SKILL.md`」。

```
Skill-safety-guard/                ← 唯一的代碼來源
├── SKILL.md          ← 技能（manifest 直接指向它）
├── package.json      ← pi manifest（新增的唯一文件）
├── src/              ← Python 引擎（原地不動）
├── scripts/          ← CLI 入口（原地不動）
├── rules/            ← 規則庫（原地不動）
└── docs/ tests/ demo/
```

**為什麼可行**（已從 pi 源碼驗證）：
1. `collectFilesFromPaths`：manifest 指向的**文件**直接作為資源載入 → `"skills": ["./SKILL.md"]` 有效
2. Pi 注入技能區塊時附帶 `References are relative to <baseDir>` → SKILL.md 用 `{baseDir}` 佔位符引用同倉庫內代碼（brave-search 同款模式）
3. `scripts/safety-check` 自帶 `sys.path` 注入 `src/` → **克隆即可運行，無需 pip install 本項目**
4. `pi install git:...` 完整克隆整個 repo → `src/`、`rules/`、`docs/` 全部就位

**已驗證**：用 pi 的 `DefaultResourceLoader` 加載本 package，正確解析出：
```
FOUND: skill-safety-guard | baseDir: <package root>
  file: <package root>/SKILL.md
```

---

## 2. package.json 結構

```json
{
  "name": "skill-safety-guard",
  "version": "3.5.0",
  "keywords": ["pi-package", "pi", "security", "skill-safety", "mcp"],
  "license": "MIT",
  "pi": {
    "skills": ["./SKILL.md"]
  }
}
```

| 字段 | 說明 |
|------|------|
| `keywords` | 必須含 `pi-package` 才能在 pi.dev 官網展示 |
| `pi.skills` | 聲明技能資源；`./SKILL.md` 文件級指向（不會誤載其他 .md） |
| `pi.image` / `pi.video` | 官網預覽（可選）：image 支持 PNG/JPEG/GIF/WebP，video 僅 MP4，video 優先 |
| `files` | npm 發布時打包的文件白名單（見下方 npm 章節） |

> ⚠️ 不要用 `"skills": ["./"]`——pi 會把根目錄**所有頂層 .md** 當作技能載入（README.md、USAGE.md 等都會變成假技能）。

---

## 3. 安裝方式（用戶視角）

```bash
# 方式 A：從 GitHub 安裝（推薦，即刻可用）
pi install git:github.com/Wahero/Skill-safety-guard

# 方式 B：npm 發布後
pi install npm:skill-safety-guard

# 方式 C：本地開發
pi install ./relative/path
pi install /absolute/path

# 臨時試用（不寫入 settings）
pi -e git:github.com/Wahero/Skill-safety-guard

# 管理
pi remove npm:skill-safety-guard
pi update npm:skill-safety-guard
pi config        # TUI 啟用/禁用資源
```

安裝位置：
- git 源 → `~/.pi/agent/git/<host>/<path>/`
- npm 源 → `~/.pi/agent/npm/node_modules/<name>/`

---

## 4. 發布到 pi.dev 官網（gallery）

### 前置條件

1. 倉庫設為 **Public**（gallery 需要可訪問）
2. `package.json` 含 `pi-package` keyword
3. （可選）加 `pi.image` / `pi.video` 預覽

### 發布流程

```bash
# 1. 確保版本號與 CHANGELOG 一致（發布前必做）
#    __init__.py 的 __version__ 也需同步

# 2. 發布到 npm（供 pi install npm:... 使用）
npm login
npm publish

# 3. 或僅用 git 源（gallery 也支持）
pi install git:github.com/Wahero/Skill-safety-guard@<tag>
```

> gallery 會自動索引帶 `pi-package` keyword 的包。發布後可在 https://pi.dev/packages 檢查。

---

## 5. 發布前檢查清單

- [ ] `__version__`（Python）與 `package.json` version 一致
- [ ] SKILL.md frontmatter `version` 一致
- [ ] 自掃通過：`python scripts/safety-check . --no-pi` → SAFE
- [ ] 檢出率回歸：`python tests/test_phase0.py` → 全 PASS（8/8）
- [ ] `pi install git:...` 後 `/safety-check` 可用（pyyaml 已裝）
- [ ] demo 截圖就緒（gallery 預覽用）
- [ ] README badge 版本更新

---

## 6. 常見問題

### Q: 安裝後 `python -m skill_safety_guard` 找不到？
A: pi package 模式不需要 pip install。SKILL.md 用 `{baseDir}/scripts/safety-check` 直接運行。
   若想全局使用 CLI：`pip install -e <package-dir>`（git 安裝位置見上文）。

### Q: 缺 pyyaml 報錯？
A: 首次使用前 `pip install pyyaml`（SKILL.md 的「設置」章節已說明）。
   `scripts/safety-check` 會給出友好提示而非 traceback。

### Q: 安裝位置在別處，`{baseDir}` 還有效嗎？
A: 有效。pi 注入的 skill 區塊帶 `References are relative to <baseDir>`，
   模型會把 `{baseDir}` 解析為實際安裝目錄（無論 git/npm/本地路徑）。

### Q: npm 發布會把整個 repo 打進去嗎？
A: 不會。`files` 字段控制打包內容；未列出的（如 tests/、.github/）不進 tarball。
   注意 `files` 必須包含運行時需要的一切：SKILL.md、src/、scripts/、rules/。

---

*更新：2026-08-18 ｜ 倉庫：https://github.com/Wahero/Skill-safety-guard*
