
import asyncio, sys
sys.path.insert(0, r'D:\mydata\Workspace\.pylibs')
from asyncua import Client

async def show(c, node, depth, maxd, path):
    if depth > maxd: return
    try:
        descs = await node.get_children_descriptions()
    except Exception as e:
        print("  "*depth + "ERR " + path + " -> " + str(e)); return
    for d in descs:
        try:
            nm = d.BrowseName.Name
        except Exception:
            nm = "?"
        tid = d.TypeDefinition
        r = d.ReferenceTypeId
        print("  "*depth + nm + "  node=" + str(d.NodeId) + "  cls=" + str(d.NodeClass) + "  ref=" + str(r))
        try:
            child = c.get_node(d.NodeId)
            await show(c, child, depth+1, maxd, path+"/"+nm)
        except Exception as e:
            print("  "*(depth+1) + "  (walk err: " + str(e) + ")")

async def main():
    async with Client(url="opc.tcp://192.168.5.1:4840") as c:
        print("--- Objects 全树 depth<=6 ---")
        await show(c, c.nodes.objects, 0, 6, "")
        print()
        print("--- 直接试 Resources ns=4;i=1001 ---")
        n = c.get_node("ns=4;i=1001")
        await show(c, n, 0, 6, "Resources")
        print()
        print("--- 试一些常见 Application 路径 ---")
        for cand in ["ns=4;s=|plc|SZYJ-CORTEX-Linux/Resources", "ns=4;s=Resources"]:
            try:
                nd = c.get_node(cand)
                kids = await nd.get_children()
                print(cand, "->", len(kids), "children")
            except Exception as e:
                print(cand, "-> err", e)

asyncio.run(main())
