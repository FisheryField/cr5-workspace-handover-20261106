# -*- coding: utf-8 -*-
"""站内活动版 vs 磁盘两版：逐项指纹对照。"""
import difflib, hashlib, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

A = open(r'D:\mydata\workspace\_rdk_scripts\TCP真实运动_2472874.py', 'rb').read().decode('utf-8', 'replace')
B = open(r'D:\mydata\working things\dobot_arm\RoboDK files 2\机械臂TCP真实运动.py', 'rb').read().decode('utf-8', 'replace')
C = open(r'D:\mydata\workspace\机械臂TCP真实运动.py', 'rb').read().decode('utf-8', 'replace')

def prof(tag, t):
    print('\n===== %s =====' % tag)
    print('  字符数 %d  行数 %d  sha=%s' % (len(t), t.count('\n') + 1, hashlib.sha256(t.encode()).hexdigest()[:12]))
    pats = {
        'real_deviation_var 默认值': r'real_deviation_var\s*=\s*tk\.StringVar\(value="([^"]+)"',
        'MOVEJ_FALLBACK_MAX_DEVIATION_MM': r'MOVEJ_FALLBACK_MAX_DEVIATION_MM\s*=\s*([0-9.]+)',
        'ROBOT_SPEED': r'ROBOT_SPEED\s*=\s*([0-9.]+)',
        '_controller_feedback 30004': r'30004',
        '_move_with_completion_check': r'_move_with_completion_check',
        '_plan_continuous_trajectory': r'_plan_continuous_trajectory',
        '姿态退让/退让': r'退让',
        '自转360': r'spin360|自转',
        '_plan_cache/缓存': r'_plan_cache|缓存',
        '避障': r'避障',
        '_check_tcp_segment_continuous(旧路径)': r'_check_tcp_segment_continuous',
        '导入JSON': r'import_trajectory|导入仿真轨迹',
        'Trace 命令': r"Command\('Trace'",
        'Tab 数': r'notebook\.add',
    }
    for k, p in pats.items():
        m = re.findall(p, t)
        print('  %-38s %s' % (k, m[:3] if m else '—'))

prof('站内活动版 TCP真实运动 @2472874（今天 16:44 那版）', A)
prof('磁盘 RoboDK目录版（9/26, 53,366B）', B)
prof('磁盘 workspace 版（9/18, 43,710B）', C)

print('\n===== 站内活动版 的函数清单 vs 磁盘 9/26 版 =====')
fa = [m.group(1) for m in re.finditer(r'^def (\w+)', A, re.M)]
fb = [m.group(1) for m in re.finditer(r'^def (\w+)', B, re.M)]
print('站内独有 :', sorted(set(fa) - set(fb)))
print('磁盘独有 :', sorted(set(fb) - set(fa)))
print('共有数   :', len(set(fa) & set(fb)))

print('\n===== 站内版 vs 9/26 版的差异摘要（unified diff, 前 60 行）=====')
diff = list(difflib.unified_diff(B.splitlines(), A.splitlines(), 'disk_9-26', 'station_now', lineterm='', n=1))
print('差异块总数 =', sum(1 for l in diff if l.startswith('@@')))
for l in diff[:60]:
    print(l[:160])
