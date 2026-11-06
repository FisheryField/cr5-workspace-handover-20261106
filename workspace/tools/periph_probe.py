#!/usr/bin/env python3
"""Is the servo firmware's ENCODER/PERIPHERAL layer findable mechanically?

The recommended primary line for the zero question is a D8-vs-3150 read of the
encoder layer (the position chain provably has no zero-offset variable and was
just excluded experimentally).  Before promising that, measure how tractable it
is:

  * how many literal-pool dwords point into the STM32 peripheral space
    (0x40000000..0x50000000)?  Those ARE the peripheral base addresses, and
    this firmware puts all 32-bit constants in the literal pool.
  * which peripheral blocks are touched (SPI / USART / TIM / DMA / CRC ...)
  * how many memory barriers (dmb/dsb/isb) exist - they bracket peripheral I/O
  * is there a 256-entry CRC table (a serial absolute-encoder protocol tells)
"""
import os
import re
import struct
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from servo_img import make_md  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGES = {
    "D8": "data/servo_fw_samples/elf/v328d8.bin",
    "3150": "data/servo_fw_samples/elf/v3150.bin",
}
LOAD = 0x08010000
PERIPH = (0x40000000, 0x50000000)

# STM32F4 peripheral block names (upper 16 bits)
BLOCKS = {
    0x4000: "TIM2-5/SPI? (APB1 low)",
    0x4001: "TIM/SPI2-3/I2C/USART2-5 (APB1 high)",
    0x4002: "USART1-3/SPI1/I2C (APB2 low)",
    0x4003: "EXTI/ADC/etc",
    0x4004: "ADC/SPI4",
    0x4005: "ADC1-3",
    0x4006: "SPI1 / I2S",
    0x4007: "DMA1/DMA2",
    0x4008: "RCC",
    0x4009: "FLASH interface",
    0x400A: "CRC?? ",
    0x400C: "ADC?",
    0x400E: "IWDG/WWDG/RTC?",
    0x4001 and 0x4003: "?",
    0x5000: "USB OTG FS",
    0x5003: "USB OTG HS",
    0x5006: "DCMI",
}


def payload(p):
    d = open(p, "rb").read()
    if d[:4] == bytes.fromhex("d4c3b2a1"):
        d = d[0x20:]
    return d


def lit_loads(pl):
    """(site_addr, literal_value) for every LDR-literal that names a value."""
    md = make_md()
    out = []
    for ins in md.disasm(pl, LOAD):
        if not (ins.mnemonic.startswith("ldr") and "[pc" in ins.op_str):
            continue
        o = ins.address - LOAD
        try:
            imm = int(ins.op_str.split("#")[1].split("]")[0].strip(), 0)
        except Exception:
            continue
        a = ((o + 4) & ~3) + imm
        if a + 4 > len(pl):
            continue
        out.append((ins.address, struct.unpack_from("<I", pl, a)[0]))
    return out


def main():
    for name, rel in IMAGES.items():
        pl = payload(os.path.join(ROOT, rel))
        md = make_md()
        lits = lit_loads(pl)
        print("=" * 74)
        print("%s   payload %d B   (%d literal loads total)" % (name, len(pl), len(lits)))
        print("=" * 74)

        per = [(a, v) for a, v in lits if PERIPH[0] <= v < PERIPH[1]]
        print("  literal values inside 0x40000000..0x50000000 : %d" % len(per))
        blk = Counter((v >> 16) << 16 for _, v in per)
        for b, c in sorted(blk.items()):
            print("     0x%08x  x%-3d  %s" % (b, c, BLOCKS.get(b >> 16, "?")))

        # exact bases (a peripheral base is usually aligned to 0x400)
        exact = Counter(v for _, v in per if v % 0x400 == 0)
        print("  -- page-aligned peripheral bases (top 12) --")
        for v, c in exact.most_common(12):
            print("     0x%08x  x%-3d" % (v, c))

        # barriers
        bar = Counter()
        for ins in md.disasm(pl, LOAD):
            if ins.mnemonic in ("dmb", "dsb", "isb"):
                bar[ins.mnemonic] += 1
        print("  barriers: %s" % dict(bar))

        # CRC/table probe: 256 consecutive u16 or u32 that look like a CRC table
        n16 = n32 = 0
        for i in range(0, len(pl) - 1024, 2):
            v = struct.unpack_from("<16H", pl, i)
            if v[0] == 0x0000 and v[1] in (0x1021, 0x8005, 0x3D65):
                n16 += 1
        print("  suspicious 256-entry u16 CRC-table starts: %d" % n16)
        print()


if __name__ == "__main__":
    main()
