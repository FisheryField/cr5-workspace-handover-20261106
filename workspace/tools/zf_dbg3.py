import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from zf_img import load_pair
from capstone.arm import ARM_OP_MEM, ARM_OP_REG

a, b = load_pair()
for im in (a, b):
    n_pc = 0
    n_mem = 0
    hits = 0
    for i in im.index():
        for k, op in enumerate(i.operands):
            if op.type != ARM_OP_MEM:
                continue
            n_mem += 1
            if op.mem.base == 15:
                n_pc += 1
        if im.lit_of(i):
            hits += 1
    print('%s mem-operands=%d  pc-based=%d  lit_of hits=%d' % (im.name, n_mem, n_pc, hits))
print()
im = b
for i in im.dis(0x080144f6, 4):
    print(i.address, i.mnemonic, i.op_str,
          [(op.type, op.mem.base, op.mem.disp) for op in i.operands if op.type == ARM_OP_MEM])
