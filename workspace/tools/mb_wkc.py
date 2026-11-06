
import struct
def readpcap(path):
    d=open(path,'rb').read(); off=24; out=[]
    while off+16<=len(d):
        ts,tus,incl,orig=struct.unpack_from("<IIII",d,off); off+=16
        out.append((ts+tus/1e6,d[off:off+incl])); off+=incl
    return out
CMD={0:'NOP',1:'APRD',2:'APWR',3:'APRW',4:'FPRD',5:'FPWR',6:'FPRW',7:'BRD',8:'BWR',9:'BRW',10:'LRD',11:'LWR',12:'LRW',13:'ARMW',14:'FRMW'}
for path,label in ((r"D:\mydata\workspace\data\codex_b\ethercat_pcap\zero32_calibration.pcap","3.2.D.8"),
                   (r"D:\mydata\workspace\data\codex_b\ethercat_pcap\capture315_ethercat.pcap1","3.1.5.0")):
    print("################ %s ################" % label)
    seen=set()
    for ts,pkt in readpcap(path):
        if len(pkt)<18 or pkt[12:14]!=b'\x88\xa4': continue
        ec = pkt[14] | ((pkt[15]&0x07)<<8)
        o=16
        while o+12 <= 16+ec and o+12 <= len(pkt):
            cmd,idx = pkt[o],pkt[o+1]
            st = pkt[o+2]|(pkt[o+3]<<8); of = pkt[o+4]|(pkt[o+5]<<8)
            lw = pkt[o+6]|(pkt[o+7]<<8); dl=lw&0x7ff; more=(lw>>15)&1
            if of in (0x1800,0x1a30):
                wkc = pkt[o+10+dl]|(pkt[o+11+dl]<<8) if o+12+dl<=len(pkt) else -99
                key=(CMD.get(cmd&0xf,cmd), st, of, dl, wkc, pkt[o+10:o+26].hex(' '))
                if key not in seen:
                    seen.add(key)
                    print("  %-5s st=0x%04x off=0x%04x dl=%-4d wkc=%d  data16=%s" % key)
            o += 12+dl
            if not more: break
    print()
