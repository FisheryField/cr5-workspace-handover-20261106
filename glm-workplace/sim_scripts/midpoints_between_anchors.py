# -*- coding: utf-8 -*-
"""轨迹14 中间点简化重设（2026-10-21 用户方案）：
前后锚点几何中点 + 原位完成姿态过渡——
- 槽1 P6/P7 在 P5(0,-719,380,90) 与 P8(0,-706,380,180) 的中点 (0,-712.5,380)：P6 保持 P5 向，P7 换到 P8 向；
- 槽2 P13/P14/P15 在 P12(0,-706,380,180/180) 与 P16(40,-694,380,90/90) 之间 (y=-700)：
  P13 平移保持 P12 向 → P14 原位换向 → P15 x 对齐 P16。
"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

JSON = r'D:\mydata\working things\dobot_arm\RoboDK files 2\连续轨迹14.json'
recs = json.load(open(JSON, encoding='utf-8'))
V = {i: [float(t) for t in recs[i - 1]['values']] for i in range(1, 22)}

# 锚点确认
print('锚点 P5', V[5], '\n锚点 P8', V[8], '\n锚点 P12', V[12], '\n锚点 P16', V[16])

mid1_y = (V[5][1] + V[8][1]) / 2.0      # -712.5
recs[5]['values']  = [0.0, mid1_y, V[5][2],  90.0, 0.0, 0.0]    # P6：中点·P5 向
recs[6]['values']  = [0.0, mid1_y, V[5][2], 180.0, 0.0, 0.0]    # P7：中点·P8 向（原位换姿）

mid2_y = (V[12][1] + V[16][1]) / 2.0    # -700.0
mid2_x = (V[12][0] + V[16][0]) / 2.0    # 20.0
recs[12]['values'] = [mid2_x, mid2_y, V[12][2], 180.0, 0.0, 180.0]  # P13：中点·P12 向
recs[13]['values'] = [mid2_x, mid2_y, V[12][2],  90.0, 0.0,  90.0]  # P14：原位换 P16 向
recs[14]['values'] = [V[16][0], mid2_y, V[12][2], 90.0, 0.0, 90.0]  # P15：x 对齐 P16

with open(JSON, 'w', encoding='utf-8', newline='\n') as f:
    json.dump(recs, f, indent=2, ensure_ascii=False); f.write('\n')

for i in (6, 7, 13, 14, 15):
    print('P%-2d %s' % (i, recs[i - 1]['values']))
print('已写回:', JSON)
