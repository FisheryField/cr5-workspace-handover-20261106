# -*- coding: utf-8 -*-
"""把 _single_move_settle 整块替换为 v10 最终版，并确保 MOVE_OFFSET_TOL 已定义。"""
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, 'utf-8', errors='replace', line_buffering=True)

PATH = r'D:\mydata\glm-workplace\sim_scripts\TCP真实运动_升级版.py'
src = io.open(PATH, encoding='utf-8').read()
lines = src.splitlines(True)

start = next(i for i, l in enumerate(lines) if l.startswith('def _single_move_settle(method, target):'))
end = next(i for i, l in enumerate(lines) if l.startswith('MOVE_SEGMENT_MAX_DEG'))

NEW = '''def _single_move_settle(method, target):
    """发一条运动指令并确认到位（v10：反馈字段已校正）。

    历史结论：驱动一直正确执行绝对关节目标；此前"半路停止"源于旧反馈误读偏移432
    （那字段是"连接基准+指令累加"的假关节角，v7/v8/v9三轮全被它误导，连"目标关节
    回原点走到一半停"也是它：v9按假起点68.4°分2瓣，臂物理走到第1瓣~34°即被假校验
    中止）。真实关节角在偏移192（2026-10-09双帧扫描定位+示教器交叉证实）。
    本函数：发指令→等物理收尾→用192字段核验到位；驱动假报断连时同样等收尾后
    核验（不重发）。"""
    try:
        getattr(robot, method)(target)
    except StoppedError as exc:
        if str(exc).strip() != 'Robot not connected':
            raise
        log('驱动报断连——等待当前运动自然收尾（不重发指令）…')
        actual, is_static = _wait_controller_static()
        if not is_static:
            raise RuntimeError('驱动报断连后等待%.0fs仍未静止，停止。' % 20.0) from exc
        err = max(abs(a - b) for a, b in zip(actual, target))
        if err > MOVE_OFFSET_TOL:
            raise RuntimeError('断连收尾后未到位：目标%s，实测%s（误差%.2f°），停止待判读。'
                               % (['%.2f' % v for v in target], ['%.2f' % v for v in actual], err)) from exc
        for _retry in range(3):
            if ensure_connected():
                break
            time.sleep(1.0)
        else:
            raise RuntimeError('已到位但驱动重连失败，停止后续指令。') from exc
        log('驱动断连但运动已自然完成到位；已重连驱动，继续。')
        return
    actual, is_static = _wait_controller_static()
    if not is_static:
        raise RuntimeError('指令返回后等待静止超时（20s），停止。')
    err = max(abs(a - b) for a, b in zip(actual, target))
    if err > MOVE_OFFSET_TOL:
        raise RuntimeError('落点偏差%.2f°：目标%s，实测%s，停止待判读。'
                           % (err, ['%.2f' % v for v in target], ['%.2f' % v for v in actual]))
    return


MOVE_OFFSET_TOL = 0.5   # 到位容差（°）：反馈字段校正后，超过即停止待判读


'''

lines[start:end] = [NEW]
io.open(PATH, 'w', encoding='utf-8', newline='').writelines(lines)

# 校验
import ast
src2 = io.open(PATH, encoding='utf-8').read()
ast.parse(src2)
assert 'MOVE_OFFSET_TOL = 0.5' in src2
assert "packet, 192" in src2
assert 'placeholder' not in src2 and 'useless' not in src2
ver = [l for l in src2.splitlines() if 'LOG_VERSION' in l and '=' in l][0].strip()
print('语法OK', len(src2.splitlines()), '行 ｜', ver)
