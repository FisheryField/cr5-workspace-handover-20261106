import tarfile, pathlib
P = pathlib.Path(r"D:\mydata\codex\b\dobot-evidence-20260922\shm_focus32.tar.gz")
with tarfile.open(P,"r:gz") as t:
    for m in t.getmembers():
        b = m.name.split("/")[-1]
        if b in ("start","end","pid","times"):
            d = t.extractfile(m).read()
            if b == "times":
                ls = d.decode().split("\n")
                print(f"times: {len(ls)} 行  首={ls[0]}  末={ls[-2] if len(ls)>1 else ''}")
            else:
                print(f"{b}: {d.decode(errors='replace').strip()}")
    # 归档内文件的 mtime
    for m in t.getmembers():
        b = m.name.split("/")[-1]
        if b in ("start","end","main_0.bin","main_300.bin","s1_0.bin","s1_300.bin"):
            print(f"  tar mtime {b}: {m.mtime}")
