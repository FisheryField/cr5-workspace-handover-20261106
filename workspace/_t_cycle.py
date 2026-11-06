import json
import sys
import time
import urllib.request

BASE = "http://192.168.5.1:22000"


def post(path, payload):
    req = urllib.request.Request(BASE + path, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"},
                                 method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, r.read().decode("utf-8", "replace")[:100]
    except Exception as e:  # noqa: BLE001
        return -1, str(e)[:100]


def main():
    servo = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] != "-" else None
    if servo:
        payload = {"src": "httpClient",
                   "body": [{"key": "addr200C01", "servoNum": servo, "value": 1}]}
        print("clear %s ->" % servo, post("/settings/modifyServoParams", payload))
        time.sleep(28)
    print("read J1 0x603F ->", post("/settings/readServoParams",
          {"body": [{"key": "addr603F00", "servoNum": "J1"}]}))
    time.sleep(2)
    print("enable ->", post("/settings/controlMode", {"controlMode": "enable"}))
    time.sleep(4)
    print("calibrate ->", post("/calibrate/home", {}))
    time.sleep(10)
    print("cycle done; check logs")


if __name__ == "__main__":
    main()
