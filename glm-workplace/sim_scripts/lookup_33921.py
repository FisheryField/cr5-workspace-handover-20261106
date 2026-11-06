import json, re
d = json.load(open(r'D:\mydata\glm-workplace\data\alarm_servo.json', encoding='utf-8'))
s = json.dumps(d, ensure_ascii=False)
for want in ('33921', '12832', '60945'):
    print('==== id', want, '====')
    for m in re.finditer(r'\{[^{}]*"id": ' + want + r'[^{}]*\}', s):
        print(m.group(0)[:600])
