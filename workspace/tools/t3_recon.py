#!/usr/bin/env python3
"""T3 recon: settle the ELF address base for the servo images, then run a
POSITIVE-CONTROL literal-pool search before any negative claim is made.

Rules honoured (workspace red lines):
  * true flash addr = 0x08010000 + file offset  (payload loaded at 0x08010000)
  * every search tool must first prove it can find a known-present sample
  * this firmware builds 32-bit constants via literal pools (movw/movt unused)
"""
import struct, sys, os

ELF = r"D:\mydata\workspace\data\servo_fw_samples\elf\v3150.elf"
ELF2 = r"D:\mydata\workspace\data\servo_fw_samples\elf\v328d8.elf"
CSV = r"D:\mydata\workspace\data\official\servoCSV\param.csv"


def elf_load(path):
    d = open(path, 'rb').read()
    assert d[:4] == b'\x7fELF', path
    assert d[4] == 1 and d[5] == 1, "need ELF32 LSB"
    e_phoff, = struct.unpack_from('<I', d, 0x1c)
    e_phentsize, e_phnum = struct.unpack_from('<HH', d, 0x2a)
    segs = []
    for i in range(e_phnum):
        o = e_phoff + i * e_phentsize
        p_type, p_offset, p_vaddr, p_paddr, p_filesz, p_memsz = struct.unpack_from('<IIIIII', d, o)
        if p_type == 1:  # PT_LOAD
            segs.append((p_vaddr, p_offset, p_filesz, p_memsz))
    if not segs:
        # sections only (mkelf.py style)
        e_shoff, = struct.unpack_from('<I', d, 0x20)
        e_shentsize, e_shnum = struct.unpack_from('<HH', d, 0x2e)
        for i in range(e_shnum):
            o = e_shoff + i * e_shentsize
            sh_name, sh_type, sh_flags, sh_addr, sh_offset, sh_size = struct.unpack_from('<IIIIII', d, o)
            if sh_flags & 0x2 and sh_addr:  # SHF_ALLOC
                segs.append((sh_addr, sh_offset, sh_size, sh_size))
    return d, segs


def seg_for(segs, vaddr):
    for v, o, fs, ms in segs:
        if v <= vaddr < v + fs:
            return v, o, fs
    return None


def rd(d, segs, addr, n):
    s = seg_for(segs, addr)
    if not s:
        return None
    v, o, fs = s
    return d[o + (addr - v): o + (addr - v) + n]


def main():
    for path in (ELF, ELF2):
        d, segs = elf_load(path)
        print("== %s" % os.path.basename(path))
        for v, o, fs, ms in segs:
            print("   PT_LOAD vaddr=0x%08X off=0x%06X filesz=0x%06X memsz=0x%06X" % (v, o, fs, ms))
        # entry
        e_entry, = struct.unpack_from('<I', d, 0x18)
        print("   e_entry=0x%08X" % e_entry)
        # vector table sanity: first two words of the lowest PT_LOAD
        lo = min(segs)
        w0, w1 = struct.unpack_from('<II', d, lo[1])
        print("   lowest seg first words: 0x%08X 0x%08X" % (w0, w1))

    d, segs = elf_load(ELF)
    # ---- positive control: known-present literals for v3150 (from §29 of AGENTS.md)
    for lit in (0x2000129C, 0x20003DB0, 0x20000022):
        n = 0
        sites = []
        for v, o, fs, ms in segs:
            blob = d[o:o + fs]
            for i in range(0, len(blob) - 4, 4):
                if struct.unpack_from('<I', blob, i)[0] == lit:
                    sites.append(v + i)
        print("POSCTL raw dword 0x%08X present at %d slot(s): %s" %
              (lit, len(sites), " ".join("0x%08X" % s for s in sites[:8])))

    # ---- the T3 candidate
    for lit in (0x200073A0, 0x200173A0, 0x2000C6C8, 0x20009A70):
        hits = []
        for v, o, fs, ms in segs:
            blob = d[o:o + fs]
            for i in range(0, len(blob) - 4, 4):
                if struct.unpack_from('<I', blob, i)[0] == lit:
                    hits.append(v + i)
        print("raw dword 0x%08X : %d slot(s) %s" % (lit, len(hits),
              " ".join("0x%08X" % s for s in hits[:10])))

    # ---- param.csv rows
    print("\n== param.csv (GBK) selected rows")
    txt = open(CSV, 'rb').read().decode('gbk', 'replace').splitlines()
    print("header:", txt[0][:200] if txt else "(none)")
    for ln in txt:
        u = ln.split(',')
        if u and u[0].strip() in ('H01.13', 'H01.14', 'H01.15', 'H01.17', 'H01.18',
                                  'H0C.02', 'H0C.00'):
            print("  ", ln.strip()[:220])
    return 0


if __name__ == '__main__':
    sys.exit(main())
