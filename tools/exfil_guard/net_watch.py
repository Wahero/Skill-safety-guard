"""L3 網絡監控：GetExtendedTcpTable（IPHLPAPI, ctypes, 零依賴）

列出本機 ESTABLISHED 的 TCP 連接及其所屬 PID，過濾出「外連」
（遠端 IP 非私有網段）供 guard 做 L3 關聯告警。

僅在 Windows 上生效；非 Windows 返回空列表。
"""
import ctypes
import ipaddress
import logging
import struct
import sys

logger = logging.getLogger("exfil_guard.net_watch")

iphlpapi = ctypes.windll.iphlpapi if sys.platform == "win32" else None

AF_INET = 2
TCP_TABLE_OWNER_PID_CONNECTIONS = 4
MIB_TCP_STATE_ESTAB = 5


def _setup_prototypes():
    if iphlpapi is None:
        return
    iphlpapi.GetExtendedTcpTable.argtypes = [
        ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint32),
        ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32,
    ]
    iphlpapi.GetExtendedTcpTable.restype = ctypes.c_uint32


_setup_prototypes()


def _is_private(ip: str) -> bool:
    try:
        return ipaddress.ip_address(ip).is_private
    except ValueError:
        return True


def get_external_connections() -> list:
    """返回外連 ESTABLISHED 連接列表：[{pid, local, remote}]"""
    if iphlpapi is None:
        return []
    # 先取所需緩衝區大小
    size = ctypes.c_uint32(0)
    iphlpapi.GetExtendedTcpTable(None, ctypes.byref(size), 0, AF_INET, TCP_TABLE_OWNER_PID_CONNECTIONS, 0)
    buf = ctypes.create_string_buffer(size.value)
    ret = iphlpapi.GetExtendedTcpTable(buf, ctypes.byref(size), 0, AF_INET, TCP_TABLE_OWNER_PID_CONNECTIONS, 0)
    if ret != 0:
        logger.error("GetExtendedTcpTable 失敗 code=%s", ret)
        return []

    # MIB_TCPTABLE_OWNER_PID: DWORD dwNumEntries; MIB_TCPROW_OWNER_PID rows[]
    # row: DWORD dwState, dwLocalAddr, dwLocalPort, dwRemoteAddr, dwRemotePort, dwOwningPid
    class Row(ctypes.Structure):
        _fields_ = [
            ("dwState", ctypes.c_uint32),
            ("dwLocalAddr", ctypes.c_uint32),
            ("dwLocalPort", ctypes.c_uint32),
            ("dwRemoteAddr", ctypes.c_uint32),
            ("dwRemotePort", ctypes.c_uint32),
            ("dwOwningPid", ctypes.c_uint32),
        ]

    def ip_str(addr: int) -> str:
        return f"{(addr >> 0) & 0xFF}.{(addr >> 8) & 0xFF}.{(addr >> 16) & 0xFF}.{(addr >> 24) & 0xFF}"

    def port_str(p: int) -> int:
        return ((p >> 8) & 0xFF) | ((p & 0xFF) << 8)

    count = struct.unpack_from("<I", buf, 0)[0]
    rows = []
    offset = 4
    row_size = ctypes.sizeof(Row)
    for _ in range(count):
        row = Row.from_buffer_copy(buf.raw[offset: offset + row_size])
        offset += row_size
        if row.dwState == MIB_TCP_STATE_ESTAB:
            remote = ip_str(row.dwRemoteAddr)
            if not _is_private(remote):
                rows.append({
                    "pid": row.dwOwningPid,
                    "local": f"{ip_str(row.dwLocalAddr)}:{port_str(row.dwLocalPort)}",
                    "remote": f"{remote}:{port_str(row.dwRemotePort)}",
                })
    return rows
