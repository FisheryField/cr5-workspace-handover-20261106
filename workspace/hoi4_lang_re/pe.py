#!/usr/bin/env python3
"""Minimal PE32+ reader + RIP-relative xref scanner for hoi4.exe language RE."""
import struct, sys, pathlib

EXE = r"D:\mygames\Hearts of Iron IV (2016)\Hearts of Iron IV\hoi4.exe"

class PE:
    def __init__(self, path):
        self.data = pathlib.Path(path).read_bytes()
        d = self.data
        self.e_lfanew = struct.unpack_from('<I', d, 0x3C)[0]
        assert d[self.e_lfanew:self.e_lfanew+4] == b'PE\0\0', 'not PE'
        coff = self.e_lfanew + 4
        (self.machine, self.nsect, self.timestamp, _, _, self.opt_size,
         self.characteristics) = struct.unpack_from('<HHIIIHH', d, coff)
        opt = coff + 20
        self.magic = struct.unpack_from('<H', d, opt)[0]
        assert self.magic == 0x20b, hex(self.magic)
        self.image_base = struct.unpack_from('<Q', d, opt + 24)[0]
        self.sect_align, self.file_align = struct.unpack_from('<II', d, opt + 32)
        self.size_of_image = struct.unpack_from('<I', d, opt + 56)[0]
        self.entry = struct.unpack_from('<I', d, opt + 16)[0]
        self.sections = []
        sh = opt + self.opt_size
        for i in range(self.nsect):
            o = sh + 40 * i
            name = d[o:o+8].rstrip(b'\0').decode('latin1')
            vsize, va, rawsize, rawptr = struct.unpack_from('<IIII', d, o + 8)
            chars = struct.unpack_from('<I', d, o + 36)[0]
            self.sections.append(dict(name=name, va=va, vsize=vsize,
                                      rawptr=rawptr, rawsize=rawsize, chars=chars))
        self.min_va = min(s['va'] for s in self.sections)
        self.max_va = max(s['va'] + max(s['vsize'], s['rawsize']) for s in self.sections)

    def off2va(self, off):
        for s in self.sections:
            if s['rawptr'] <= off < s['rawptr'] + s['rawsize']:
                return self.image_base + s['va'] + (off - s['rawptr'])
        return None

    def va2off(self, va):
        rva = va - self.image_base
        for s in self.sections:
            if s['va'] <= rva < s['va'] + max(s['vsize'], s['rawsize']):
                if rva - s['va'] < s['rawsize']:
                    return s['rawptr'] + (rva - s['va'])
        return None

    def section_of(self, va):
        rva = va - self.image_base
        for s in self.sections:
            if s['va'] <= rva < s['va'] + max(s['vsize'], s['rawsize']):
                return s
        return None

    def find_bytes(self, needle, limit=None):
        out, start = [], 0
        while True:
            i = self.data.find(needle, start)
            if i < 0:
                break
            out.append(i)
            if limit and len(out) >= limit:
                break
            start = i + 1
        return out

    def cstr(self, va, maxlen=200):
        off = self.va2off(va)
        if off is None:
            return None
        end = self.data.find(b'\0', off, off + maxlen)
        if end < 0:
            end = off + maxlen
        return self.data[off:end].decode('latin1')


def scan_ripxrefs(pe, targets):
    """targets: dict va -> label. Returns list of (insn_va, target_va, kind)."""
    d = pe.data
    hits = []
    tset = {}
    for va, lab in targets.items():
        tset[va] = lab
    # candidate opcode prefixes for RIP-relative memory operands
    firsts = set()
    for rex in range(0x40, 0x50):
        for op in (0x8D, 0x8B, 0x89, 0x3B, 0x39, 0x85, 0x01, 0x03, 0xC7, 0x8F):
            firsts.add(bytes([rex, op]))
    for op in (0x8D, 0x8B, 0x89, 0x3B, 0x39, 0x85, 0x01, 0x03, 0xC7, 0x8F):
        firsts.add(bytes([op]))
    for s in pe.sections:
        if not (s['chars'] & 0x20000000):  # not executable
            continue
        base = s['rawptr']
        end = base + s['rawsize']
        blob = d[base:end]
        va_base = pe.image_base + s['va']
        for pat in firsts:
            L = len(pat)
            start = 0
            while True:
                i = blob.find(pat, start)
                if i < 0:
                    break
                start = i + 1
                # skip patterns where a preceding REX byte belongs to this instruction
                if L == 1 and i > 0 and 0x40 <= blob[i-1] <= 0x4F:
                    continue
                o = i + L
                if o >= len(blob):
                    continue
                modrm = blob[o]
                if (modrm & 0xC7) != 0x05:
                    continue
                if o + 5 > len(blob):
                    continue
                disp = struct.unpack_from('<i', blob, o + 1)[0]
                insn_va = va_base + i
                nxt = insn_va + L + 1 + 4
                tgt = nxt + disp
                if tgt in tset:
                    hits.append((insn_va, tgt, tset[tgt], pat.hex()))
    hits.sort()
    return hits


if __name__ == '__main__':
    pe = PE(EXE)
    print('image_base=%#x sections=%d entry=%#x' % (pe.image_base, pe.nsect, pe.image_base + pe.entry))
    for s in pe.sections:
        print('  %-8s va=%#010x vsize=%#010x rawptr=%#010x rawsize=%#010x chars=%#x'
              % (s['name'], pe.image_base + s['va'], s['vsize'], s['rawptr'], s['rawsize'], s['chars']))
    needles = sys.argv[1:] or ['l_simp_chinese']
    for n in needles:
        nb = n.encode()
        offs = pe.find_bytes(nb, limit=20)
        print('== %r : %d 处' % (n, len(offs)))
        for o in offs:
            va = pe.off2va(o)
            sec = pe.section_of(va) if va else None
            ctx = pe.data[max(0, o-40):o+len(nb)+40].decode('latin1').replace('\0', '.')
            print('   off=%#x va=%#x sec=%s  …%s…' % (o, va or 0, sec['name'] if sec else '?', ctx))
