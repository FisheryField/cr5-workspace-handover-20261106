import ctypes
import ctypes.wintypes as wt
import subprocess

user32 = ctypes.windll.user32
out = subprocess.run(
    ["powershell", "-NoProfile", "-Command",
     "Get-Process RoboDK -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id"],
    capture_output=True, text=True).stdout.split()
pids = [int(p) for p in out]
print("RoboDK pids:", pids)

rows = []
WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wt.HWND, wt.LPARAM)


def cb(h, l):
    rows.append(h)
    return True


user32.EnumWindows(WNDENUMPROC(cb), 0)


def txt(h):
    b = ctypes.create_unicode_buffer(256)
    user32.GetWindowTextW(h, b, 256)
    return b.value


for h in rows:
    p = wt.DWORD()
    user32.GetWindowThreadProcessId(h, ctypes.byref(p))
    if p.value in pids:
        print(hex(h),
              "vis" if user32.IsWindowVisible(h) else "HID",
              "ICONIC" if user32.IsIconic(h) else "normal",
              "fg" if h == user32.GetForegroundWindow() else "-",
              repr(txt(h)))
