import urllib.request, time
def post(path, body, ct="application/json"):
    req = urllib.request.Request("http://192.168.5.1:22000"+path, data=body.encode(),
                                 headers={"Content-Type":ct}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, r.read().decode("utf-8","replace")[:300]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8","replace")[:300]
    except Exception as e:
        return -1, str(e)[:300]
print("json-string ClearError ->", post("/protocol/exchange", '"ClearError()"'))
time.sleep(1.5)
print("json-string alarms ->", post("/protocol/exchange", '"alarms"'))
