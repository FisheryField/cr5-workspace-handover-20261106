# -*- coding: utf-8 -*-
"""清报警：试几个已知的 HTTP 路由，逐个打印状态码。"""
import sys
import urllib.request

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
CTRL = "192.168.5.1:22000"

ROUTES = ["/interface/clearAlarms", "/interface/ClearError", "/interface/clearError"]


def post(path, body=b"{}"):
    req = urllib.request.Request("http://%s%s" % (CTRL, path), data=body,
                                 headers={"Content-Type": "application/json"},
                                 method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            data = r.read()[:200]
            return "HTTP %s %r" % (r.status, data)
    except urllib.error.HTTPError as exc:
        return "HTTPError %s %s" % (exc.code, exc.reason)
    except Exception as exc:  # noqa: BLE001
        return "EXC %s: %s" % (type(exc).__name__, exc)


for route in ROUTES:
    print("%-28s -> %s" % (route, post(route)))
