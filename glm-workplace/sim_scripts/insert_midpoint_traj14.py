# -*- coding: utf-8 -*-
"""轨迹14 手术：在翻转点(P4)与 x=-100 点(P5)之间插入中点 (0,-719,380,90,0,0)，
把 200mm 段拆成 100+100（两段都 ≤150mm 单指令门禁）。
先备份原文件；插入后结构自检（22 点、各点值逐项核对）。"""
import sys, io, json, shutil, time, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PATH = r'D:\mydata\working things\dobot_arm\RoboDK files 2\连续轨迹14.json'
raw = open(PATH, 'rb').read()
bom = raw.startswith(b'\xef\xbb\xbf')
text = raw.decode('utf-8-sig')
records = json.loads(text)
print('原点数 =', len(records))

def vals(rec):
    return [float(v) for v in rec['values'][:6]]

i4 = 3   # 0-based：翻转点
i5 = 4   # 0-based：x=-100 点
assert records[i4].get('singular') is True, 'P4 不是翻转点：%s' % records[i4]
assert abs(vals(records[i4])[0] - 100.0) < 1e-9, 'P4 x != 100: %s' % vals(records[i4])
assert abs(vals(records[i5])[0] - (-100.0)) < 1e-9, 'P5 x != -100: %s' % vals(records[i5])
for k in (1, 2, 3, 4, 5):  # 中点必须与 P5 同 y/z/姿态
    assert abs(vals(records[i5])[k] - [-100.0, -719.0, 380.0, 90.0, 0.0, 0.0][k]) < 1e-9, \
        'P5 期望值不符: %s' % vals(records[i5])

ts = time.strftime('%Y%m%d-%H%M')
bak = PATH.replace('.json', '_pre_midpoint_%s.json.bak' % ts)
shutil.copy2(PATH, bak)
print('备份 =', bak)

mid = dict(records[i5])            # 复制同点 schema（singular/j6_delta 等字段完全一致）
mid['values'] = [0.0, -719.0, 380.0, 90.0, 0.0, 0.0]
records.insert(i5, mid)            # 插到翻转点之后

out = json.dumps(records, indent=2, ensure_ascii=False) + ('\n' if text.endswith('\n') else '')
data = out.encode('utf-8')
if bom:
    data = b'\xef\xbb\xbf' + data
open(PATH, 'wb').write(data)

check = json.loads(open(PATH, encoding='utf-8-sig').read())
assert len(check) == 22, len(check)
assert vals(check[3]) == [100.0, -719.0, 380.0, 90.0, 0.0, 0.0], vals(check[3])
assert vals(check[4]) == [0.0, -719.0, 380.0, 90.0, 0.0, 0.0], vals(check[4])
assert vals(check[5]) == [-100.0, -719.0, 380.0, 90.0, 0.0, 0.0], vals(check[5])
assert check[3].get('singular') is True and check[4].get('singular') is False
seg_a = abs(100.0 - 0.0)
seg_b = abs(0.0 - (-100.0))
print('插入后点数 =', len(check))
print('段长 P4->P5 = %.1fmm，P5->P6 = %.1fmm（均 ≤150）' % (seg_a, seg_b))
print('DONE：插入成功，结构自检通过')
