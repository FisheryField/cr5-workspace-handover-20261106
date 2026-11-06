# -*- coding: utf-8 -*-
"""轨迹16 自动修复（traj14 方法论）：底版=连续轨迹13_t126_z460，
场景=当前（滚轮 y=-886 z=460）。循环：预检 → 失败分类 → 规则化改 y/z → 重试。
规则：
 - 点无逆解        → 该点 z −5
 - P2 类碰撞死区    → 前3轮：高排 z 整体 −10；之后：P2 y +4（最多到 +16）
 - P_other 碰撞死区 → 该点 y +3（最多 +12）
- 最多 14 轮；收敛即存 连续轨迹16.json（原版均不动）。"""
import sys, io, json, copy, re, shutil, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
from robodk import robolink

BASE = r'D:\mydata\working things\dobot_arm\RoboDK files 2\连续轨迹13_t126_z460.json'
OUT = r'D:\mydata\working things\dobot_arm\RoboDK files 2\连续轨迹16.json'

RDK = robolink.Robolink()
robot = RDK.Item('', robolink.ITEM_TYPE_ROBOT)
print('PoseTool =', robot.PoseTool().Pos())
src = open(r'D:\mydata\glm-workplace\sim_scripts\TCP真实运动_P2P版.py', encoding='utf-8').read()
lines = src.splitlines()
stop = next(i for i, l in enumerate(lines) if l.startswith('root = tk.Tk()'))
ns = {}
exec(compile('\n'.join(lines[:stop]), 'p2p_head', 'exec'), ns)
ns['_ensure_canonical_tool']()

records = json.load(open(BASE, encoding='utf-8'))
print('底版点数 =', len(records), '（轨迹13 z460 @126）')

def row_idx(recs):
    return [k for k, r in enumerate(recs)
            if r['type'] == 'TCP' and float(r['values'][2]) >= 450.0 and not r.get('singular', False)]

def run_precheck(recs):
    exp = ns['_retreat_orientation_records'](copy.deepcopy(recs))
    robot.setJoints([0.0] * 6)
    RDK.setRunMode(robolink.RUNMODE_SIMULATE)
    try:
        plan = ns['_plan_continuous_trajectory'](exp, 500.0, lambda m: None)
        RDK.setRunMode(robolink.RUNMODE_RUN_ROBOT)
        return True, plan, None
    except ValueError as e:
        RDK.setRunMode(robolink.RUNMODE_RUN_ROBOT)
        return False, None, str(e)

def shift(pi, field, delta):
    """改 records[pi] 的 field，并链式同步其后的奇异点：
    自转(±360)数值全同；±180翻转只同步 xyz（姿态保留翻转点自身的）。"""
    v = records[pi]['values']
    idx = {'x': 0, 'y': 1, 'z': 2}[field]
    v[idx] = round(float(v[idx]) + delta, 3)
    k = pi + 1
    while k < len(records) and records[k].get('singular'):
        d = abs(int(records[k].get('j6_delta', 180)))
        if d == 360:
            records[k]['values'] = list(v)
        else:
            records[k]['values'] = list(v[:3]) + list(records[k]['values'][3:])
        k += 1

p2_rounds = 0
for rnd in range(1, 15):
    print('\n----- 第 %d 轮 -----' % rnd)
    ok, plan, err = run_precheck(records)
    if ok:
        print('=== 收敛！预检通过 %d 段 ===' % len(plan))
        open(OUT, 'w', encoding='utf-8').write(json.dumps(records, indent=2, ensure_ascii=False) + '\n')
        print('已保存 =', OUT)
        base = json.load(open(BASE, encoding='utf-8'))
        for k, (a, b) in enumerate(zip(base, records)):
            if a['values'] != b['values']:
                print('  P%-2d %s -> %s' % (k + 1, a['values'], b['values']))
        print('RESULT: PASS')
        break
    print('失败：', err[:160])
    m = re.search(r'P(\d+)', err)
    pi = int(m.group(1)) - 1 if m else 1
    if '完全相同' in err:
        # 自转点与前点失配 → 全量对齐
        records[pi]['values'] = list(records[pi - 1]['values'])
        print('  规则0：P%d 自转点数值对齐前点' % (pi + 1))
        continue
    if '仅旋转J6无法到达' in err:
        shift(pi - 1, 'y', 3.0)
        print('  规则0b：翻转点失效 → 前一点 y +3 → %.1f（链同步）' % float(records[pi - 1]['values'][1]))
        continue
    if '没有逆解' in err:
        shift(pi, 'z', -5.0)
        print('  规则1：P%d z −5 → %.1f（链同步）' % (pi + 1, float(records[pi]['values'][2])))
    elif pi <= 2:
        shift(1, 'y', 4.0)   # P2
        shift(2, 'y', 4.0)   # P3（连带 P4 翻转点链同步）
        print('  规则2：P2/P3 耦合 y +4 → P2=%.1f P3=%.1f' % (
            float(records[1]['values'][1]), float(records[2]['values'][1])))
        if float(records[1]['values'][1]) >= -675.0:
            print('P2/P3 y 到 +24 上限（−675），停止')
            break
    else:
        shift(pi, 'y', 3.0)
        print('  规则3：P%d y +3 → %.1f（链同步）' % (pi + 1, float(records[pi]['values'][1])))
print('DONE')
