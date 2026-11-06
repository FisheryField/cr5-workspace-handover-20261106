# T5d: dump the +0x230 writer functions and the +0x238 producer functions, both versions
import struct
from capstone import *
from capstone.arm import *

BASE = r"D:\mydata\workspace\data\servo_fw_samples\elf"
FILES = {"D8": BASE + r"\v328d8.elf", "3150": BASE + r"\v3150.elf"}
RANGES = {
    "D8":   [("w230_fn", 0x08020A38, 0x08020E00), ("w238_fn", 0x08015398, 0x08015720)],
    "3150": [("w230_fn", 0x0801F6A4, 0x0801FAC0), ("w238_fn", 0x08014864, 0x08014C60)],
}

def sections(data):
    e_shoff = struct.unpack_from('<I', data, 0x20)[0]
    e_shentsize = struct.unpack_from('<H', data, 0x2E)[0]
    e_shnum = struct.unpack_from('<H', data, 0x30)[0]
    e_shstrndx = struct.unpack_from('<H', data, 0x32)[0]
    out = []
    for i in range(e_shnum):
        off = e_shoff + i * e_shentsize
        name, typ, flags, addr, offset, size = struct.unpack_from('<IIIIII', data, off)
        out.append(dict(name=name, typ=typ, flags=flags, addr=addr, offset=offset, size=size))
    st = out[e_shstrndx]; strtab = data[st['offset']:st['offset'] + st['size']]
    for s in out:
        n = s['name']; e = strtab.find(b'\0', n); s['sname'] = strtab[n:e].decode('latin1')
    return out

def dump(tag, data, ss, name, a, b, out):
    txt = [s for s in ss if s['sname'] == '.text'][0]
    off = txt['offset'] + (a - txt['addr'])
    code = data[off:off + (b - a)]
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB); md.detail = True
    lines = ["### %s %s %08X..%08X  (TRUE %08X..%08X)" % (tag, name, a, b, a + 0x10000, b + 0x10000)]
    # literal pool resolution: for ldr rX,[pc,#imm]
    for i in md.disasm(code, a):
        s = "%08X  %-8s %s" % (i.address, i.mnemonic, i.op_str)
        if i.mnemonic == 'ldr' and '[pc' in i.op_str:
            try:
                imm = int(i.op_str.split('#')[-1].rstrip(']'), 0)
                tgt = (i.address + 4) & ~3
                tgt += imm
                toff = txt['offset'] + (tgt - txt['addr'])
                val = struct.unpack_from('<I', data, toff)[0]
                s += "        ; [pc]->%08X = %08X" % (tgt, val)
            except Exception:
                pass
        if i.mnemonic in ('add', 'sub') and 'pc' in i.op_str:
            s += "        ; (adr)"
        lines.append(s)
    out.write("\n".join(lines) + "\n\n")

# pointer-reference hunt: find (fn|1) dword in whole image
def ptrhunt(tag, data, ss, addrs, out):
    pats = {}
    for a in addrs:
        pats[struct.pack('<I', a)] = "%08X" % a
        pats[struct.pack('<I', a | 1)] = "%08X|1" % a
    for p, nm in pats.items():
        i = data.find(p)
        while i >= 0:
            va = None
            for s in ss:
                if s['offset'] <= i < s['offset'] + s['size'] and s['addr']:
                    va = s['addr'] + i - s['offset']
            out.write("PTR %s %s at fileoff %X vaddr %s\n" % (tag, nm, i, hex(va) if va else 'none'))
            i = data.find(p, i + 1)

if __name__ == '__main__':
    with open(r"D:\mydata\workspace\t5_dumps.txt", "w", encoding="utf-8") as out:
        for tag, p in FILES.items():
            data = open(p, 'rb').read(); ss = sections(data)
            for name, a, b in RANGES[tag]:
                dump(tag, data, ss, name, a, b, out)
            ptrhunt(tag, data, ss, [0x08020A38, 0x0801F6A4, 0x08015398, 0x08014864], out)
    print("done")
