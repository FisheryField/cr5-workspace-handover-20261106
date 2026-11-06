import json
import sys
import time
import urllib.request

URL = "http://192.168.5.1:22000/settings/modifyServoParams"


def post(payload):
    req = urllib.request.Request(URL, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"},
                                 method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, r.read().decode("utf-8", "replace")[:200]
    except Exception as e:  # noqa: BLE001
        return -1, str(e)[:200]


def main():
    servo = sys.argv[1] if len(sys.argv) > 1 else "J1"
    value = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    dry = "--go" not in sys.argv
    # H0C.00 fault reset -> EtherCAT 0x200C:01 (param.csv mapping, pcap-verified)
    # body requires top-level object with "src" member (reverse-eng 2026-09-25:
    # HasMember("src") else 400 @0x11a330; src must be "httpClient" or "files")
    payload = {"src": "httpClient",
               "body": [{"key": "addr200C01", "servoNum": servo, "value": value}]}
    print("payload:", json.dumps(payload))
    if dry:
        print("DRY only. re-run with --go")
        return
    rc, out = post(payload)
    print("->", rc, out)


if __name__ == "__main__":
    main()
