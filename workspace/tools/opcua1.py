
import sys, asyncio
sys.path.insert(0, r"D:\mydata\workspace\.pylibs")
try:
    from asyncua import Client
except Exception as e:
    print("asyncua 导入失败:", e); sys.exit()
async def main():
    async with Client(url="opc.tcp://192.168.5.1:4840") as c:
        print("已连接 4840")
        root = c.nodes.objects
        kids = await root.get_children()
        print("Objects 下 %d 个子节点:" % len(kids))
        for k in kids:
            try:
                bn = await k.read_browse_name()
                print("   -", bn.NamespaceIndex, bn.Name)
            except Exception as e:
                print("   - <读取失败>", e)
        # 尝试找 Application
        for k in kids:
            try:
                bn = await k.read_browse_name()
            except: continue
            if 'Application' in bn.Name or 'Device' in bn.Name:
                subs = await k.get_children()
                print("  >>", bn.Name, "下有", len(subs), "个子节点")
                for s in subs[:40]:
                    try:
                        b2 = await s.read_browse_name(); print("       *", b2.Name)
                    except: pass
asyncio.run(main())
