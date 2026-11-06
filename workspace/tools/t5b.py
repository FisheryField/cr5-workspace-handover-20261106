# T5b: resync disassembly + address-space verification
import struct
from capstone import *
from capstone.arm import *

BASE = r"D:\mydata\workspace\data\servo_fw_samples\elf"
FILES = {"D8": BASE + r"\v328d8.elf", "3150": BASE + r"\v3150.elf"}
BIN = BASE + r"\v3150.bin"

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
    st = out[e_shstrndx]
    strtab = data[st['offset']:st['offset'] + st['size']]
    for s in out:
        n = s['name']; e = strtab.find(b'\0', n)
        s['sname'] = strtab[n:e].decode('latin1')
    return out

def full_disasm(data, ss):
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    md.detail = True
    insns = []
    for s in ss:
        if not ((s['flags'] & 0x4) and s['typ'] == 1 and s['size']):
            continue
        code = data[s['offset']:s['offset'] + s['size']]
        base = s['addr']
        off = 0
        n = len(code)
        while off < n:
            got = False
            for i in md.disasm(code[off:off + 256], base + off):
                insns.append(i); got = True
            if got:
                last = insns[-1]
                noff = last.address + last.size - base
                off = noff if noff > off else off + 2
            else:
                off += 2
    insns.sort(key=lambda x: x.address)
    return insns

def verify_addrs():
    b = open(BIN, 'rb').read()
    print("payload v3150.bin len=%d  head=%s" % (len(b), b[:8].hex()))
    for pat in [b"DS.3.1.5.0", b"DS.3.2.D.8"]:
        print("payload find %r -> %s" % (pat, [hex(x) for x in [i for i in range(len(b)) if b.startswith(pat, i)][:5]]))
    for tag, p in FILES.items():
        d = open(p, 'rb').read()
        ss = sections(d)
        print(tag, "sections:", [(s['sname'], hex(s['addr']), hex(s['size']), hex(s['offset'])) for s in ss if s['size']])
        for pat in [b"DS.3.1.5.0", b"DS.3.2.D.8"]:
            locs = []
            i = d.find(pat)
            while i >= 0 and len(locs) < 5:
                locs.append(i); i = d.find(pat, i + 1)
            va = []
            for l in locs:
                for s in ss:
                    if s['offset'] <= l < s['offset'] + s['size']:
                        va.append(hex(s['addr'] + l - s['offset']))
            print("  ", tag, pat, "fileoff", [hex(x) for x in locs], "vaddr", va)

if __name__ == '__main__':
    verify_addrs()
