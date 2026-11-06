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

def o2v(o):
    for va, off, sz in segs:
        if off <= o < off + sz:
            return va + (o - off)
    return None

# 1) locate target strings
targets = [b'clear error from http exchange', b'DataSubProcess::clearError', b'protoExchange']
for t in targets:
    idx = 0
    while True:
        o = data.find(t, idx)
        if o < 0:
            break
        v = o2v(o)
        print('STR  %-32s file_off=0x%x vaddr=0x%x' % (t.decode()[:32], o, v if v else 0))
        idx = o + 1
