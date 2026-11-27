"""CP3/CP4 numbers for one Mistral run vs the pre-fix parser (parser_original.py).
usage: python3 cp3_report.py <mistral_runN.jsonl> <parser_depth.jsonl> <gsm8k_depth_smoke_40.jsonl>"""
import sys, json
from collections import Counter

run = [json.loads(l) for l in open(sys.argv[1])]
par = {x["idx"]: x for x in map(json.loads, open(sys.argv[2]))}
order = [json.loads(l)["idx"] for l in open(sys.argv[3])]
bucket = {i: ("淺" if k < 14 else "中" if k < 27 else "深") for k, i in enumerate(order)}
assert [r["idx"] for r in run] == order, "idx order/coverage mismatch"

def chain_depth(steps):
    ids = {s.get("id"): s for s in steps}; memo = {}
    def d(i, seen=()):
        if i in memo: return memo[i]
        if i in seen or i not in ids: return None
        us = ids[i].get("uses") or []
        sub = [d(u, seen + (i,)) for u in us]
        if any(x is None for x in sub): return None
        memo[i] = 1 + max(sub, default=0); return memo[i]
    vals = [d(i) for i in ids]
    return None if any(v is None for v in vals) else max(vals, default=0)

rows = []
for r in run:
    p = r["parsed"]; md = p.get("depth") if p else None
    ok_graph = None
    if p and isinstance(p.get("steps"), list):
        cd = chain_depth(p["steps"])
        ok_graph = (cd == md) and (p.get("n_steps") == len(p["steps"]))
    rows.append(dict(idx=r["idx"], b=bucket[r["idx"]], m=md, pd=par[r["idx"]]["parser_depth"], err=r["parse_error"],
                     fenced=r.get("fenced"), trunc=r.get("truncated"), graph=ok_graph, ntok=r.get("n_new_tokens"),
                     flags=(p or {}).get("flags")))

valid = [x for x in rows if isinstance(x["m"], int)]
print("解析失敗", sum(x["err"] for x in rows), "／ 有外框", sum(bool(x["fenced"]) for x in rows),
      "／ 截斷", sum(bool(x["trunc"]) for x in rows), "／ 最長輸出 tokens", max(x["ntok"] or 0 for x in rows))
print("Mistral 深度分佈", dict(sorted(Counter(x["m"] for x in valid).items())))
print("depth 與 uses／n_steps 不自洽", sum(x["graph"] is False for x in rows), [x["idx"] for x in rows if x["graph"] is False])
ex = sum(x["m"] == x["pd"] for x in valid); w1 = sum(abs(x["m"] - x["pd"]) <= 1 for x in valid)
print(f"與程式（修正前）完全一致 {ex}/{len(valid)} = {ex/len(valid):.3f}；差距 ≤1 {w1}/{len(valid)} = {w1/len(valid):.3f}")
for b in "淺中深":
    g = [x for x in valid if x["b"] == b]
    print(f"  {b}: 一致 {sum(x['m']==x['pd'] for x in g)}/{len(g)}")
dis = [x for x in valid if x["m"] != x["pd"]]
print("不一致題號", [(x["idx"], x["pd"], x["m"]) for x in dis])
print("flags 統計", dict(Counter(f for x in rows for f in (x["flags"] or []))))
