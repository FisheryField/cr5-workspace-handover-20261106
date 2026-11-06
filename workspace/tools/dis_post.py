
import json,sys
sys.argv=['x']
exec(open(r'D:\mydata\workspace\tools\dis_modify.py').read().split('target=None')[0])
dis(0x11a312, 1016-(0x11a312-0x11a1ac), "modifyServoParams POST 分支后半", 120)
