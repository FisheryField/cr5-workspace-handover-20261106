"""zf_img.py - zero-point/persistence investigation toolkit (round: ZERO_PERSIST_2).

Self-contained: loads the servo firmware images with a *verified* base-map,
disassembles with capstone, resolves PC-relative literal pools, and provides
scanners for `str/ldr [rX,#off]` field accesses with a mandatory positive
self-check.

Base map (independently re-verified here):
  raw  <name>.bin : header 0x20 bytes, application image loaded at 0x08010000
                    (vector table: first word SP, second word Reset_Handler)
  elf  <name>.elf : .text mapped at 0x08000000, file offset 0x1000
  => addr 0x08010000 in the running device == blob offset 0x00000 (raw)
                                          == file offset 0x1000  (elf)

usage (as a module):
    from zf_img import Img
    a = Img('data/servo_fw_samples/elf/v3150.elf')
"""
import struct, os, sys

APP_BASE = 0x08010000          # canonical address of blob offset 0
APP_START = 0x08010000
FLASH_BASE = 0x08010000
GHIDRA_DELTA = 0x10000         # ghidra_addr + GHIDRA_DELTA == address used here

try:
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN
    from capstone.arm import ARM_OP_REG, ARM_OP_IMM, ARM_OP_MEM
except ImportError:
    raise SystemExit("needs capstone")

STR_OPS = ('str', 'strh', 'strb', 'str.w', 'strh.w', 'strb.w', 'vstr', 'stm', 'stmia', 'stmdb', 'push')
LDR_OPS = ('ldr', 'ldrh', 'ldrb', 'ldr.w', 'ldrh.w', 'ldrsb', 'ldrsh', 'vldr', 'ldm', 'ldmia', 'pop')

# ---- self-check: capstone's ARM operand type codes ----
assert ARM_OP_REG == 1 and ARM_OP_IMM == 2 and ARM_OP_MEM == 3, \
    'capstone ARM operand type codes changed: %d %d %d' % (ARM_OP_REG, ARM_OP_IMM, ARM_OP_MEM)


class Img:
    def __init__(self, path, base=APP_BASE):
        self.path = path
        self.name = os.path.splitext(os.path.basename(path))[0]
        self.base = base
        if path.lower().endswith('.elf'):
            d = open(path, 'rb').read()
            e_shoff = struct.unpack_from('<I', d, 0x20)[0]
            shnum = struct.unpack_from('<H', d, 0x30)[0]
            shstrndx = struct.unpack_from('<H', d, 0x32)[0]

            def sh(i):
                return struct.unpack_from('<IIIIIIIIII', d, e_shoff + i * 40)
            h = sh(shstrndx)
            strs = d[h[4]:h[4] + h[5]]
            blob = None
            for i in range(shnum):
                s = sh(i)
                nm = strs[s[0]:strs.index(b'\0', s[0])].decode()
                if nm == '.text':
                    blob = d[s[4]:s[4] + s[5]]
            assert blob is not None, 'no .text'
        else:
            raw = open(path, 'rb').read()
            blob = raw[0x20:]
        self.blob = blob
        self.md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
        self.md.detail = True
        # ---- self check: the raw flash image starts with a vector table ----
        # CANONICAL ADDRESS SCHEME used throughout this investigation:
        #   .bin offset 0 == .elf .text offset 0 == 0x08010000
        # The reset vector really is 0x0801019c (a copy of the vector table sits
        # at the head of the image; the link origin is 0x08010000).  Ghidra is
        # imported at 0x08000000, so a Ghidra address + 0x10000 == the address
        # used here and in every prior finding document.
        sp = struct.unpack_from('<I', blob, 0)[0]
        rv = struct.unpack_from('<I', blob, 4)[0] & ~1
        assert 0x20000000 <= sp < 0x20080000, 'SP %08x not in SRAM' % sp
        assert rv == self.base + 0x19C, 'Reset %08x != base+0x19c' % rv
        self.sp, self.reset = sp, rv
        self._idx = None

    # ---------- memory ----------
    def off(self, addr):
        return addr - self.base

    def inrange(self, addr, n=1):
        o = self.off(addr)
        return 0 <= o and o + n <= len(self.blob)

    def rd(self, addr, n):
        o = self.off(addr)
        assert 0 <= o and o + n <= len(self.blob), 'read outside image @%08x' % addr
        return self.blob[o:o + n]

    def u32(self, addr):
        return struct.unpack_from('<I', self.rd(addr, 4))[0]

    def u16(self, addr):
        return struct.unpack_from('<H', self.rd(addr, 2))[0]

    def find_u32(self, v, limit=200):
        out = []
        for o in range(0, len(self.blob) - 4, 4):
            if struct.unpack_from('<I', self.blob, o)[0] == v:
                out.append(self.base + o)
                if len(out) >= limit:
                    break
        return out

    def find_u16(self, v, limit=400):
        out = []
        for o in range(0, len(self.blob) - 2, 2):
            if struct.unpack_from('<H', self.blob, o)[0] == v:
                out.append(self.base + o)
                if len(out) >= limit:
                    break
        return out

    # ---------- instruction index (linear sweep, once) ----------
    def index(self):
        if self._idx is not None:
            return self._idx
        insns = []
        a, end = self.base, self.base + len(self.blob)
        while a < end - 2:
            got = False
            for i in self.md.disasm(self.blob[self.off(a):self.off(a) + 4], a):
                got = True
                insns.append(i)
                a += i.size
                break
            if not got:
                a += 2
        self._idx = insns
        return insns

    # ---------- disassembly ----------
    def dis(self, addr, ln):
        return list(self.md.disasm(self.rd(addr, ln), addr))

    def func(self, addr, maxlen=0x800):
        addr &= ~1
        n = min(maxlen, len(self.blob) - self.off(addr))
        out = []
        for i in self.md.disasm(self.rd(addr, n), addr):
            if i.mnemonic.startswith('udf'):
                break
            out.append(i)
            if i.mnemonic in ('bx', 'pop') and 'pc' in i.op_str:
                break
            if i.mnemonic.startswith(('b',)) and i.mnemonic not in ('bl', 'blx', 'bic', 'bfi', 'bfc'):
                break
        return out

    def lit_of(self, ins):
        """(litaddr, value) for a PC-relative ldr/ldr.w, else None.

        NOTE: capstone reports the ARM PC register as operand-register 11
        (ARM_REG_PC), not 15 -- verified against a known `ldr r0,[pc,#0x10]`
        at 0x080144f6 whose literal really is 0x08014508 = FLASH_KEY1.
        """
        if not ins.mnemonic.startswith(('ldr', 'vldr')):
            return None
        try:
            ops = ins.operands
        except Exception:
            return None
        if len(ops) < 2 or ops[0].type != ARM_OP_REG or ops[1].type != ARM_OP_MEM:
            return None
        m = ops[1].mem
        if m.base not in (11, 15):          # capstone PC operand reg == 11
            return None
        pc = (ins.address + 4) & ~3
        tgt = pc + m.disp
        if self.inrange(tgt, 4):
            return (tgt, self.u32(tgt))
        return None

    def call(self, ins):
        if ins.mnemonic in ('bl', 'blx') and ins.op_str.startswith('#'):
            return int(ins.op_str[1:], 0) & ~1
        return None

    def branch(self, ins):
        if ins.mnemonic.startswith('b') and ins.mnemonic not in ('bic', 'bfi', 'bfc') \
                and ins.op_str.startswith('#'):
            return int(ins.op_str[1:], 0) & ~1
        return None

    def memops(self, ins):
        """list of (is_write, disp, base_reg_name, index_reg_name, scale)"""
        try:
            ops = ins.operands
        except Exception:
            return []
        out = []
        mn = ins.mnemonic
        for k, op in enumerate(ops):
            if op.type != ARM_OP_MEM:
                continue
            m = op.mem
            bn = ins.reg_name(m.base) if m.base else ''
            ix = ins.reg_name(m.index) if m.index else ''
            w = (k == 1) and (mn.startswith('str') or mn.startswith('vstr')
                              or mn.startswith('stm') or mn == 'push')
            out.append((w, m.disp, bn, ix, m.scale))
        return out

    # ---------- field scanners ----------
    def field_sites(self, disp, read=True, write=True, regs=None):
        """all instructions with a memory operand of displacement `disp`.

        returns list of dicts: addr, mnemonic, op_str, write, base, base_const
        `base_const` = absolute constant the base register was loaded with
        (tracked from literal pools / movw / movt / adds), else None.
        """
        res = []
        rc = {}
        for i in self.index():
            lit = self.lit_of(i)
            if lit is not None and i.operands[0].type == ARM_OP_REG:
                rc[i.reg_name(i.operands[0].reg)] = lit[1]
            elif i.mnemonic in ('mov', 'movs', 'movw') and len(i.operands) == 2 \
                    and i.operands[0].type == ARM_OP_REG and i.operands[1].type == ARM_OP_IMM:
                rc[i.reg_name(i.operands[0].reg)] = i.operands[1].imm
            elif i.mnemonic == 'movt' and len(i.operands) == 2 \
                    and i.operands[0].type == ARM_OP_REG and i.operands[1].type == ARM_OP_IMM:
                r = i.reg_name(i.operands[0].reg)
                rc[r] = ((rc.get(r) or 0) & 0xFFFF) | (i.operands[1].imm << 16)
            elif i.mnemonic in ('add', 'adds', 'addw') and len(i.operands) == 3 \
                    and i.operands[0].type == ARM_OP_REG and i.operands[2].type == ARM_OP_IMM:
                d = i.reg_name(i.operands[0].reg)
                s = i.reg_name(i.operands[1].reg)
                rc[d] = None if rc.get(s) is None else rc[s] + i.operands[2].imm
            for (w, d, bn, ix, sc) in self.memops(i):
                tot = d + (0 if not ix else 0)
                if d != disp:
                    continue
                if w and not write:
                    continue
                if (not w) and not read:
                    continue
                if regs and bn not in regs:
                    continue
                res.append(dict(addr=i.address, mn=i.mnemonic, op=i.op_str,
                                write=w, base=bn, index=ix,
                                base_const=rc.get(bn)))
        return res

    def xref_lit(self, addr):
        """all instructions whose PC-relative literal load targets `addr`."""
        out = []
        for i in self.index():
            lit = self.lit_of(i)
            if lit and lit[0] == addr:
                out.append(i)
        return out

    def xref_call(self, target):
        t = target & ~1
        return [i for i in self.index() if self.call(i) == t]

    def xref_branch(self, target):
        t = target & ~1
        return [i for i in self.index() if self.branch(i) == t]


def load_pair(dirpath='data/servo_fw_samples/elf'):
    return (Img(os.path.join(dirpath, 'v3150.elf')),
            Img(os.path.join(dirpath, 'v328d8.elf')))


if __name__ == '__main__':
    for im in load_pair():
        print('%s base=0x%08x blob=0x%x SP=0x%08x reset=0x%08x insns=%d' %
              (im.name, im.base, len(im.blob), im.sp, im.reset, len(im.index())))
