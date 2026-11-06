# -*- coding: ascii -*-
import json, re
d = json.load(open(r'D:\mydata\glm-workplace\data\alarm_servo.json', encoding='utf-8'))
s = json.dumps(d, ensure_ascii=False)
for m in re.finditer(r'\{[^{}]*"id": (12832|60945)[^{}]*\}', s):
    print(m.group(0)[:500])
    print('---')
