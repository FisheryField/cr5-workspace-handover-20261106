# -*- coding: utf-8 -*-
"""T3 v2: per-axis parameter block 0x200073A0 + axis*0x60 (v3150) -- base-tracking field scan.
ELF here is section-only, base vaddr 0x08000000 == payload byte 0, and payload byte 0 is
true flash 0x08010000  =>  TRUE = ELF_vaddr + 0x10000  (Ghidra coords = true - 0x10000).
"""
import struct, sys
from capstone import *
from capstone.arm import *

OUT = open(r"D:\mydata\workspace\tools\t3_scan2_out.txt", "w", encoding="utf-8")


def P(*a):
    s = " ".join(str(x) for x in a)
    OUT.write(s + "\n")


def u16(b, o):
    return struct.unpack_from('<H', b, o)[0]


def u32(b, o):
    return struct.unpack_from('<I', b, o)[0]


def sections(path):
    raw = open(path, 'rb').read()
    e_shoff = u32(raw, 0x20); es = u16(raw, 0x2e); en = u16(raw, 0x30); si = u16(raw, 0x32)
    secs = []
    for i in range(en):
        o = e_shoff + i * es
        nm, typ, fl, addr, off, size = struct.unpack_from('<IIIIII', raw, o)
        secs.append((nm, typ, fl, addr, off, size))
    cand = [s for s in secs if s[1] == 1 and s[3] >= 0x08000000]
    s = max(cand, key=lambda z: z[5])
    return raw, s[4], s[3], s[5]


FILES = [("3150", r"D:\mydata\workspace\data\servo_fw_samples\elf\v3150.elf"),
         ("d8", r"D:\mydata\workspace\data\servo_fw_samples\elf\v328d8.elf")]

MD = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
MD.detail = True
MD.skipdata = True
CACHE = {}

for tag, path in FILES:
    raw, base_off, base_va, size = sections(path)
    TRUE0 = 0x08010000
    assert base_va == 0x08000000, (tag, hex(base_va))
    fo = lambda t: base_off + (t - TRUE0)
    P("=" * 100)
    P("### %s  %s  filesize=%d  PROGBITS off=%x va=%x size=%x  => TRUE = vaddr+0x10000 ; TRUE0=%08x"
      % (tag, path.split('\\')[-1], len(raw), base_off, base_va, size, TRUE0))
    code = raw[base_off:base_off + size]
    def _ok(i):
        try:
            i.operands
            return i.id != 0
        except Exception:
            return False
    insns = [i for i in MD.disasm(code, TRUE0) if _ok(i)]
    P("instructions decoded: %d" % len(insns))
    byaddr = {i.address: k for k, i in enumerate(insns)}
    CACHE[tag] = (raw, base_off, size, insns, byaddr, fo)

    # ---- POSITIVE CONTROL 1: known strings / version carrier, by true address and by content
    idx = raw.find(b"DS.3.1.5.0")
    P("PC1a raw find b'DS.3.1.5.0' at fileoff=%s true=%s" %
      (hex(idx) if idx >= 0 else None, hex(TRUE0 + idx - base_off) if idx >= 0 else None))
    idx2 = raw.find(b"DS.3.2.D.8")
    P("PC1b raw find b'DS.3.2.D.8' at fileoff=%s true=%s" %
      (hex(idx2) if idx2 >= 0 else None, hex(TRUE0 + idx2 - base_off) if idx2 >= 0 else None))

    # ---- POSITIVE CONTROL 2: known literal -> count
    for name, v in (("OD_desc_base(D8 0x2000138C)", 0x2000138C), ("OD_desc_base(3150 0x2000129C)", 0x2000129C),
                    ("fnptr_table(D8 0x20000078)", 0x20000078), ("fnptr_table(3150 0x20000074)", 0x20000074),
                    ("0x20003DB0(state)", 0x20003DB0), ("20000=0x4e20 imm", None)):
        if v is None:
            continue
        pat = struct.pack('<I', v)
        c = 0; st = 0; ex = []
        while True:
            k = raw.find(pat, st)
            if k < 0:
                break
            c += 1
            if len(ex) < 6:
                ex.append(hex(TRUE0 + k - base_off))
            st = k + 1
        P("PC2 literal %08x -> %d hits  %s" % (v, c, ex))

    # ---- enumerate all literal-pool dwords pointing into 0x20006000..0x2000A000
    famcnt = {}
    lit_sites = []          # (ins_index, ins_addr, ldr dest reg, target true addr, value)
    flash_lits = []         # pc-relative literals pointing into flash
    for i, ins in enumerate(insns):
        if len(ins.operands) < 2:
            continue
        m = ins.operands[-1] if ins.operands[-1].type == ARM_OP_MEM else ins.operands[1]
        if m.type != ARM_OP_MEM or m.mem.base != ARM_REG_PC:
            continue
        tgt = ((ins.address + 4) & ~3) + m.mem.disp
        o = fo(tgt)
        if o < 0 or o + 4 > len(raw):
            continue
        val = struct.unpack_from('<I', raw, o)[0]
        if 0x20006000 <= val < 0x2000A000:
            famcnt[val] = famcnt.get(val, 0) + 1
            dst = ins.operands[0].reg if ins.operands[0].type == ARM_OP_REG else 0
            lit_sites.append((i, ins.address, dst, tgt, val))
        elif 0x08010000 <= val < 0x08060000:
            flash_lits.append((i, ins.address, tgt, val))
    P("--- literal dwords in 0x20006000..0x2000A000 (value: count), sorted by count:")
    for v in sorted(famcnt, key=lambda x: -famcnt[x]):
        P("    %08x : %d" % (v, famcnt[v]))
    P("--- flash-directed literals: %d (sample %s)" % (len(flash_lits),
      [hex(x[3]) for x in flash_lits[:10]]))

    # ---- base tracking inside each literal-load window
    RBASES = set([v for v in famcnt if famcnt[v] >= 3])
    P("--- family bases tracked (>=3 literal sites): %s" % [hex(v) for v in sorted(RBASES)])
    fieldtbl = {}   # base -> {field: [reads, writes]}
    events = []     # (base, field, wr, addr, text)
    for (i, addr, dst, tgt, val) in lit_sites:
        if val not in RBASES:
            continue
        rb = {dst: val}
        lits = []
        prev = []
        for j in range(i, min(i + 260, len(insns))):
            ins = insns[j]
            mn = ins.mnemonic
            if j > i and mn in ('bx', 'pop', 'pop.w'):
                break
            # memory accesses via tracked base
            for op in ins.operands:
                if op.type == ARM_OP_MEM and op.mem.base in rb:
                    b = rb[op.mem.base]
                    f = op.mem.disp
                    wr = bool(op.access & CS_AC_WRITE)
                    d = fieldtbl.setdefault(b, {})
                    rw = d.setdefault(f, [0, 0])
                    rw[1 if wr else 0] += 1
                    events.append((b, f, wr, ins.address, "%s %s" % (mn, ins.op_str), tuple(prev[-6:])))
            # literal loads in window
            if len(ins.operands) >= 2:
                m2 = ins.operands[1]
                if m2.type == ARM_OP_MEM and m2.mem.base == ARM_REG_PC:
                    t2 = ((ins.address + 4) & ~3) + m2.mem.disp
                    o2 = fo(t2)
                    if 0 <= o2 < len(raw) - 4:
                        v2 = struct.unpack_from('<I', raw, o2)[0]
                        if 0x08010000 <= v2 < 0x08060000 or 0x20000000 <= v2 < 0x20010000:
                            lits.append((ins.address, hex(v2)))
            # propagate base identity
            if mn in ('add', 'add.w', 'adds', 'mov', 'mov.w', 'movs', 'adr', 'sub', 'sub.w'):
                if len(ins.operands) >= 2 and ins.operands[0].type == ARM_OP_REG:
                    d = ins.operands[0].reg
                    srcs = [op.reg for op in ins.operands[1:] if op.type == ARM_OP_REG]
                    hit = [s for s in srcs if s in rb]
                    if hit:
                        rb[d] = rb[hit[0]]
                    else:
                        rb.pop(d, None)
            else:
                if j > i and len(ins.operands) >= 1 and ins.operands[0].type == ARM_OP_REG:
                    d = ins.operands[0].reg
                    if d in rb and not mn.startswith('v'):
                        rb.pop(d, None)
            prev.append("%08x %s %s" % (ins.address, mn, ins.op_str))
        if j > i:
            P("SITE load@%08x base=%08x dst=%s | window %d insns | lits=%s"
              % (addr, val, insns[i].reg_name(dst), j - i, lits[:8]))
    P("--- per-base field table (base: field -> [reads,writes])")
    for b in sorted(fieldtbl):
        P("  %08x: %s" % (b, ", ".join("+0x%02x %s" % (f, fieldtbl[b][f]) for f in sorted(fieldtbl[b]))))
    P("--- events with field 0x26 / 0x32 / 0x34 / 0x24:")
    for (b, f, wr, a, t, cx) in events:
        if f in (0x24, 0x26, 0x32, 0x34):
            P("   %s base=%08x +0x%02x  @%08x  %s" % ("W" if wr else "R", b, f, a, t))
    P("--- ALL accesses via base 0x200073a0 (writes carry preceding context):")
    for (b, f, wr, a, t, cx) in events:
        if b == 0x200073a0:
            if wr:
                P("   W +0x%02x @%08x %s" % (f, a, t))
                for c in cx:
                    P("        prev %s" % c)
            else:
                P("   R +0x%02x @%08x %s" % (f, a, t))
    P("--- ALL accesses via base 0x20007400 / 0x20007660 / 0x200077c0:")
    for (b, f, wr, a, t, cx) in events:
        if b in (0x20007400, 0x20007660, 0x200077c0):
            P("   %s base=%08x +0x%02x @%08x %s" % ("W" if wr else "R", b, f, a, t))

    # ---- enc_type dispatch: ubfx rX,rY,#4,#3     (candidate = H01.13)
    P("--- ubfx #4,#3 sites (enc_type candidates):")
    for i, ins in enumerate(insns):
        if ins.id == ARM_INS_UBFX and len(ins.operands) == 4:
            if ins.operands[2].imm == 4 and ins.operands[3].imm == 3:
                P("  @%08x  %s %s" % (ins.address, ins.mnemonic, ins.op_str))
    # ---- candidates: any memory access at disp 0x26 / 0x34 anywhere (base unknown)
    P("--- all insns with mem disp 0x26 or 0x34 (address, text):")
    c26 = 0
    for ins in insns:
        for op in ins.operands:
            if op.type == ARM_OP_MEM and op.mem.disp in (0x26, 0x34):
                P("  @%08x  %s %s   [disp=0x%x]" % (ins.address, ins.mnemonic, ins.op_str, op.mem.disp))
                c26 += 1
    P("   total=%d" % c26)

# ---- function dump with literal annotation (encoder-type dispatch area)
RANGES = {"3150": (0x080215C0, 0x08021840), "d8": (0x08021E00, 0x080220A0)}
for tag in ("3150", "d8"):
    raw2, bo2, sz2, ins2, ba2, fo2 = CACHE[tag]
    a0, a1 = RANGES[tag]
    P("=" * 100)
    P("### FN DUMP %s true %08x..%08x" % (tag, a0, a1))
    for ins in ins2:
        if not (a0 <= ins.address < a1):
            continue
        note = ""
        for op in ins.operands:
            if op.type == ARM_OP_MEM and op.mem.base == ARM_REG_PC:
                t = ((ins.address + 4) & ~3) + op.mem.disp
                o = fo2(t)
                if 0 <= o < len(raw2) - 4:
                    v = struct.unpack_from('<I', raw2, o)[0]
                    note = "   ; lit@%08x = %08x" % (t, v)
        P("  %08x  %-10s %s%s" % (ins.address, ins.bytes.hex(), ins.mnemonic + " " + ins.op_str, note))

OUT.close()
print("done")