# -*- coding: utf-8 -*-
"""对比新旧两次采集的 maps，解释旧采集为何没看到变化。"""
import tarfile, pathlib, re

OLD = pathlib.Path(r"D:\mydata\codex\b\dobot-evidence-20260922\shm_focus32.tar.gz")
NEW = pathlib.Path(r"D:\mydata\workspace\data\captures\zero_shm_20260923_112646\zero_shm_20260923_112646\maps")

with tarfile.open(OLD, "r:gz") as t:
    old_maps = t.extractfile([m for m in t.getmembers() if m.name.endswith("/maps")][0]).read().decode(errors="replace")
new_maps = NEW.read_text(errors="replace")

def find(m, tag):
    print(f"\n--- {tag}：含 73a / SYSV 的行 ---")
    hits = [l for l in m.splitlines() if "73a" in l.lower() or "SYSV" in l]
    for l in hits[:20]:
        print("   ", l[:110])
    if not hits: print("    （无）")

find(old_maps, "旧采集 11:02")
find(new_maps, "新采集 11:26")

# 旧采集 main 的目标地址 = 0x73a40000
print("\n--- 旧脚本要读的地址 0x73A40000 在旧 maps 中是否被映射 ---")
def mapped(m, addr):
    for l in m.splitlines():
        mm = re.match(r"([0-9a-f]+)-([0-9a-f]+)\s+(\S+)", l)
        if not mm: continue
        a, b = int(mm.group(1), 16), int(mm.group(2), 16)
        if a <= addr < b:
            return f"YES  {l[:100]}"
    return "NO（未映射 → dd 读到的是空洞，全是 0）"
print("  旧 maps:", mapped(old_maps, 0x73A40000))
print("  新 maps:", mapped(new_maps, 0x73A40000))
print("\n--- 该地址在两次采集里分别属于哪个段 ---")
for tag, m in (("旧", old_maps), ("新", new_maps)):
    for l in m.splitlines():
        mm = re.match(r"([0-9a-f]+)-([0-9a-f]+)\s+(\S+)\s+\S+\s+\S+\s+(\S+)\s*(.*)", l)
        if mm and "SYSV" in l and int(mm.group(1),16) <= 0x73A84000 < int(mm.group(2),16):
            print(f"  {tag}: {l[:110]}")
