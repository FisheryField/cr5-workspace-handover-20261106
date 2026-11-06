#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Trigger the UI-equivalent servo clear-error via POST /protocol/exchange.

⛔⛔⛔ DO NOT USE — DISABLED ⛔⛔⛔
2026-09-25 17:17 field result: sending the JSON-string body
    "{\"alarms\": true}"
CRASHED codesyscontrol (remote closed connection, port 22000 gone),
with no protoExchange log line — the crash happens early in parse/dispatch,
so the exact required inner shape is still unknown. Keep using the
DobotStudio Pro UI clear-error button (proven 14:28:43) instead.

Reverse-engineered 2026-09-25 from libdataSvr.so.bin protoExchange dispatcher
(PLT symbols resolved via tools/libdata_plt.py):
  * the HTTP layer jsoncpp-parses the body; @0x11a258 it checks the value
    type is STRING (QJsonValue::String == 3) and 500s otherwise -> the POST
    body must be a JSON *string* whose text is another JSON object
    (that is why plain objects returned 500 without any protoExchange log).
  * the inner object is read section by section with jsoncpp
    (Json::Value::operator[] 0xb53d4); the "alarms" member lands at [sp+0x44]
    (@0x11a76c-0x11a780).
  * @0x11aadc: body["alarms"].asBool() (0xb957c) != 0 -> log
    "clear error from http exchange ...." (str 0x214a74) ->
    DataSubProcess::clearError() (0xb6530) -> "... done !" (0x214a9c).
    A null "alarms" is the read path (returns alarms instead of clearing).
  * Known-good UI clear at 14:28:43 used this path and produced
    "servo1 error ID update : 34322 -> 0".
Body actually sent: the JSON-string encoding of {"alarms": true}.
"""
import json
import sys
import urllib.request

CTRL = "192.168.5.1"
URL = "http://%s:22000/protocol/exchange" % CTRL


def wrap(inner):
    """Encode inner object as a JSON string document (the required shape)."""
    return json.dumps(json.dumps(inner))


CANDIDATES = [
    {"alarms": True},
    {"alarms": 1},
]


def post(body):
    req = urllib.request.Request(URL, data=body.encode(),
                                 headers={"Content-Type": "application/json"},
                                 method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, r.read().decode("utf-8", "replace")[:200]
    except Exception as e:  # noqa: BLE001
        return -1, str(e)[:200]


def main():
    dry = "--go" not in sys.argv
    for inner in CANDIDATES:
        body = wrap(inner)
        if dry:
            print("DRY   would POST", body)
            continue
        print("POST", body, "->", end=" ")
        rc, out = post(body)
        print(rc, out)
        if rc == 200:
            break
    if dry:
        print('\nre-run with --go to actually send.')


if __name__ == "__main__":
    main()
