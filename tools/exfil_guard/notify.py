"""通知層：MessageBoxW（ctypes，零第三方依賴）優先；Toast 經 PowerShell（可選）

設計約束（來自方案可行性評估）：
  - MessageBoxW ✅ 純 ctypes，無依賴
  - Toast ⚠️ 需 Windows 10+ WinRT，經 PowerShell 最佳努力，失敗回退 MessageBoxW
  - 第三方庫（pywin32 / win10toast / watchdog）❌ 不使用，保持零依賴
"""
import ctypes
import subprocess
import sys

MB_ICONWARNING = 0x30
MB_ICONERROR = 0x10
MB_TOPMOST = 0x40000


def messagebox(title: str, text: str, error: bool = False) -> bool:
    """彈出 MessageBoxW。成功返回 True。"""
    try:
        user32 = ctypes.windll.user32
        flags = (MB_ICONERROR if error else MB_ICONWARNING) | MB_TOPMOST
        user32.MessageBoxW(0, str(text), str(title), flags)
        return True
    except Exception:
        # 非 Windows 或無法調用 GUI 時靜默失敗
        return False


def toast(title: str, text: str) -> bool:
    """最佳努力：PowerShell 彈出 Toast。失敗回退 MessageBoxW。"""
    ps = (
        "powershell -NoProfile -NonInteractive -Command "
        "[Windows.UI.Notifications.ToastNotificationManager,"
        " Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null;"
        "$t = [Windows.UI.Notifications.ToastNotificationManager]::"
        "CreateToastNotifier('exfil_guard');"
        "$x = New-Object Windows.Data.Xml.Dom.XmlDocument;"
        "$x.LoadXml('<toast><visual><binding template=\\'ToastText02\\'>"
        "<text>%TITLE%</text><text>%BODY%</text></binding></visual></toast>'."
        "Replace('%%TITLE%%', %QT%T%QT%).Replace('%%BODY%%', %QT%B%QT%));"
        "$t.Show($x)" % {
            "T": title.replace("'", ""),
            "B": text.replace("'", "")[:200],
            "QT": "'",
        }
    )
    try:
        subprocess.run(ps, shell=True, capture_output=True, timeout=15)
        return True
    except Exception:
        return messagebox(title, text, error=False)


def notify(title: str, text: str, method: str = "messagebox", error: bool = False) -> None:
    """統一入口。method: messagebox | toast | both"""
    if method in ("messagebox", "both"):
        messagebox(title, text, error=error)
    if method in ("toast", "both"):
        toast(title, text)
