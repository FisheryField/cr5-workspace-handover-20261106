import sys
sys.path.insert(0, r"D:\mydata\workspace\.pylibs")
sys.path.insert(0, r"D:\mydata\workspace\tools")
import struct
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
from libdata_strrefs import Elf
e = Elf()
d = e.d
# .text: find section containing 0x11aafc
for s in e.secs:
    if s["addr"] and s["addr"] <= 0x11aafc < s["addr"]+s["size"] and s["type"]==1:
        print("in section", s["name"], hex(s["addr"]), hex(s["offset"]))
        base_off = s["offset"] + (0x11aafc - s["addr"])
        print("file off:", hex(base_off))
        cs = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
        start = base_off - 0x400
        code = d[start:start+0xA00]
        for insn in cs.disasm(code, 0x11aafc-0x400):
            mark = " <<<" if abs(insn.address-0x11aafc) < 8 else ""
            print("0x%08x  %-8s %s%s" % (insn.address, insn.mnemonic, insn.op_str, mark))
        break
