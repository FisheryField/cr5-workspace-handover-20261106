# -*- coding: utf-8 -*-
import re, pathlib, struct
for name in ("ecat_zero", "ecat_read", "slaveinfo_arm"):
    p = pathlib.Path(r"D:\mydata\workspace") / name
    if not p.exists():
        print(f"### {name} 不存在"); continue
    d = p.read_bytes()
    print(f"\n### {name}  {len(d):,} B  ELF={d[:4]!r} type={struct.unpack_from('<H', d, 16)[0]} machine={hex(struct.unpack_from('<H', d, 18)[0])}")
    S = [s.decode() for s in re.findall(rb"[ -~]{3,}", d)]
    for kw in ("usage:", "mode=", "sdoinfo", "slaves=%d", "rv", "wv", "home", "OD entries", "ec_init", "eth0"):
        hits = [s for s in S if kw in s]
        if hits:
            print(f"   [{kw}] " + " | ".join(dict.fromkeys(hits))[:220])
