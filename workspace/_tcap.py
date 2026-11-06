import sys
sys.path.insert(0, r"D:\mydata\workspace\.pylibs")
import capstone
print("ok", capstone.__version__)
cs = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
print("dis ok:", cs.disasm(b"\x01\x46\x00\xbf", 0x1000).__next__().mnemonic)
