# -*- coding: utf-8 -*-
"""对比断电前/后的 zeroprobe 指纹。用法: compare_zeroprobe.py <dirA> <dirB>"""
import pathlib, struct, re, sys, json

def load(d):
    d = pathlib.Path(d)
    st = (d/"state.txt").read_text(errors="replace")
    r = {"dir": d}
    i = st.find("homeEncoder.json ==")
    if i >= 0:
        s = st.find("{", i)
        depth = 0; end = -1
        for k in range(s, len(st)):
            if st[k] == "{": depth += 1
            elif st[k] == "}":
                depth -= 1
                if depth == 0: end = k + 1; break
        if s >= 0 and end > s:
            try:
                j = json.loads(st[s:end])
                last = j["encoder"][-1]
                r["he_time"] = last.get("time"); r["he_date"] = last.get("date")
                r["he_inner"] = last.get("innerEncoder"); r["he_outer"] = last.get("outEncoder")
                r["he_count"] = len(j.get("encoder", []))
            except Exception as e:
                r["he_err"] = str(e)
        else:
            r["he_err"] = "brace match failed"
    else:
        r["he_err"] = "marker not found"
    r["servo"] = re.findall(r'"(servo\d)"\s*:\s*"([^"]+)"', st)
    m = re.search(r"base_hex=(\S+) base_dec=(\d+)", st)
    if m: r["base"] = int(m.group(2))
    m = re.search(r"pid=(\d+)", st)
    if m: r["pid"] = m.group(1)
    m = re.search(r"^([\d.]+) ([\d.]+)$", st.split("== 控制器")[0], re.M)
    if m: r["uptime"] = m.group(1)
    # 两个实例的 6 轴
    for pg in (64, 132):
        f = d/f"page_{pg}.bin"
        if f.exists():
            b = f.read_bytes()
            r[f"enc{pg}"] = [round(struct.unpack_from("<f", b, 0xE24 + 40*i)[0], 4) for i in range(6)]
            # 记录里的第二个 float（+0x08）
            r[f"enc{pg}_b"] = [round(struct.unpack_from("<f", b, 0xE2C + 40*i)[0], 4) for i in range(6)]
    return r

A, B = load(sys.argv[1]), load(sys.argv[2])
print(f"A(断电前) {A['dir']}")
print(f"B(断电后) {B['dir']}\n")
def line(k, fmt=str):
    a = A.get(k); b = B.get(k)
    print(f"  {k:12} A={a}")
    print(f"  {'':12} B={b}")
for k in ("uptime", "pid", "base", "he_date", "he_time", "he_count", "he_err", "servo"):
    if A.get(k) is None and B.get(k) is None: continue
    line(k)
print()
print("  === homeEncoder.json 的 innerEncoder ===")
print(f"   A: {A.get('he_inner')}")
print(f"   B: {B.get('he_inner')}")
print(f"   === outEncoder ===")
print(f"   A: {A.get('he_outer')}")
print(f"   B: {B.get('he_outer')}")
print()
for pg in (64, 132):
    print(f"  === 内存实例 page {pg} @ +0xE24（每轴首字段）===")
    print(f"   A: {A.get('enc'+str(pg))}")
    print(f"   B: {B.get('enc'+str(pg))}")
    same = A.get('enc'+str(pg)) == B.get('enc'+str(pg))
    print(f"   -> {'相同' if same else '不同'}")
    print()
