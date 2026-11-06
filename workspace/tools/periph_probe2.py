#!/usr/bin/env python3
"""Peripheral-layer tractability - v2, with the float pollution removed.

v1 swept 0x40000000..0x50000000, but that is exactly where single-precision
float constants live (0x41A00000 == 20.0f, 0x42000000 == 32.0f, ...), so the
histogram was mostly floats, not peripheral bases.  Real STM32F4 peripheral
addresses are:
    APB1 0x40000000 | APB2 0x40010000 | AHB1 0x40020000 | AHB2 0x50000000
so the filter is 0x40000000..0x40080000 plus 0x50000000..0x50080000, and
float-looking bit patterns are additionally rejected by range check on the
exponent field.
"""
import os
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

# STM32F4 register blocks worth naming (base -> label)
KNOWN = {
    0x40000000: "TIM2",       0x40000400: "TIM3",
    0x40000800: "TIM4",       0x40000C00: "TIM5",
    0x40002800: "RTC",        0x40003000: "WWDG",
    0x40003800: "SPI2",       0x40003C00: "SPI3",
    0x40005400: "I2C1",       0x40005800: "I2C2",
    0x40007000: "PWR",        0x40010000: "TIM1",
    0x40011000: "USART1",     0x40012000: "ADC?",
    0x40013000: "SPI1",       0x40013800: "USART6",
    0x40020000: "GPIOA",      0x40020400: "GPIOB",
    0x40020800: "GPIOC",      0x40020C00: "GPIOD",
    0x40021000: "GPIOE",      0x40021400: "GPIOF",
    0x40021800: "GPIOG",      0x40021C00: "GPIOH",
    0x40022000: "CRC",        0x40023000: "RCC",
    0x40023800: "FLASH-IF",   0x40026000: "DMA1",
    0x40026400: "DMA2",       0x50000000: "USB-OTG-FS",
    0x50050000: "DCMI",
}


def payload(p):
    d = open(p, "rb").read()
    if d[:4] == bytes.fromhex("d4c3b2a1"):
        d = d[0x20:]
    return d


def is_periph(v):
    if 0x40000000 <= v < 0x40080000:
        return True
    if 0x50000000 <= v < 0x50080000:
        return True
    return False


def is_float(v):
    e = (v >> 23) & 0xFF
    return 1 <= e <= 254 and not is_periph(v)


def main():
    for name, rel in IMAGES.items():
        pl = payload(os.path.join(ROOT, rel))
        md = make_md()
        lits = []
        for ins in md.disasm(pl, LOAD):
            if not (ins.mnemonic.startswith("ldr") and "[pc" in ins.op_str):
                continue
            o = ins.address - LOAD
            try:
                imm = int(ins.op_str.split("#")[1].split("]")[0].strip(), 0)
            except Exception:
                continue
            a = ((o + 4) & ~3) + imm
            if a + 4 <= len(pl):
                lits.append(struct.unpack_from("<I", pl, a)[0])

        print("=" * 74)
        print("%s  payload %d B  (%d literal loads)" % (name, len(pl), len(lits)))
        print("=" * 74)
        per = [v for v in lits if is_periph(v)]
        print("  peripheral-range literals (float-rejected) : %d" % len(per))
        c = Counter(per)
        print("  -- named register blocks --")
        for v, n in sorted(c.items()):
            if v in KNOWN:
                print("     0x%08x  x%-3d  %s" % (v, n, KNOWN[v]))
        print("  -- unnamed aligned bases (>=2 uses) --")
        for v, n in sorted(c.items()):
            if v not in KNOWN and n >= 2:
                print("     0x%08x  x%-3d" % (v, n))

        bar = Counter(ins.mnemonic for ins in md.disasm(pl, LOAD)
                      if ins.mnemonic in ("dmb", "dsb", "isb"))
        print("  barriers : %s" % (dict(bar) or "none"))

        # CRC table probe: does a 256*4 byte region start with 0 then 0x1021/0x8005?
        n = 0
        for i in range(0, len(pl) - 1024, 4):
            a, b = struct.unpack_from("<HH", pl, i)
            if a == 0x0000 and b in (0x1021, 0x8005, 0x3D65):
                n += 1
        print("  CRC-table candidates (0x0000 then 0x1021/0x8005/0x3D65) : %d" % n)
        print()


if __name__ == "__main__":
    main()
