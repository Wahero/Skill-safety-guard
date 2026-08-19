# 自掃維護規則（SELF-SCAN RULES）

> **用途**：明確哪些目錄/文件可自行改動、哪些禁止，確保自掃結果始終保持 **SAFE / A 級 / 0 發現**
> **適用對象**：WaBoss 自行複製/新增檔案進倉庫時遵守
> **更新**：2026-08-19 ｜ **當前版本**：v3.5.0 ｜ **驗證命令**：見文末「快速驗證」

---

## 一、為什麼要有這份規則

自掃（`python scripts/safety-check . --no-pi`）是項目的**信任狀**——SAFE/A/0 證明工具掃得動自己，也是 CI 回歸防線。

但自掃是**全目錄文本掃描**：倉庫裡任何新增的 `.md/.py/.sh/.yaml` 等文本文件，只要含危險模式（`curl | bash`、改寫 `~/.pi/agent/AGENTS.md`、假金鑰等），就會被自己的規則命中 → 自掃從 SAFE 掉到 DANGER，對外可信度歸零。

**已發生過的案例**：`docs/PACKAGE_INTRO.md` 因含 ClawHavoc 攻擊手法示例（`curl | bash`、AGENTS.md 引用），未入白名單時自掃 8 個發現、F 級。

---

## 二、掃描機制（影響哪些文件會被掃）

| 機制 | 行為 |
|------|------|
| **文件類型** | 只掃文本文件：`.md .txt .py .js .ts .sh .bash .json .yaml .yml .toml .cfg .ini .html .css .jsx .tsx .vue .go .rs .java .kt .rb .php` |
| **自動跳過目錄** | `.git`、`node_modules`、`__pycache__`、`venv`、`.venv`、`build`、`dist`（任意層級出現即跳過）|
| **fixtures 跳過** | 掃整個倉庫時跳過 `tests/fixtures/`（直接掃 fixture 目錄時不跳）|
| **白名單過濾** | 路徑白名單（fnmatch）+ 模式白名單（rule_id+pattern）→ 命中即不報告 |
| **⚠️ 路徑白名單限制** | `*/xxx/*` 模式**只匹配子目錄內文件**，根目錄新增文件不在任何路徑白名單覆蓋範圍（除非內容本身無危險模式）|

---

## 三、三區規則（核心）

### 🟢 綠區：可自由新增/改動（不影響自掃）

| 位置 | 原因 |
|------|------|
| `report/` | 已入路徑白名單 `*/report/*` |
| `demo/outputs/*.md`、`demo/index.html` | 已入白名單（示例輸出）|
| `.gitignore`、`CHANGELOG.md` | 已入白名單 |
| `docs/CRITICAL_PATHS_EVALUATION.md`、`docs/PACKAGE_INTRO.md`、`docs/SELFSCAN_RULES.md`（本文件）| 已入白名單 |
| **非文本文件**（`.png .jpg .zip .pdf .exe .lock` 等）| 根本不被掃描，可隨意放置 |
| `.git/`、`node_modules/`、`venv/` 等跳過目錄內 | 掃描器直接跳過 |

### 🟡 黃區：可新增，但需自查（誤報高風險）

| 位置 | 風險與處理 |
|------|-----------|
| **根目錄新增 `.md`/`.txt`/`.py`/`.sh` 等文本文件** | ⚠️ 不在任何路徑白名單。若內容提到安全術語（見第五節）→ 觸發檢測。**新增後必跑自掃**，誤報則加白名單 |
| **`docs/` 新增含攻擊示例的文檔**（寫到 `curl | bash`、AGENTS.md 改寫、假金鑰、`/etc/passwd` 等）| 必觸發。需加入路徑白名單（同 PACKAGE_INTRO.md 處理）|
| **`scripts/` 新增腳本** | 若含 shell 示例/敏感路徑引用 → 需白名單或確保為安全代碼 |

**黃區處理流程**（新增後）：
```
1. 新增文件
2. 跑自掃 → 0 發現 = OK，直接提交
3. 有發現 → 判斷是否真誤報（文檔示例/描述性文字 = 誤報）
4. 誤報 → 在 rules/whitelist.yaml 的 whitelisted_paths 加精準路徑（如 */docs/新檔名.md）
5. 重跑自掃確認 SAFE + 對照掃描（掃 url-extract）確認檢出率未受損
```

### 🔴 紅區：禁止自行改動（破壞自掃/檢出率/版本）

| 位置 | 禁止原因 |
|------|----------|
| `rules/*.yaml`（credentials/dangerous_shell/sensitive_paths/critical_paths/unicode/prompt_injection/mcp/mcp_injection/installed_extensions）| 規則定義，改動影響規則數（181）與檢測能力 |
| `rules/whitelist.yaml` | 白名單自身；改錯 → 要麼誤報、要麼檢測失明 |
| `tests/fixtures/` | 惡意測試樣本；改動破壞檢出率 8/8 驗證 |
| `src/skill_safety_guard/` | 檢測代碼本體 |
| `pyproject.toml`、`package.json`、`SKILL.md` frontmatter | 版本一致性（3.5.0）；改動造成版本分裂 |
| `CHANGELOG.md` 已歸檔版本節 | 歷史記錄不可竄改 |

> 例外：如需新增**規則**或**白名單條目**，交給開發流程（本會話）處理，勿直接手改。

---

## 四、常見誤觸發模式（黃區文件易踩）

以下是會觸發自身檢測的文本模式，新增文件時注意：

| 模式 | 觸發規則 | 典型場景 |
|------|----------|----------|
| `curl | bash`（管道執行遠程腳本）| shell-curl-bash | 攻擊手法描述、安裝指南 |
| 寫入 `~/.pi/agent/AGENTS.md`（含 writeFileSync/write 等動詞）| critical-agents-md-write / path-agents-md-ref | 全局配置劫持描述 |
| `sk-...`、`ghp_...`、`AKIA...` 形式字符串 | cred-* | 假金鑰示例 |
| `.env` 路徑 + 讀取動詞（open/read/cat）| path-env-file | 憑證洩露描述 |
| `/etc/passwd`、`.ssh/`、`/etc/ld.so.preload` 等敏感路徑 + 訪問動詞 | sensitive-* | Rootkit 向量描述 |
| 零寬字符 / Unicode 標籤字符（U+E0000 等）| unicode-* | 隱寫術示例 |

**防範技巧**：描述攻擊手法時用「管道執行遠程腳本」等文字描述，或把代碼範例拆開（如 `curl ｜ bash` 用全形符號），避免字面命中。

---

## 五、快速驗證（每次新增文件後跑）

```bash
cd D:/ai/PiAgent/Skill-safety-guard

# 1. 自掃（必須 SAFE / A / 0 發現）
PYTHONIOENCODING=utf-8 python scripts/safety-check . --no-pi

# 2. 檢出率（必須 8/8 = 100%，確保白名單沒弄瞎檢測）
PYTHONIOENCODING=utf-8 python -m pytest tests/test_phase0.py::test_v04_detection_rate -s -q | grep 檢出率

# 3. 對照掃描（掃真實 skill，確認未失明；預期 url-extract：CAUTION / 有發現）
PYTHONIOENCODING=utf-8 python scripts/safety-check C:/Users/Administrator/.pi/agent/skills/url-extract --no-pi

# 4. 單元測試（預期 3 passed）
PYTHONIOENCODING=utf-8 python -m pytest tests/ -q
```

**綠燈條件**：自掃 SAFE/A/0 ＋ 檢出率 8/8 ＋ pytest 3 passed → 才可 commit。

---

## 六、違規後果速查

| 若自掃出現 | 原因 | 處理 |
|-----------|------|------|
| DANGER / F 級，8 個發現 | 新增文件含危險模式未入白名單 | 找到發現位置 → 判斷誤報 → 加白名單（黃區流程）|
| 檢出率 < 8/8 | 白名單 pattern 過寬誤傷 fixture | 收緊 pattern（如 `https://example\.com` 而非 `example\.com`）|
| 版本號不一致（報告 v1.5.0 等）| 改了版本文件或 __init__.py | 統一為 3.5.0 |

---

*本文件本身已在白名單內（`*/docs/SELFSCAN_RULES.md`），可自由包含攻擊模式示例，不影響自掃。*
*生成：2026-08-19 ｜ 倉庫：https://github.com/Wahero/Skill-safety-guard*
