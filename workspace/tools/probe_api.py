# -*- coding: utf-8 -*-
"""在控制器 22000 端口探测 servo 参数接口（纯只读 GET）。"""
import urllib.request, urllib.error, json

BASE = "http://192.168.5.1:22000"
CANDIDATES = [
    "/settings/version",
    "/settings/servoParams", "/settings/servoParam", "/settings/servo/params",
    "/settings/function/servoParams", "/servoParams", "/servo/params",
    "/settings/productInfo/hardwareInfo", "/settings/productInfo",
    "/settings/encoder", "/settings/homeEncoder", "/settings/function/homeEncoder",
    "/protocol/version", "/list", "/help",
]

def req(path, method="GET", body=None):
    url = BASE + path
    data = body.encode() if body else None
    r = urllib.request.Request(url, data=data, method=method)
    if body: r.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(r, timeout=6) as resp:
            return resp.status, resp.read(600).decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, (e.read(200).decode("utf-8", "replace") or "")
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"

for p in CANDIDATES:
    st, txt = req(p)
    mark = "  <<<" if st == 200 else ""
    print(f"{str(st):>5}  GET {p:42} {txt[:110].replace(chr(10),' ')}{mark}")
