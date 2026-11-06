# -*- coding: utf-8 -*-
"""进程外看门狗：每秒枚举 python.exe 进程，记录生灭时刻到 watch_macro_log.txt。
纯旁观：不连接机械臂、不碰 RoboDK API、不写宏代码。
运行方式：系统 python 后台常驻。"""
import subprocess, time, io, os, datetime

LOG = r'D:\mydata\glm-workplace\sim_scripts\watch_macro_log.txt'
SELF = os.getpid()

def wlog(s):
    with io.open(LOG, 'a', encoding='utf-8') as f:
        f.write('%s | %s\n' % (datetime.datetime.now().strftime('%m-%d %H:%M:%S'), s))

def snapshot():
    out = subprocess.run(
        ['tasklist', '/FI', 'IMAGENAME eq python.exe', '/FO', 'CSV', '/NH'],
        capture_output=True, text=True).stdout
    pids = set()
    for line in out.splitlines():
        parts = [p.strip('"') for p in line.split('","')]
        if len(parts) >= 4 and parts[1].isdigit():
            pids.add(int(parts[1]))
    return pids

def cmdline(pid):
    try:
        out = subprocess.run(
            ['powershell', '-NoProfile', '-Command',
             "(Get-CimInstance Win32_Process -Filter 'ProcessId=%d').CommandLine" % pid],
            capture_output=True, text=True, timeout=15).stdout.strip()
        return out[:200]
    except Exception as e:
        return '<cmdline err %r>' % e

def recent_wer():
    try:
        out = subprocess.run(
            ['powershell', '-NoProfile', '-Command',
             "Get-WinEvent -FilterHashtable @{LogName='Application';Level=2,3;StartTime=(Get-Date).AddMinutes(-2)} -MaxEvents 6 -ErrorAction SilentlyContinue | ForEach-Object { '{0} {1} {2}' -f $_.TimeCreated, $_.ProviderName, ($_.Message -split \"`n\")[0] }"],
            capture_output=True, text=True, timeout=30).stdout.strip()
        return out or '(no events)'
    except Exception as e:
        return '<wer err %r>' % e

wlog('===== watchdog start, self pid=%d（自身进程的生灭请忽略）=====' % SELF)
known = {p for p in snapshot() if p != SELF}
wlog('初始 python 进程: %s' % sorted(known))
while True:
    time.sleep(1.0)
    try:
        cur = {p for p in snapshot() if p != SELF}
    except Exception as e:
        wlog('snapshot err %r' % e)
        continue
    born = cur - known
    died = known - cur
    for p in born:
        wlog('BIRTH pid=%d cmd=%s' % (p, cmdline(p)))
    for p in died:
        wlog('DEATH pid=%d —— 近2分钟应用错误/挂起事件：' % p)
        wlog(recent_wer())
    known = cur
