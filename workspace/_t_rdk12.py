# -*- coding: utf-8 -*-
"""抽取站内活动条目 TCP真实运动 的内嵌源码，落盘并打印文件头/指纹。"""
import hashlib, os, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

d = open(r'D:\mydata\workspace\_rdk_unpacked.bin', 'rb').read()
OUT = r'D:\mydata\workspace\_rdk_scripts'
os.makedirs(OUT, exist_ok=True)

# 站内所有 python 代码块起点（按已知结构：名字后紧跟 длина + 源码）
starts = [381, 663, 1861146, 1861423, 1910353, 1910630, 1959341, 1959618,
          2010152, 2010176, 2013647, 2049439, 2050611, 2125317, 2125607,
          2178937, 2179227, 2233499, 2233776, 2290336, 2290613, 2355543,
          2355833, 2410137, 2410523, 2472874, 2473317]

def block(o):
    z = d.find(b'\x00', o)
    return d[o:z if z > 0 else len(d)]

print('=== 两个 TCP真实运动 流（站内活动条目）===')
for o in (2410137, 2472874):
    code = block(o)
    head = code[:400].decode('utf-8', 'replace')
    print('\n@%d  len=%d  sha256=%s' % (o, len(code), hashlib.sha256(code).hexdigest()))
    print('---- 文件头 ----')
    print('\n'.join(head.splitlines()[:14]))
    open(os.path.join(OUT, 'TCP真实运动_%d.py' % o), 'wb').write(code)
    print('已存 _rdk_scripts/TCP真实运动_%d.py' % o)

# 与磁盘两版对比
disk = {
    'workspace(43,710B,9/18)': r'D:\mydata\workspace\机械臂TCP真实运动.py',
    'RoboDK目录(53,366B,9/26)': r'D:\mydata\working things\dobot_arm\RoboDK files 2\机械臂TCP真实运动.py',
}
print('\n=== 与磁盘版对比 ===')
for o in (2410137, 2472874):
    code = block(o)
    for k, p in disk.items():
        raw = open(p, 'rb').read()
        same = raw == code
        same_lf = raw.replace(b'\r\n', b'\n') == code.replace(b'\r\n', b'\n')
        print('  @%-8d vs %-26s 完全相同=%s 仅换行差异=%s' % (o, k, same, same_lf))

print('\n=== 站内副本的“启动日志行”指纹（判断是不是最新一版）===')
for o in starts:
    code = block(o)
    if code[:1] != b'#':
        continue
    last = code[-1400:].decode('utf-8', 'replace')
    m = re.search(r'log\("([^"]{1,120})"\)', last)
    print('  @%-8d %s' % (o, (m.group(1)[:100] if m else '?')))
