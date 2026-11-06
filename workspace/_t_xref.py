import sys, struct
sys.path.insert(0, '.pylibs')
import capstone

SO = 'libdataSvr.so.bin'
data = open(SO, 'rb').read()
e_phoff = struct.unpack_from('<I', data, 0x1c)[0]
e_phentsize, e_phnum = struct.unpack_from('<HH', data, 0x2a)
segs = []
for i in range(e_phnum):
    off = e_phoff + i * e_phentsize
    p_type, p_offset, p_vaddr, _, p_filesz = struct.unpack_from('<IIIII', data, off)
    if p_type == 1:
        segs.append((p_vaddr, p_offset, p_filesz))

def v2o(v):
    for va, off, sz in segs:
        if va <= v < va + sz:
            return off + (v - va)
    return None

# find literal-pool entries pointing at 0x214a74 / 0x214a9c, then locate the
# 'add rX, pc' instructions that consume them, i.e. the log call sites.
targets = {0x214a74, 0x214a9c}
# scan whole .text (first LOAD seg with exec) for 4-byte little-endian occurrences
hits = []
for va, off, sz in segs:
    for t in targets:
        pat = struct.pack('<I', t)
        idx = 0
        while True:
            o = data.find(pat, off, off + sz)
            if o < 0:
                break
            hits.append((o, o2v_of(off, o, va), t))
            idx = o + 1
            off2 = o + 1
            # continue searching from o+1 within same seg
            o2 = data.find(pat, off2, off + sz)
            if o2 < 0:
                break
            hits.append((o2, o2v_of(off, o2, va), t))
            off = o2  # not used further
            break
        # simpler: redo below

def o2v_of(seg_off, o, seg_va):
    return seg_va + (o - seg_off)

hits = sorted(set(hits))
for o, v, t in hits:
    print('LIT pool @file 0x%x  vaddr 0x%08x  -> str 0x%x' % (o, v, t))
