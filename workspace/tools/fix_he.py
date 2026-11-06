
import json
p = r"D:\mydata\workspace\data\homeEncoder.json"
j = json.load(open(p, encoding='utf-8'))
recs = j["encoder"]
print("记录数:", len(recs))
last = recs[-1]
print("最后一条:", last.get("date"), last.get("time"))
print("  改前 innerEncoder =", last["innerEncoder"])
last["innerEncoder"][5] = 115043.0
print("  改后 innerEncoder =", last["innerEncoder"])
json.dump(j, open(p,'w',encoding='utf-8'), indent=4, ensure_ascii=False)
print("已写回本地")
