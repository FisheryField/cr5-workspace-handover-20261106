#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 .rdk 解出的文本流里提取全部内嵌 Python 宏，命名归档并比对磁盘版本。"""
import io, re, os, hashlib

SRC = r"D:\mydata\glm-workplace\data\scripts_ref\rdk_extract.txt"
OUT = r"D:\mydata\glm-workplace\data\scripts_ref"
text = io.open(SRC, encoding="utf-8", errors="replace").read()

markers = [m.start() for m in re.finditer(r"# -\*- coding: utf-8 -\*-", text)]
print("coding markers:", len(markers))

def utf16_names_near(pos_back):
    """在脚本起始标记之前的 600 字符里找 UTF-16LE 编码的条目名。"""
    ctx = text[max(0, pos_back - 600):pos_back]
    # UTF-16LE 汉字/字母序列：字符间夹 \x00
    m = re.findall(r"(?:[\u4e00-\u9fffA-Za-z0-9_]\x00){3,}", ctx)
    out = []
    for s in m:
        out.append(s.replace("\x00", ""))
    return out

extracted = []
for idx, start in enumerate(markers):
    end_m = re.search(r"root\.mainloop\(\)", text[start:])
    if not end_m:
        print("no mainloop end for marker", idx)
        continue
    end = start + end_m.end()
    code = text[start:end]
    names = utf16_names_near(start)
    # 时间戳快照名（如 TCP仿真_20260910_170410）
    tag = names[-1] if names else "unnamed"
    tag = re.sub(r"[^\w\u4e00-\u9fff]+", "_", tag)[:40]
    fn = os.path.join(OUT, "rdk_embedded_%02d_%s.py" % (idx, tag))
    io.open(fn, "w", encoding="utf-8", newline="\n").write(code)
    md5 = hashlib.md5(code.encode("utf-8")).hexdigest()
    # 首行特征（docstring 标题）
    title = ""
    t = re.search(r'"""(.{0,80})', code)
    if t:
        title = t.group(1).strip().replace("\n", " ")
    if not title:
        t2 = re.search(r'log\("([^"]{0,80})', code)
        title = t2.group(1) if t2 else ""
    extracted.append((idx, fn, tag, len(code), md5, title))
    print("== embedded %02d == name=%s chars=%d md5=%s" % (idx, tag, len(code), md5))
    print("   title:", title[:90])

print()
print("== 与磁盘版本比对 ==")
disk = {
    "RoboDK files 2\\机械臂TCP仿真.py": r"D:\mydata\glm-workplace\data\scripts_ref\TCP仿真_roboDK_files2.py",
    "workspace\\机械臂TCP仿真.py": r"D:\mydata\glm-workplace\data\scripts_ref\TCP仿真_workspace.py",
    "本工作区 test.py": r"D:\mydata\glm-workplace\test.py",
}
disk_data = {}
for k, p in disk.items():
    d = io.open(p, encoding="utf-8", errors="replace").read()
    disk_data[k] = d
    print("%-36s chars=%d md5=%s" % (k, len(d), hashlib.md5(d.encode("utf-8")).hexdigest()))

for idx, fn, tag, n, md5, title in extracted:
    code = io.open(fn, encoding="utf-8").read()
    for k, d in disk_data.items():
        # 归一化行尾后比较
        a = code.replace("\r\n", "\n").strip()
        b = d.replace("\r\n", "\n").strip()
        if a == b:
            print("embedded %02d (%s) == %s  ★完全一致" % (idx, tag, k))
        else:
            # 部分重叠度
            common = os.path.commonprefix([a, b])
            if len(common) > 500:
                print("embedded %02d (%s) ~ %s：前 %d 字符相同后分叉" % (idx, tag, k, len(common)))

# 退让逻辑检查
print()
print("== 内嵌脚本里是否有退让(_retreat_orientation_records)==")
for idx, fn, tag, n, md5, title in extracted:
    code = io.open(fn, encoding="utf-8").read()
    has = "_retreat_orientation_records" in code or "退让" in code
    print("embedded %02d %-28s retreat=%s" % (idx, tag, "YES" if has else "no"))
