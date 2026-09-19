---
name: exfil_guard
description: >
  Workspace Exfiltration Guard 運行時守禦（L1/L2/L3）。監控 workspace 外落地的
  打包產物與外連，對 ZCode 外洩方案指紋（R1–R8）做實時檢測與可選阻斷。
  僅 Windows，需顯式啟用與管理員權限。
trigger_words:
  - 監控 workspace 外洩
  - 開 exfil guard
  - guard status
  - 紅隊測試
---

# exfil_guard（運行時守禦 · 可選模塊）

> ⚠️ **獨立於靜態引擎**：本目錄是 `skill_safety_guard` 的**運行時**補充層，
> 不被 `scan_orchestrator` 引用，不影響主工具的「純靜態、零執行」保證。
> 它與 `rules/exfiltration.yaml` + `detectors/exfiltration.py`（靜態層）共用同一套
> 外洩指紋知識（R1–R8），但運作方式不同：靜態層在**安裝前**掃描 Skill 源碼；
> 本模塊在**運行時**監控文件系統與網絡。

## 層級

- **L1 文件系統監控**：`fs_watch.py` 用 `ReadDirectoryChangesW`（ctypes）監控
  `config.yaml` 中配置的落地目錄（默認 `%TEMP%`、`%LOCALAPPDATA%`）。
- **L2 產物啟發式**：對監控目錄內出現的 `.zip/.tar/.tgz/.enc` 等產物做規則評估
  （見 `rules/`）。
- **L3 網絡關聯**：`net_watch.py` 用 `GetExtendedTcpTable` 列出外連連接，
  nuke 模式下可經防火牆封鎖（見 `responder.py`）。

## 指紋規則（R1–R8）

見 `rules/builtin_zcode.yaml`（ZCode 方案指紋）與 `rules/generic.yaml`（通用啟發式）。
規則類型：`substring` / `co_occur` / `path_enum` / `ext_in_temp`，由 `guard.py` 解釋。

## 響應模式（config.yaml → response.mode）

| 模式 | 行為 | 系統修改 |
|---|---|---|
| `audit` | 記錄日誌 + 彈窗通知 | 無 |
| `block` | 額外對命中文件施加拒絕寫入 ACL（`icacls /deny`） | 有（ACL） |
| `nuke` | block + 經 `netsh` 防火牆封鎖外連 | 有（ACL + 防火牆） |

## 用法

```bash
# 觀測（不修改系統）
python tools/exfil_guard/guard.py --dry-run

# 依 config.yaml 的 response.mode 運行（block/nuke 需管理員）
python tools/exfil_guard/guard.py

# 自檢（無需管理員）
python tools/exfil_guard/selftest.py

# 紅隊模擬（僅驗證檢測 / 加 --execute 才真響應）
python tools/exfil_guard/redteam_sim.py
python tools/exfil_guard/redteam_sim.py --execute

# 開機自啟（管理員，修改排程）
python tools/exfil_guard/install_autostart.py
python tools/exfil_guard/install_autostart.py --remove
```

## 依賴與約束

- **零第三方依賴**：僅用 `ctypes` + 標準庫 + `PyYAML`（與主工具一致）。
- **僅 Windows**：非 Windows 平台 L1/L3 直接跳過。
- **需權限**：`block`/`nuke` 與 `install_autostart` 會修改系統，須經審批並以管理員執行。
- **可行性邊界**（來自方案評估）：
  - 不做 HTTPS 路徑級攔截（需 MITM/根證，已否決）；
  - 文件**讀**監控不精確（需 ETW/minifilter）；
  - 用戶態守禦可被繞過——定位是「增加外洩成本 + 事後止血」，非絕對防線。

## 11 階段推出路線（參考）

1. 骨架 + L1 + builtin-zcode 規則（低風險）
2. redteam_sim 驗證檢測 + 阻斷（低風險）
3. 觀測模式跑 7 日看誤報（低風險）
4. 轉 block 模式 + 裝自啟（中風險）
5. 加 L2 啟發式（中風險）
6. 加 L3 網絡（可選，事後止血用，中風險）
