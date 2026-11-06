import sys, os, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from zf_img import load_pair

a, b = load_pair()
im = b
# find the ldr that loads 0x45670123 (FLASH_KEY1) -> look near 0x080144f6
for addr in (0x080144ec, 0x080144f6, 0x080144fe):
    print('--- around 0x%08x' % addr)
    for i in im.dis(addr, 0x10):
        lit = im.lit_of(i)
        print('   %08x %-9s %-28s  ops=%d  lit=%s' % (i.address, i.mnemonic, i.op_str, len(i.operands), lit))
# brute force: which instructions have a mem operand with base pc
print('--- scan for pc-relative ldr and print target for a window')
for i in im.dis(0x08014400, 0x200):
    for op in i.operands:
        pass
    lits = im.lit_of(i)
    if lits:
        print('   %08x %-9s %-28s -> 0x%08x = 0x%08x' % (i.address, i.mnemonic, i.op_str, lits[0], lits[1]))
