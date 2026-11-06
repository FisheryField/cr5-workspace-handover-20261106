# -*- coding: utf-8 -*-
"""找 RoboDK 驱动程序的输出/日志文件（近 1 天内修改的，且路径含 RoboDK）。"""
import os, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

roots = [r'D:\software\RoboDK', r'C:\Users\FisheryField\AppData\Roaming\RoboDK',
         r'C:\Users\FisheryField\Documents\RoboDK', r'C:\Users\FisheryField\AppData\Local\Temp']
now = time.time()
hits = []
for root in roots:
    for dirpath, dirs, files in os.walk(root):
        if '.vscodium2' in dirpath or 'node_modules' in dirpath:
            continue
        for f in files:
            fp = os.path.join(dirpath, f)
            try:
                mt = os.path.getmtime(fp); sz = os.path.getsize(fp)
            except OSError:
                continue
            if now - mt < 86400 and (f.lower().endswith(('.log', '.txt', '.out', '.err'))
                                     or 'log' in f.lower() or 'driver' in f.lower()):
                hits.append((mt, sz, fp))
hits.sort(reverse=True)
print('=== 近 24h 的日志类文件（%d 个）===' % len(hits))
for mt, sz, fp in hits[:40]:
    print('  %s %8d  %s' % (time.strftime('%m-%d %H:%M:%S', time.localtime(mt)), sz, fp))

print('\n=== 近 24h 内被修改的 RoboDK 目录下所有文件（前 25）===')
allf = []
for root in roots[:3]:
    for dirpath, dirs, files in os.walk(root):
        if '.vscodium2' in dirpath:
            continue
        for f in files:
            fp = os.path.join(dirpath, f)
            try:
                mt = os.path.getmtime(fp); sz = os.path.getsize(fp)
            except OSError:
                continue
            if now - mt < 86400:
                allf.append((mt, sz, fp))
allf.sort(reverse=True)
for mt, sz, fp in allf[:25]:
    print('  %s %8d  %s' % (time.strftime('%m-%d %H:%M:%S', time.localtime(mt)), sz, fp))
