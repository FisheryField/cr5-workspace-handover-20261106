# -*- coding: utf-8 -*-
"""对比任意多份 zeroprobe 指纹。用法: compare_multi.py <dir1> <dir2> [dir3 ...]"""
import pathlib, struct, re, sys, json

def load(d):
    d = pathlib.Path(d)
    st = (d/"state.txt").read_text(errors="replace")
    r = {"name": d.name}
    i = st.find("homeEncoder.json ==")
    if i >= 0:
        s = st.find("{", i); depth = 0; end = -1
        for k in range(s, len(st)):
            if st[k] == "{": depth += 1
            elif st[k] == "}":
                depth -= 1
                if depth == 0: end = k+1; break
        if s >= 0 and end > s:
            try:
                j = json.loads(st[s:end]); last = j["encoder"][-1]
                r["he_time"] = last.get("time"); r["he_count"] = len(j.get("encoder", []))
                r["he_inner"] = last.get("innerEncoder")
            except Exception as e: r["he_err"] = str(e)
    m = re.search(r"^([\d.]+) [\d.]+$", st.split("== 控制器")[0], re.M)
    if m: r["uptime"] = float(m.group(1))
    m = re.search(r"pid=(\d+)", st); r["pid"] = m.group(1) if m else "?"
    for pg in (64, 132):
        f = d/f"page_{pg}.bin"
        if f.exists():
            b = f.read_bytes()
            r[f"f0_{pg}"] = [round(struct.unpack_from("<f", b, 0xE24+40*i)[0], 3) for i in range(6)]
            r[f"f1_{pg}"] = [round(struct.unpack_from("<f", b, 0xE2C+40*i)[0], 3) for i in range(6)]
    f = d/"page_133.bin"
    if f.exists():
        b = f.read_bytes()
        r["pose"] = [round(struct.unpack_from("<f", b, 0x04+4*i)[0], 4) for i in range(6)]
    return r

S = [load(p) for p in sys.argv[1:]]
def row(label, key, fmt=lambda v: str(v)):
    print(f"  {label:22}" + "".join(f"{fmt(s.get(key)):>26}" for s in S))
print("指纹对比：" + "".join(f"{s['name']:>26}" for s in S))
row("uptime(s)", "uptime", lambda v: f"{v:.0f}" if v else "?")
row("pid", "pid")
row("homeEncoder 末条", "he_time")
row("homeEncoder 条数", "he_count")
print()
row("TCP pose x", "pose", lambda v: f"{v[0]:.3f}" if v else "?")
row("TCP pose ry", "pose", lambda v: f"{v[4]:.3f}" if v else "?")
print()
for pg in (64, 132):
    for fld in ("f0", "f1"):
        row(f"page{pg} {fld} 轴1-3", f"{fld}_{pg}", lambda v: str(v[:3]) if v else "?")
        row(f"page{pg} {fld} 轴4-6", f"{fld}_{pg}", lambda v: str(v[3:]) if v else "?")
print()
row("he innerEncoder", "he_inner")
