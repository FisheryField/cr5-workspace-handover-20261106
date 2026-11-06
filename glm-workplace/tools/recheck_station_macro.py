# -*- coding: utf-8 -*-
"""实时复核（只读，不保存站、不碰控制器）：
RoboDK 站内「TCP真实运动」宏的嵌入代码是否仍与升级版源逐字一致。
结果同时写 UTF-8 日志，避免控制台中文乱码。
"""
import traceback

LOG_PATH = r'D:\mydata\glm-workplace\tools\recheck_station_macro.log'
SRC_PATH = r'D:\mydata\glm-workplace\sim_scripts\TCP真实运动_升级版.py'

log_lines = []


def log(msg):
    print(msg)
    log_lines.append(str(msg))


def nm(x):
    """ItemList 元素可能是名字(str)也可能是 Item，统一转可读名字。"""
    if isinstance(x, str):
        return x
    try:
        return x.Name()
    except Exception:
        return repr(x)


try:
    from robodk.robolink import Robolink

    RDK = Robolink()
    log('connected to RoboDK, version: %s' % RDK.Version())

    # 站内 Python 宏清单（Type 10）
    macros = RDK.ItemList(10)
    log('python macro count: %d' % len(macros))
    for m in macros:
        log('  macro: %s' % nm(m))

    # 目标项
    item = RDK.Item('TCP真实运动')
    t = item.Type()
    log('item "TCP真实运动" type: %d (10 = Python 宏)' % t)

    code = item.setParam('Code')          # 只读用法：读回嵌入代码
    norm = code.replace('<br>', '\n')     # <br> 解码为换行
    with open(SRC_PATH, 'r', encoding='utf-8') as f:
        src = f.read()

    log('station code: %d chars / %d lines' % (len(norm), norm.count('\n') + 1))
    log('disk source: %d chars / %d lines' % (len(src), src.count('\n') + 1))
    log('EXACT_MATCH: %s' % (norm == src))

    if norm != src:
        mlen = min(len(norm), len(src))
        i = 0
        while i < mlen and norm[i] == src[i]:
            i += 1
        log('first diff at char index %d' % i)
        log('station[...]: %r' % norm[max(0, i - 60):i + 80])
        log('disk  [...]: %r' % src[max(0, i - 60):i + 80])

    # 关键升级点抽查（在站内码里直接找锚点）
    anchors = [
        ('_plan_cache = {}', '规划缓存初始化'),
        ('def _retreat_orientation_records', '退让展开函数'),
        ('def _plan_continuous_trajectory', '连续规划器'),
        ('def _tcp_target_to_flange', 'TCP→法兰换算'),
        ('spin360', '自转360标记'),
        ('磨砂圆柱_R180_H40', '障碍物含轮'),
    ]
    for a, desc in anchors:
        log('anchor [%s] %s: %s' % (desc, a, a in norm))

except Exception as e:
    log('ERROR: %r' % (e,))
    log(traceback.format_exc())

with open(LOG_PATH, 'w', encoding='utf-8') as f:
    f.write('\n'.join(log_lines))
print('LOG_WRITTEN')
