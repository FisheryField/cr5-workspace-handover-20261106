import sys
sys.path.insert(0, 'tools')
sys.path.insert(0, '.pylibs')
import libdata_plt as P

d, secs, stub, slot2sym, dsym, plt, rel = P.build()
for a in (0xb957c, 0xb6530, 0xb957c - 1, 0xb6530 - 1, 0xb8b78, 0xba750, 0xb4560, 0xb9f14, 0xb47d4, 0xb53d4, 0xba5c0, 0xbad10):
    name = stub.get(a) or stub.get(a | 1) or stub.get(a - 1) or stub.get(a & ~1)
    print('0x%08x -> %s' % (a, name))
