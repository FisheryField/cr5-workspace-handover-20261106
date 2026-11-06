# -*- coding: utf-8 -*-
"""分析站内内嵌脚本的存储结构：每个脚本的元数据字段 + 代码文本。"""
import re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
d = open(r'D:\mydata\workspace\_rdk_unpacked.bin', 'rb').read()
t = d.decode('utf-8', 'replace')

print('=== 1) 所有 "script"（区分大小写/不区分）出现位置及上下文 ===')
for m in re.finditer(r'(?i)script', t):
    o = m.start()
    ctx = t[max(0, o-160):o+160].replace('\n', '\\n')
    print('@%d  ...%s...' % (o, ctx))
    print('-' * 100)

print('\n=== 2) 版本指纹：新版/旧版独有串 ===')
marks = {
    '新版独有: 避障优先启动日志': '避障优先。J6自动',
    '新版独有: _move_with_completion_check': '_move_with_completion_check',
    '新版独有: _plan_continuous_trajectory': '_plan_continuous_trajectory',
    '新版独有: _controller_feedback': '_controller_feedback',
    '新版独有: 预检MoveJ兜底最大TCP偏离': '预检MoveJ兜底最大TCP偏离',
    '新版独有: 安装台_650x650x80mm': '安装台_650x650x80mm',
    '新版独有: _enable_obstacle_checks': '_enable_obstacle_checks',
    '旧版独有: 连续运动：支持导入仿真JSON': '连续运动：支持导入仿真JSON',
    '旧版独有: TCP IK：可达': 'TCP IK：可达',
    '旧版独有: _check_tcp_segment_continuous': '_check_tcp_segment_continuous',
    '两者共有: robodk_movej_diag.py': 'robodk_movej_diag.py',
    '两者共有: _flange_target_description': '_flange_target_description',
    '两者共有: Fanuc 格式': 'Fanuc 格式',
}
for name, s in marks.items():
    print('%-40s 出现 %d 次' % (name, t.count(s)))
