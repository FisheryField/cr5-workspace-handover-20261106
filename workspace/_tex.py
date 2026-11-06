import urllib.request, time
def post(path, body):
    req = urllib.request.Request("http://192.168.5.1:22000"+path, data=body.encode(),
                                 headers={"Content-Type":"application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, r.read().decode("utf-8","replace")[:300]
    except Exception as e:
        return -1, str(e)[:300]
cands = [
  '{"Exchange":"RobotMode()"}',
  '{"data":"RobotMode()"}',
  '{"cmd":"RobotMode()"}',
  '{"protocol":"RobotMode()"}',
  '{"body":[{"key":"Exchange","value":"RobotMode()"}]}',
]
for c in cands:
    print(repr(c), "->", post("/protocol/exchange", c))
    time.sleep(1.2)
