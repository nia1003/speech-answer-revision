"""Resample the stage-2 smoke 80 by Qwen's first-round status (2026-11-23, user decision). Reads the config written
before sampling (seed, allocation). Writes <out>/smoke80_v2_ids.jsonl and the population counts per cell x bin.
usage: python3 stage2_resample.py <config.json> <out_dir>"""
import sys, json, random, collections, pathlib
cfg = json.load(open(sys.argv[1])); out = pathlib.Path(sys.argv[2])
items = {(x["dataset"], str(x["id"])): x for x in map(json.loads, open("data/full_items.jsonl"))}
fr = {}
for l in open("out/judge_stage1/judged_qwen25omni.jsonl"):
    r = json.loads(l)
    if r["run"] in ("A_q", "C_q", "A_bc", "C_b"): fr[(r["dataset"], str(r["id"]), r["run"][0])] = r
def status(r):
    if r["truncated"] in (True, "True"): return "excluded"
    if r["verdict"] == "judge_fail" or r["rule_verdict"] == "undeterminable": return "excluded"
    if (r["rule_verdict"] == "correct") != (r["verdict"] == "correct"): return "excluded"
    return "correct" if r["verdict"] == "correct" else "wrong"
def sbin(it):
    s = it["total_steps"]
    if it["dataset"] == "gsm8k": return "1-2" if s <= 2 else ("3" if s == 3 else ("4" if s == 4 else "5+"))
    return str(s)
pop = collections.defaultdict(list)
for (ds, iid), it in items.items():
    if ds == "gsm8k" and it.get("no_marker"): continue
    a, c = status(fr[(ds, iid, "A")]), status(fr[(ds, iid, "C")])
    if a == c and a in ("correct", "wrong"): pop[(ds, "both_" + a, sbin(it))].append(iid)
rng = random.Random(cfg["seed"]); picks = []
counts = {f"{k[0]}|{k[1]}|{k[2]}": len(v) for k, v in sorted(pop.items())}
for ds in ("gsm8k", "musique"):
    for st in ("both_correct", "both_wrong"):
        alloc = dict(cfg["allocation"][ds]); bins = list(alloc)
        avail = {b: sorted(pop[(ds, st, b)], key=lambda s: (len(s), s) if ds == "gsm8k" else s) for b in bins}
        short = 0
        for b in bins:
            if len(avail[b]) < alloc[b]: short += alloc[b] - len(avail[b]); alloc[b] = len(avail[b])
        for b in bins:
            if short and len(avail[b]) > alloc[b]:
                add = min(short, len(avail[b]) - alloc[b]); alloc[b] += add; short -= add
        for b in bins:
            for iid in rng.sample(avail[b], alloc[b]):
                picks.append(dict(dataset=ds, id=iid, first_round=st, step_bin=b))
with open(out / "smoke80_v2_ids.jsonl", "w") as f:
    for p in picks: f.write(json.dumps(p) + "\n")
json.dump(counts, open(out / "resample_population_counts.json", "w"), indent=1)
print(len(picks), collections.Counter((p["dataset"], p["first_round"], p["step_bin"]) for p in picks)); print(counts)
