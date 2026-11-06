import sys
sys.path.insert(0, 'tools')
sys.path.insert(0, '.pylibs')
import libdata_strrefs as L

e = L.Elf()
sites = L.scan(e)
print('sites:', len(sites))
for tgt, label in [(0x214a74, 'clear_err_start'), (0x214a9c, 'clear_err_done'), (0x209b5c, 'protoExchange')]:
    hits = [a for a, v in sites if v == tgt]
    print('%-16s 0x%x  %s' % (label, tgt, [hex(a) for a in hits]))
# control
ctrl = [a for a, v in sites if v == 0x00235324]
print('control isRequestCalihome:', [hex(a) for a in ctrl])
