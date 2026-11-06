# v14m 落地后语法+指纹自检（嵌入式 python 运行）
import ast, io, sys

PATH = r'D:\mydata\glm-workplace\sim_scripts\TCP真实运动_P2P版.py'
src = io.open(PATH, encoding='utf-8').read()

# 1) ast.parse
ast.parse(src)
print('[1] ast.parse OK')

# 2) 指纹：v14m 版本串在位、v14k 版本串消失、步长=40、v14l 残留为 0
assert 'v14m-20261012-1645' in src, 'v14m 版本串缺失'
assert 'v14k-20261012-1040' not in src, 'v14k 版本串残留'
import re
m = re.search(r'^LINEAR_SUBSTEP_MM = ([0-9.]+)', src, re.M)
assert m and float(m.group(1)) == 40.0, 'LINEAR_SUBSTEP_MM != 40'
for token in ('MOVL_TRIAL_MAX_MM', '_movl_trial_ready', 'MOVL试航'):
    assert token not in src, 'v14l 残留: ' + token
print('[2] 指纹 OK：v14m 版本串在位、步长 40.0、v14l 残留 0 处')

# 3) 防呆护栏仍在（驱动 MOVL 拒发）
assert '拒绝发送驱动 MOVL' in src, '驱动 MOVL 防呆护栏丢失'
print('[3] 防呆护栏在位：MoveL 步缺途经点 → 拒发驱动 MOVL')
print('ALL OK')
