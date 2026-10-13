"""Which processes hold a file open (Windows Restart Manager). usage: python who_locks.py <file> [<file> ...]"""
import ctypes, ctypes.wintypes as w, sys
mgr = ctypes.windll.rstrtmgr
class UniqueProcess(ctypes.Structure): _fields_ = [("dwProcessId", w.DWORD), ("ProcessStartTime", w.FILETIME)]
class ProcessInfo(ctypes.Structure): _fields_ = [("Process", UniqueProcess), ("strAppName", w.WCHAR * 256), ("strServiceShortName", w.WCHAR * 64), ("ApplicationType", ctypes.c_int), ("AppStatus", w.DWORD), ("TSSessionId", w.DWORD), ("bRestartable", w.BOOL)]
for path in sys.argv[1:]:
    handle = w.DWORD(); key = ctypes.create_unicode_buffer(33)
    assert mgr.RmStartSession(ctypes.byref(handle), 0, key) == 0
    files = (w.LPCWSTR * 1)(path); assert mgr.RmRegisterResources(handle, 1, files, 0, None, 0, None) == 0
    n = w.UINT(0); needed = w.UINT(0); reason = w.DWORD(0)
    mgr.RmGetList(handle, ctypes.byref(needed), ctypes.byref(n), None, ctypes.byref(reason))
    arr = (ProcessInfo * max(needed.value, 1))(); n = w.UINT(needed.value)
    res = mgr.RmGetList(handle, ctypes.byref(needed), ctypes.byref(n), arr, ctypes.byref(reason))
    print(path.split("\\")[-1], "->", [(arr[i].Process.dwProcessId, arr[i].strAppName) for i in range(n.value)] if res == 0 else "error %d" % res)
    mgr.RmEndSession(handle)
