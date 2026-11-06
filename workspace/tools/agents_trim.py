#!/usr/bin/env python3
"""Condense the AGENTS.md round-32 entry so the file fits the instruction budget.

AGENTS.md is the workspace index and is injected as instructions on every turn;
it has a hard 65536-byte budget, and after adding round 33 it went over, which
truncates the file's tail.  Round 32's full text is duplicated in
SERVO_SUMMARY.md §13, so the index only needs a pointer plus the red lines.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "AGENTS.md")

START = "- \u2605\u2605\u2605\u2605\u2605 **\u00a732 \u7b2c 32 \u8f6e"
END = "## 9. \u4f1a\u8bdd\u4ea4\u63a5\u6587\u6863"

CONDENSED = """- \u2605\u2605\u2605 **\u00a732 \u7b2c 32 \u8f6e\uff08\u8865\u4e01\u4ea4\u4ed8\u524d\u590d\u6838\uff09\uff1a\u6293\u51fa\u4e00\u4e2a"\u4f1a\u5237\u574f\u673a\u5668"\u7684\u574f\u8865\u4e01\uff0c\u5e76\u628a\u52a0\u8f7d\u5730\u5740\u5b9a\u6b7b\u3002**
  **\u5168\u6587\u89c1 `SERVO_SUMMARY.md` \u00a713**\uff08\u672c\u8282\u53ea\u7559\u7ea2\u7ebf\uff0c\u4e3a\u4e86\u4e0d\u8d85\u6307\u4ee4\u9884\u7b97\uff09\u3002\u672c\u8f6e\u672a\u52a8\u673a\u5668\u4eba\u3001\u672a\u78b0\u603b\u7ebf\u3002
  \u23d4\u23d4 **\u00a732.1 \u52a0\u8f7d\u5730\u5740 = `0x08010000`**\uff08\u4e09\u91cd\u5b9e\u8bc1\uff1a\u4e24 payload \u5404\u5bf9\u5404\u81ea\u7684 hex \u5728\u8be5\u57fa\u5740\u6709 **100.0000%** \u9010\u5b57\u8282\u91cd\u5408\uff1b
  `0x08000000` \u4f1a\u8986\u76d6 bootloader\uff1bReset \u5411\u91cf\u53ea\u5728\u8be5\u57fa\u5740\u89e3\u6210\u771f\u4ee3\u7801\uff09\u21d2 **manifest \u662f\u5bf9\u7684**\uff0c
  **\u672c\u5de5\u4f5c\u533a\u6240\u6709 `0801xxxx` \u53cd\u6c47\u7f16\u6807\u7b7e\u90fd\u8981 `+0x10000`**\u3002\u8865\u4e01\u8f7d\u8377\u504f\u79fb `0x14AFE` \u4e0d\u53d8\uff0cflash \u5730\u5740\u5e94\u5199 `0x08024AFE`\u3002
  \u26a0\ufe0f **\u65b9\u6cd5\u7ea2\u7ebf**\uff1a**"payload \u524d\u4e24\u5b57\u50cf SP/Reset"\u4e0d\u80fd\u53cd\u63a8\u52a0\u8f7d\u5730\u5740**\uff08\u5411\u91cf\u8868\u5728\u4efb\u4f55\u57fa\u5740\u4e0a\u90fd\u957f\u4e00\u6837\uff09\u2014\u2014
  **\u5730\u5740\u7c7b\u7ed3\u8bba\u5fc5\u987b\u7528"\u4e0e\u5df2\u77e5\u955c\u50cf\u7684\u9010\u5b57\u8282\u91cd\u5408\u7387"\u8fd9\u79cd\u53ef\u8bc1\u4f2a\u7684\u6d4b\u91cf\u3002**
  \u23d4\u23d4 **\u00a732.2 \u574f\u8865\u4e01\uff1a`08 46` = `mov r0,r1`\uff0c\u65b9\u5411\u53cd\u4e86\u3002** \u6b63\u786e\u5fc5\u987b\u662f **`mov r1, r0`\uff08`01 46`\uff09**\uff0c
  \u56e0\u4e3a `0x08024B04` \u7684 `str.w` **\u5b58\u7684\u662f r1**\u3002`08 46` \u4f1a\u628a r0 \u8986\u76d6\u6210\u4fee\u6b63\u9879\u3001\u800c\u5b58\u7684\u4ecd\u662f\u4fee\u6b63\u9879 \u21d2 `+0x234` **\u53ea\u5269\u4fee\u6b63\u9879**\u3002
  **\u4e3a\u4f55 \u00a731 \u7684"\u4e09\u9879\u9a8c\u8bc1"\u6ca1\u6293\u4f4f**\uff1a\u4e09\u9879\u5168\u5728\u68c0\u67e5**\u8865\u4e01\u70b9\u5468\u56f4**\uff0c**\u6ca1\u6709\u4e00\u6761\u68c0\u67e5"\u8865\u4e01\u540e r1 \u5230\u5e95\u7b49\u4e8e\u4ec0\u4e48"**\u3002
  \u21d2 **\u65b0\u7ea2\u7ebf\uff1a\u5b57\u8282\u7ea7\u8865\u4e01\u7684\u9a8c\u6536\u65ad\u8a00\u5fc5\u987b\u5305\u542b\u300c\u8865\u4e01\u540e\u76ee\u6807\u5bc4\u5b58\u5668\u7684\u503c = \u671f\u671b\u8868\u8fbe\u5f0f\u300d\u3002**
  \u23d4 **\u00a732.3 `0x20003EF8` \u2260 `0x20003DB0` \u7684\u5bf9\u5e94\u7269**\uff08\u5426\u8bc1"\u5730\u5740\u76f8\u90bb\u5373\u7ed3\u6784\u5bf9\u5e94"\uff09\uff1aD8 \u7684 `0x20003EF8` \u5168\u90e8\u662f
  `add.w r0,r3,r0,lsl #2` + `vldr s,[r0,#0x10..0x30]` \u5f62\u6001 \u21d2 \u662f**\u9010\u8f74\u7cfb\u6570\u6570\u7ec4**\uff08\u6b65\u957f `0x34`\uff09\uff0c\u4e0e\u72b6\u6001\u673a\u7ed3\u6784**\u4e0d\u540c\u7c7b**\uff1b\u4e24\u8005\u53ea\u662f\u5730\u5740\u76f8\u90bb\u3002
  \u23d4 **\u00a732.4** \u00a731 \u7684"`+0x18` \u53ea\u6709 2 \u4e2a\u8bfb\u53d6\u70b9"\u4e0d\u51c6\uff1a\u5b9e\u4e3a **9 \u8bfb + 8 \u5199**\uff08\u8be6\u89c1 \u00a713.4\uff09\u3002
  \u26a0\ufe0f **\u672c\u6761\u662f"\u9759\u9ed8\u7a7a\u7ed3\u679c"\u7b2c 7 \u6b21\u5b9e\u4f8b**\uff1a\u68c0\u6d4b\u5668\u628a MEM \u64cd\u4f5c\u6570\u5199\u6210 `op.type == 1`\uff0c\u800c capstone \u91cc
  **`CS_OP_REG == 1` / `CS_OP_MEM == 3`** \u21d2 \u5bf9\u8089\u773c\u53ef\u89c1\u7684\u8bfb\u53d6\u70b9\u8fd4\u56de **0 \u5904**\uff1b**\u662f\u6b63\u4f8b\u81ea\u68c0\u6293\u51fa\u6765\u7684\u3002**
  \u2605 \u4ea4\u4ed8\u7269\uff1a`tools/servo_patch_verify3.py`\uff08**34 \u6761\u65ad\u8a00\u5168 PASS**\uff0c\u6bcf\u6761\u68c0\u6d4b\u90fd\u5e26\u6b63\u4f8b\u5bf9\u7167\uff09\u3002
  **V7.8 \u662f\u4e13\u4e3a `bf 00` \u9677\u9631\u5199\u7684\u673a\u5668\u5224\u636e**\uff1a\u65ad\u8a00"\u8865\u4e01\u7a97\u53e3\u5185\u9664\u4e86 r1 **\u4e0d\u5199\u4efb\u4f55\u5bc4\u5b58\u5668\u3001\u4e5f\u4e0d\u5199\u5185\u5b58**"\u3002
  \u2605\u2605 **\u4e3a\u4f55"\u628a\u8be5\u9879\u7f6e\u96f6"\u4e0d\u662f hack**\uff1a\u56fa\u4ef6**\u81ea\u5df1**\u5c31\u6709\u4e00\u6761\u6e05\u96f6\u8def\u5f84
  （`0x08024AE6..0x08024AF2`\uff1a`if *(u16*)0x20000020 == 1 then [0x20003DB0+0x18] := 0`\uff09\u21d2 **"\u4fee\u6b63\u9879 = 0"\u662f\u5382\u5546\u81ea\u5df1\u5b9e\u73b0\u7684\u6a21\u5f0f**\u3002
  \u2605\u2605\u2605 **\u00a732.6 \u95e8\u63a7\u6807\u5fd7\u5b57\u8282\u9519\u4f4d\uff08\u672a\u9a8c\u8bc1\u7684\u6839\u56e0\u5019\u9009\uff09**\uff1aD8 \u7528 `ldrb`/`strb` \u8bfb\u5199 **`0x20000020`**\uff1b
  3150 \u7528 `ldrh` \u8bfb **`0x20000020`**\uff08u16\uff09**\u5374\u628a 1 \u5199\u5230 `0x20000022`**\uff08\u53e6\u4e00\u4e2a u16\uff09\u21d2 \u82e5\u65e0\u4eba\u7ed9\u90a3\u4e2a u16 \u5199 1\uff0c
  **"\u4fee\u6b63\u9879\u6e05\u96f6"\u8fd9\u6761\u8def\u5728 3150 \u4e0a\u6c38\u8fdc\u8d70\u4e0d\u5230**\u3002**\u96f6\u98ce\u9669\u9a8c\u8bc1**\uff1a\u7528 `amrd` \u8bfb `0x20000000..0x20000040`\uff0c
  \u770b\u6807\u5b9a\u524d/\u6807\u5b9a\u540e/\u91cd\u65b0\u4e0a\u4f7f\u80fd\u540e `+0x20` \u5904\u534a\u5b57\u662f\u5426\u66fe\u4e3a 1\u3002
  \u65b0\u5de5\u5177\uff1a`pkg_load_verdict.py`\u3001`servo_patch_review.py`\u3001`servo_patch_audit2.py`\u3001`servo_block_gate_cmp.py`\u3001
  `servo_ramglobals_census.py`\u3001`servo_global_role.py`\u3001`servo_ef8_sites.py`\u3001`servo_gate_blocks.py`\u3001`servo_patch_verify3.py`\u3002
  \u7559\u6863\u8f93\u51fa\uff1a`data/servo_fw_samples/{LOAD_ADDR_VERDICT,PATCH_SITE_REVIEW2,BLOCK_CMP_GATE,GLOBAL_ROLES,EF8_SITES,GATE_BLOCKS}.txt`\u3002

"""


def main():
    t = open(P, encoding="utf-8").read()
    before = len(t.encode("utf-8"))
    i = t.find(START)
    j = t.find(END)
    if i < 0 or j < 0 or j < i:
        print("!! markers not found (i=%d j=%d) - aborting, nothing written" % (i, j))
        return 2
    new = t[:i] + CONDENSED + t[j:]
    open(P + ".bak_before_trim", "w", encoding="utf-8", newline="").write(t)
    open(P, "w", encoding="utf-8", newline="").write(new)
    after = len(new.encode("utf-8"))
    print("AGENTS.md: %d -> %d bytes (budget 65536)  %s"
          % (before, after, "OK" if after <= 65536 else "STILL OVER"))
    # integrity
    b = open(P, "rb").read()
    s = b.decode("utf-8")
    print("strict utf-8 OK, U+FFFD=%d, ctrl=%d, lines=%d"
          % (s.count("\ufffd"),
             sum(1 for c in s if ord(c) < 32 and c not in "\n\r\t"),
             s.count("\n") + 1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
