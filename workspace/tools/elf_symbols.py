# -*- coding: utf-8 -*-
"""检查未 strip 的 libdataSvr.so：找 SDO 相关符号与 updateEncoderData 的引用。"""
import struct, sys, re, pathlib, collections

P = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else r"D:\mydata\workspace\libdataSvr.so.bin")
data = P.read_bytes()
print(f"文件 {P.name}  {len(data):,} B")
print("ELF:", data[:4], "class:", "32" if data[4] == 1 else "64", "machine:", hex(struct.unpack_from("<H", data, 18)[0]), "(40=ARM)")
print("build-id/注释线索:")
for m in re.finditer(rb"GCC:.*?\x00|GLIBC_[0-9.]+", data[:200000]):
    pass

# --- 解析节头找符号表 ---
is64 = data[4] == 2
if not is64:
    e_shoff, = struct.unpack_from("<I", data, 32)
    e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<HHH", data, 46)
else:
    e_shoff, = struct.unpack_from("<Q", data, 40)
    e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<HHH", data, 58)

def sh(i):
    off = e_shoff + i * e_shentsize
    if not is64:
        name, typ, flags, addr, offset, size, link, info, align, entsize = struct.unpack_from("<IIIIIIIIII", data, off)
    else:
        name, typ, flags, addr, offset, size, link, info, align, entsize = struct.unpack_from("<IIQQQQIIQQ", data, off)
    return dict(name=name, typ=typ, addr=addr, offset=offset, size=size, link=link, entsize=entsize)

secs = [sh(i) for i in range(e_shnum)]
shstr = secs[e_shstrndx]
def sname(n):
    end = data.index(b"\x00", shstr["offset"] + n)
    return data[shstr["offset"] + n:end].decode("ascii", "replace")
for s in secs:
    s["sname"] = sname(s["name"])

symtabs = [s for s in secs if s["typ"] in (2, 11)]   # SYMTAB / DYNSYM
print(f"节: {len(secs)} 个；符号表: {[s['sname'] + '(' + str(s['size']) + 'B)' for s in symtabs]}")

syms = {}
for st in symtabs:
    strtab = secs[st["link"]]
    n = st["size"] // st["entsize"] if st["entsize"] else 0
    for i in range(n):
        off = st["offset"] + i * st["entsize"]
        if not is64:
            nm, val, size, info, other, shndx = struct.unpack_from("<IIIBBH", data, off)
        else:
            nm, info, other, shndx, val, size = struct.unpack_from("<IBBHQQ", data, off)
        end = data.index(b"\x00", strtab["offset"] + nm)
        name = data[strtab["offset"] + nm:end].decode("ascii", "replace")
        if name:
            syms[name] = (val, size)
print(f"符号总数: {len(syms):,}")

KEY = re.compile(r"sdo|SDO|canopen|CanOpen|co_|ec_|encoder|Encoder|Calib|calib|Home|home|Param|param", re.I)
hits = {k: v for k, v in syms.items() if KEY.search(k)}
print(f"\n关键字相关符号 {len(hits)} 个，抽样：")
for k in sorted(hits)[:60]:
    print(f"   {hits[k][0]:#010x}  size={hits[k][1]:<6} {k[:90]}")

print("\n--- 与 SDO 直接相关的 ---")
for k in sorted(hits):
    if re.search(r"sdo", k, re.I):
        print(f"   {hits[k][0]:#010x}  size={hits[k][1]:<6} {k}")
