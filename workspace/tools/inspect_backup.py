# -*- coding: utf-8 -*-
"""拆 9/16 控制器备份：zip(pwd=dobot123) -> tar.gz -> 解压 + 清单。"""
import zipfile, tarfile, io, collections, pathlib, re, sys

ZIP = pathlib.Path(r"D:\mydata\working things\CR5_CC162_V3.5.4.1-stable-a014bd6f-2212301029_20260916_Backup.zip")
OUT = pathlib.Path(r"D:\mydata\workspace\data\backup_20260916")
PWD = b"dobot123"

with zipfile.ZipFile(ZIP) as z:
    inner = z.namelist()[0]
    tgz = z.read(inner, pwd=PWD)
print(f"内层 {inner}  ({len(tgz)} B)")

with tarfile.open(fileobj=io.BytesIO(tgz), mode="r:gz") as t:
    members = t.getmembers()
files = [m for m in members if m.isfile()]
print(f"tar 成员 {len(members)}（文件 {len(files)}，目录 {len(members)-len(files)}），解压后 {sum(m.size for m in files)/1048576:.2f} MB")

agg, aggbytes = collections.Counter(), collections.Counter()
for m in files:
    parts = m.name.split("/")
    key = "/".join(parts[:2]) if len(parts) > 2 else m.name
    agg[key] += 1; aggbytes[key] += m.size
print("\n--- 顶层聚合 ---")
for k, n in agg.most_common(20):
    print(f"   {n:5d} 个 {aggbytes[k]/1024:10.1f} KB  {k}")

KEY = re.compile(r"homeEncoder|setting|calibrat|zero|servo|robotType|Recipe|SavePos|SaveAxes|persist", re.I)
print("\n--- 关键文件 ---")
for m in sorted(files, key=lambda x: x.name):
    if KEY.search(m.name):
        print(f"   {m.size:9d}  {m.name}")

OUT.mkdir(parents=True, exist_ok=True)
with tarfile.open(fileobj=io.BytesIO(tgz), mode="r:gz") as t:
    t.extractall(OUT)
print("\n已解压到", OUT)
