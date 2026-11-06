
import asyncio, sys
sys.path.insert(0, r'D:\mydata\Workspace\.pylibs')
from asyncua import Client

KEY = ['gvl','home','zero','sdo','param','axis','encoder','calib','offset','servo','homing','position']

async def main():
    url = "opc.tcp://192.168.5.1:4840"
    async with Client(url=url) as c:
        print("CONNECTED:", url)
        try:
            ns = await c.get_namespace_array()
            print("namespaces:", ns)
        except Exception as e:
            print("ns err:", e)
        root = c.nodes.objects
        seen = 0
        outline = []
        hits = []
        async def walk(node, depth, path):
            nonlocal seen
            if depth > 5 or seen > 4000:
                return
            try:
                kids = await node.get_children()
            except Exception:
                return
            for k in kids:
                seen += 1
                try:
                    bn = await k.read_browse_name()
                    nm = bn.Name
                except Exception:
                    continue
                p = path + "/" + nm
                if depth <= 3:
                    outline.append("  " * depth + nm + "   [" + str(k.nodeid) + "]")
                low = nm.lower()
                if any(x in low for x in KEY):
                    hits.append("  " + p + "   [" + str(k.nodeid) + "]")
                await walk(k, depth + 1, p)
        await walk(root, 0, "")
        print("\n=== 对象树 (深度<=3) ===")
        for l in outline[:160]:
            print(l)
        print("\n=== 关键词命中 (" + str(len(hits)) + ") ===")
        for h in hits[:160]:
            print(h)
        print("\nvisited nodes:", seen)

asyncio.run(main())
