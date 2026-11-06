import sys, os, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from zf_img import load_pair

a, b = load_pair()
for im, addrs in ((a, [0x08011800, 0x08011894, 0x0801416c]),
                  (b, [0x080117c0, 0x08011854, 0x08014508])):
    for tgt in addrs:
        print('==== %s literals around 0x%08x' % (im.name, tgt))
        for i in im.dis(tgt - 0x30, 0x60):
            lit = im.lit_of(i)
            note = '   ; =0x%08x' % lit[1] if lit else ''
            print('   %08x: %-9s %-28s%s' % (i.address, i.mnemonic, i.op_str, note))
        print()
