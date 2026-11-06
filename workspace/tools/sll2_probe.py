
import struct, sys
path=sys.argv[1]
with open(path,'rb') as f:
    gh=f.read(24)
    print("magic:", gh[:4].hex())
    tz,sig,snap,net = struct.unpack_from('<iIII', gh, 8)
    print("snaplen=%d network=%d" % (snap, net))
    for k in range(3):
        h=f.read(16)
        if len(h)<16: break
        ts,tu,cap,orig=struct.unpack('<IIII',h)
        d=f.read(cap)
        print("--- pkt %d caplen=%d origlen=%d ---" % (k,cap,orig))
        print("   head 48:", d[:48].hex())
        print("   88a4 at offset:", d.find(b'\x88\xa4'))
