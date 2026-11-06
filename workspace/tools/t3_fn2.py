# -*- coding: utf-8 -*-
"""T3 v3: identify the object whose +0x26 / +0x32 fields are touched near true 0x080215A6
(doc claimed 0x08021606 ldrb r0,[r4,#0x32]) and compare with the D8 counterpart.
Naive in-region base tracker: seeds from every PC-relative literal, propagates add/mov.
"""
import struct
from capstone import *
from capstone.arm import *

OUT = open(r"D:\mydata\workspace\tools\t3_fn2_out.txt", "w", encoding="utf-8")


def P(*a):
    OUT.write(" ".join(str(x) for x in a) + "\n")


def u16(b, o):
    return struct.unpack_from('<H', b, o)[0]


def u32(b, o):
    return struct.unpack_from('<I', b, o)[0]


def load(path):
    raw = open(path, 'rb').read()
    e_shoff = u32(raw, 0x20); es = u16(raw, 0x2e); en = u16(raw, 0x30)
    secs = []
    for i in range(en):
        o = e_shoff + i * es
        secs.append(struct.unpack_from('<IIIIII', raw, o))
    c = [s for s in secs if s[1] == 1 and s[3] >= 0x08000000]
    s = max(c, key=lambda z: z[5])
    return raw, s[4], s[3], s[5]


MD = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
MD.detail = True
MD.skipdata = True
TRUE0 = 0x08010000


def run(tag, path, a0, a1):
    raw, bo, bv, sz = load(path)
    fo = lambda t: bo + (t - TRUE0)
    code = raw[bo:bo + sz]
    insns = []
    for i in MD.disasm(code, TRUE0):
        try:
            i.operands
        except Exception:
            continue
        if i.id == 0:
            continue
        insns.append(i)
    P("=" * 100)
    P("### %s tracker over true %08x..%08x  (literal annotation for loads)" % (tag, a0, a1))
    rb = {}
    for ins in insns:
        if not (a0 <= ins.address < a1):
            continue
        mn = ins.mnemonic
        # literal loads
        if len(ins.operands) >= 2:
            m = ins.operands[-1]
            if m.type == ARM_OP_MEM and m.mem.base == ARM_REG_PC:
                t = ((ins.address + 4) & ~3) + m.mem.disp
                o = fo(t)
                if 0 <= o < len(raw) - 4:
                    v = struct.unpack_from('<I', raw, o)[0]
                    if ins.operands[0].type == ARM_OP_REG:
                        rb[ins.operands[0].reg] = v
                    P("  %08x  %-28s -> %08x" % (ins.address, mn + " " + ins.op_str, v))
        for op in ins.operands:
            if op.type == ARM_OP_MEM and op.mem.base in rb and op.mem.base != ARM_REG_PC:
                P("      MEM %s +0x%x  base=%08x  @%08x  %s" %
                  ("W" if (op.access & CS_AC_WRITE) else "R", op.mem.disp, rb[op.mem.base], ins.address, mn + " " + ins.op_str))
        if mn in ('add', 'add.w', 'adds', 'mov', 'mov.w', 'movs', 'sub', 'sub.w', 'adr'):
            if len(ins.operands) >= 2 and ins.operands[0].type == ARM_OP_REG:
                d = ins.operands[0].reg
                srcs = [o.reg for o in ins.operands[1:] if o.type == ARM_OP_REG]
                hit = [s for s in srcs if s in rb]
                if hit:
                    rb[d] = rb[hit[0]]
                else:
                    rb.pop(d, None)
        else:
            if len(ins.operands) >= 1 and ins.operands[0].type == ARM_OP_REG and not mn.startswith('v') and ins.operands[0].reg != ARM_REG_PC:
                rb.pop(ins.operands[0].reg, None)
    # plain listing of two windows
    for (w0, w1) in ((a0 + 0x500, a0 + 0x620), (a1 - 0x120, a1)):
        P("--- listing %08x..%08x" % (w0, w1))
        for ins in insns:
            if w0 <= ins.address < w1:
                note = ""
                for op in ins.operands:
                    if op.type == ARM_OP_MEM and op.mem.base == ARM_REG_PC:
                        t = ((ins.address + 4) & ~3) + op.mem.disp
                        o = fo(t)
                        if 0 <= o < len(raw) - 4:
                            note = "   ; = %08x" % struct.unpack_from('<I', raw, o)[0]
                P("  %08x  %-10s %-32s%s" % (ins.address, ins.bytes.hex(), ins.mnemonic + " " + ins.op_str, note))


run("3150", r"D:\mydata\workspace\data\servo_fw_samples\elf\v3150.elf", 0x08021000, 0x08021620)
run("d8", r"D:\mydata\workspace\data\servo_fw_samples\elf\v328d8.elf", 0x08021860, 0x08021E80)
OUT.close()
print("done")
