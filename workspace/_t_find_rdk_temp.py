# -*- coding: utf-8 -*-
"""只读：查 RoboDK 的 Python 临时脚本目录（内嵌脚本运行时落地处）。"""
import glob, os, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

cands = []
for env in ('TEMP', 'TMP', 'LOCALAPPDATA', 'APPDATA', 'USERPROFILE'):
    v = os.environ.get(env)
    if v:
        cands.append(v)
print('环境候选目录:', cands)

pat = []
for base in set(cands):
    for sub in ('RoboDK*', 'robodk*', '*RoboDK*', 'Temp/RoboDK*'):
        pat.append(os.path.join(base, sub))
    pat.append(os.path.join(base, '**', 'RoboDK*'))
hits = set()
for p in pat:
    for h in glob.glob(p, recursive=False):
        hits.add(h)
print('\n=== 目录型命中 ===')
for h in sorted(hits):
    if os.path.isdir(h):
        print(' ', h)

print('\n=== 每个命中目录下最近文件（前 25）===')
for h in sorted(hits):
    if not os.path.isdir(h):
        continue
    files = []
    for root, dirs, fs in os.walk(h):
        for f in fs:
            fp = os.path.join(root, f)
            try:
                files.append((os.path.getmtime(fp), os.path.getsize(fp), fp))
            except OSError:
                pass
    files.sort(reverse=True)
    print('\n--- %s（%d 文件）' % (h, len(files)))
    for mt, sz, fp in files[:25]:
        print('   %s  %8d  %s' % (time.strftime('%m-%d %H:%M:%S', time.localtime(mt)), sz, fp))
