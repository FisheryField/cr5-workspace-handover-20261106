import json, os

BASE = r'D:\mydata\glm-workplace'
targets = {'0x74', '116', '0x86', '134', '0x82', '130', '0x83', '131', '60948', '60949'}

def walk(o, path=''):
    if isinstance(o, dict):
        keys = {str(k) for k in o.keys()}
        vals = {str(v) for v in o.values() if not isinstance(v, (dict, list))}
        if (keys & targets) or (vals & targets):
            print(path, '->', json.dumps(o, ensure_ascii=False)[:260])
            return
        for k, v in o.items():
            walk(v, path + '/' + str(k))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            walk(v, '%s[%d]' % (path, i))

for name in ('alarm_controller.json', 'alarm_servo.json'):
    f = os.path.join(BASE, 'data', name)
    print('##', name)
    if os.path.exists(f):
        walk(json.load(open(f, encoding='utf-8')))
    else:
        print('  (missing)')
    print()
