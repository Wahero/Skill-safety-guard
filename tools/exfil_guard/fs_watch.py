"""L1 文件系統監控：ReadDirectoryChangesW（ctypes, 零第三方依賴）

監控配置的根目錄，對創建 / 寫入 / 重命名事件調用 callback(full_path, action)。
僅在 Windows 上生效；非 Windows 平台 run() 直接退出（不報錯）。
"""
import ctypes
import logging
import os
import struct
import sys
import threading

logger = logging.getLogger("exfil_guard.fs_watch")

kernel32 = ctypes.windll.kernel32 if sys.platform == "win32" else None

FILE_LIST_DIRECTORY = 0x0001
FILE_SHARE_READ = 0x0001
FILE_SHARE_WRITE = 0x0002
FILE_SHARE_DELETE = 0x0004
OPEN_EXISTING = 3
FILE_FLAG_BACKUP_SEMANTICS = 0x02000000

FILE_NOTIFY_CHANGE_FILE_NAME = 0x00000001
FILE_NOTIFY_CHANGE_LAST_WRITE = 0x00000010
FILE_NOTIFY_CHANGE_CREATION = 0x00000040

FILTER = (
    FILE_NOTIFY_CHANGE_FILE_NAME
    | FILE_NOTIFY_CHANGE_LAST_WRITE
    | FILE_NOTIFY_CHANGE_CREATION
)

ACTIONS = {1: "created", 2: "deleted", 3: "updated", 4: "renamed_old", 5: "renamed_new"}
RELEVANT = (1, 3, 5)  # created / updated / renamed_new


def _setup_prototypes():
    if kernel32 is None:
        return
    kernel32.CreateFileW.argtypes = [
        ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32,
        ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p,
    ]
    kernel32.CreateFileW.restype = ctypes.c_void_p
    kernel32.ReadDirectoryChangesW.argtypes = [
        ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32,
        ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32), ctypes.c_void_p, ctypes.c_void_p,
    ]
    kernel32.ReadDirectoryChangesW.restype = ctypes.c_int32
    kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
    kernel32.CloseHandle.restype = ctypes.c_int32


_setup_prototypes()

INVALID_HANDLE = (1 << (8 * ctypes.sizeof(ctypes.c_void_p))) - 1  # -1 as unsigned


class DirectoryWatcher(threading.Thread):
    """監控單一目錄（可遞歸）的後台線程。"""

    def __init__(self, path: str, recursive: bool, callback):
        super().__init__(daemon=True)
        self.path = path
        self.recursive = recursive
        self.callback = callback
        self._stop = threading.Event()

    def stop(self):
        self._stop.set()

    def run(self):
        if kernel32 is None:
            logger.debug("非 Windows 平台，跳過 L1 監控: %s", self.path)
            return
        h_dir = kernel32.CreateFileW(
            self.path, FILE_LIST_DIRECTORY,
            FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
            None, OPEN_EXISTING, FILE_FLAG_BACKUP_SEMANTICS, None,
        )
        if h_dir is None or h_dir == INVALID_HANDLE:
            logger.error("無法打開監控目錄（需權限）: %s", self.path)
            return
        buf = ctypes.create_string_buffer(8192)
        n = ctypes.c_uint32(0)
        while not self._stop.is_set():
            ok = kernel32.ReadDirectoryChangesW(
                h_dir, buf, len(buf), self.recursive, FILTER,
                ctypes.byref(n), None, None,
            )
            if not ok or n.value == 0:
                continue
            self._parse(bytes(buf.raw[: n.value]), self.path)
        kernel32.CloseHandle(h_dir)

    def _parse(self, data: bytes, root: str):
        off = 0
        while off + 12 <= len(data):
            next_off, action, fn_len = struct.unpack_from("<III", data, off)
            if fn_len > 0:
                raw = data[off + 12: off + 12 + fn_len]
                name = raw.decode("utf-16-le", errors="ignore")
                full = os.path.join(root, name)
                if action in RELEVANT:
                    try:
                        self.callback(full, ACTIONS.get(action, "unknown"))
                    except Exception as e:  # callback 異常不應終止監控
                        logger.error("callback 異常: %s", e)
            if next_off == 0:
                break
            off += next_off
