import struct
f = open(r"D:\mydata\workspace\data\Application.app",'rb').read()
m = open(r"D:\mydata\workspace\data\appmap\reg_75a76000.bin",'rb').read()
BASE = 0x75a76000
DELTA = 0x75a95cd0

def show(fo, n=48):
    mo = fo + DELTA - BASE
    print("--- file 0x%08x  /  mem 0x%08x (delta applies) ---" % (fo, fo + DELTA))
    print("  file: %s" % f[fo:fo+n].hex(' '))
    if 0 <= mo < len(m) - n:
        print("  mem : %s" % m[mo:mo+n].hex(' '))
    else:
        print("  mem : <outside dump>")
    # same absolute addr resolved in the dump
    print()

for fo in (0x10080, 0x100c0, 0x10100, 0x10200, 0x10400, 0x10600, 0x10c00):
    show(fo)

print("=== where DOES mem 0x75aa5748.. come from? search the file for its neighbourhood ===")
# take 32 bytes of mem at 0x75aa5748 and look for it in the file
memoff = 0x75aa5748 - BASE
w = m[memoff:memoff+32]
print("  mem window: %s" % w.hex(' '))
for g in range(0, len(f)-32, 2):
    if f[g:g+32] == w:
        print("  found verbatim at file 0x%06x" % g)
print()
print("=== and the file window at 0x10080 in the whole dump? ===")
w2 = f[0x10080:0x10080+32]
print("  file window: %s" % w2.hex(' '))
i = m.find(w2)
print("  first dump hit:", hex(BASE+i) if i >= 0 else None)
