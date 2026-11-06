
import sys, asyncio
sys.path.insert(0, r"D:\mydata\workspace\.pylibs")
from asyncua import Client
MAXD=5
async def walk(node, depth, path):
    if depth>MAXD: return
    try: kids = await node.get_children()
    except: return
    for k in kids:
        try: bn = await k.read_browse_name()
        except: continue
        p = path + "/" + bn.Name
        print("  "*depth + "- " + bn.Name)
        if depth < MAXD:
            await walk(k, depth+1, p)
async def main():
    async with Client(url="opc.tcp://192.168.5.1:4840") as c:
        objs = c.nodes.objects
        for ch in await objs.get_children():
            bn = await ch.read_browse_name()
            print("== " + bn.Name)
            await walk(ch, 1, bn.Name)
asyncio.run(main())
