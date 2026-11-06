# -*- coding: utf-8 -*-
"""回退：删除站内挡板『挡板_215x710x20』。不保存工作站。"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
from robodk.robolink import Robolink, ITEM_TYPE_OBJECT

NAME = '挡板_215x710x20'
RDK = Robolink()
it = RDK.Item(NAME, ITEM_TYPE_OBJECT)
if not it.Valid():
    print('站内无此对象（已回退过？）:', NAME)
    sys.exit(0)
it.Delete()
still = RDK.Item(NAME, ITEM_TYPE_OBJECT)
print('删除完成，回读 valid =', still.Valid(), '（False=已不存在）')
