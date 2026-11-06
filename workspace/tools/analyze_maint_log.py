# -*- coding: utf-8 -*-
"""分析工厂维护工具日志：参数索引编码、SDO 读写、以及它到底做了什么。"""
import pathlib, re, collections, sys

D = pathlib.Path(r"D:\software\dobot\V1.3.4-stable\Log-RobotMaintenanceTools")
logs = sorted(D.glob("*.log"), key=lambda p: p.stat().st_mtime)
print("=== 日志文件 ===")
for p in logs:
    print(f"   {p.stat().st_size:>10,} B  {p.name}")

target = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else logs[-1]
print(f"\n=== 分析 {target.name} ===")
text = target.read_text(errors="replace")
lines = text.splitlines()
print(f"行数 {len(lines):,}")

idx = [int(m) for m in re.findall(r"intParamIndex (\d+)", text)]
print(f"\nintParamIndex 出现 {len(idx)} 次；去重 {len(set(idx))} 个")
if idx:
    print(f"   最小 {min(idx)}  最大 {max(idx)}")
    print(f"   前 12 个: {idx[:12]}")
    print(f"   后 12 个: {idx[-12:]}")
    # 观察编码规律
    pref = collections.Counter(str(i)[:4] for i in set(idx))
    print(f"   前 4 位分布: {dict(pref)}")
    suf = sorted(set(str(i)[4:] for i in set(idx)))
    print(f"   后 2 位: {suf[:20]}{' …' if len(suf) > 20 else ''}")

print("\n=== 含 sdo / SDO / slave / index 的行（前 30）===")
for i, l in enumerate(lines):
    if re.search(r"\bsdo\b|SDO|slave|Slave", l):
        print(f"   {i}: {l.strip()[:190]}")
        if i > 4000: break

print("\n=== 关键动作行（import/read/write/upgrade/update/success/fail）===")
KEY = re.compile(r"importServoParamsExcel|delegateServoParamsTable|readServo|writeServo|modifyServo|success|fail|error|升级|写入|读取", re.I)
shown = 0
for l in lines:
    if KEY.search(l) and shown < 45:
        print("   " + l.strip()[:190]); shown += 1
