"""Stage 1 cross-model summary (2026-11-22). Reads scored *_v2.jsonl files, prints accuracy per run, paired McNemar
(speech vs text on the same items), and speech-minus-text gap by steps (GSM8K) / hops (MuSiQue).
usage: python summarize_stage1.py name=file1[,file2] ..."""
import sys, json, collections
from math import comb
def mc(a, b):
    n = a + b; k = min(a, b); return min(1, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n) if n else 1
models = {}
for arg in sys.argv[1:]:
    name, files = arg.split("=", 1); v = {}; meta = {}; tr = collections.Counter()
    for fp in files.split(","):
        for l in open(fp):
            x = json.loads(l); k = (x["dataset"], str(x["id"]), x["run"])
            v[k] = x["verdict"] == "correct"; tr[x["run"]] += bool(x["truncated"])
            meta[(x["dataset"], str(x["id"]))] = x.get("total_steps")
    models[name] = (v, meta, tr)
RUNS = ["A_q", "C_q", "A_a", "A_bc", "C_b"]
print("| model | " + " | ".join(RUNS) + " |"); print("|---" * (len(RUNS) + 1) + "|")
for m, (v, meta, tr) in models.items():
    cells = []
    for r in RUNS:
        ks = [k for k in v if k[2] == r]; ok = sum(v[k] for k in ks)
        cells.append(f"{100*ok/len(ks):.1f}% (n={len(ks)}, tr={tr[r]})" if ks else "-")
    print(f"| {m} | " + " | ".join(cells) + " |")
print()
print("| model | dataset | text | speech | gap (pp) | text✓speech✗ | text✗speech✓ | McNemar p |"); print("|---" * 8 + "|")
for m, (v, meta, tr) in models.items():
    for ds, t, s in [("gsm8k", "A_q", "C_q"), ("musique", "A_bc", "C_b")]:
        ids = sorted({i for (d, i, r) in v if d == ds and (d, i, t) in v and (d, i, s) in v})
        a = sum(v[(ds, i, t)] and not v[(ds, i, s)] for i in ids); b = sum(v[(ds, i, s)] and not v[(ds, i, t)] for i in ids)
        T = sum(v[(ds, i, t)] for i in ids); S = sum(v[(ds, i, s)] for i in ids); n = len(ids)
        print(f"| {m} | {ds} (n={n}) | {100*T/n:.1f} | {100*S/n:.1f} | {100*(S-T)/n:+.1f} | {a} | {b} | {mc(a,b):.2g} |")
print()
print("gap by depth (speech - text, pp; n per cell) — GSM8K steps 1-2/3/4/5+, MuSiQue 2/3/4 hop")
for m, (v, meta, tr) in models.items():
    out = []
    for ds, t, s, bins in [("gsm8k", "A_q", "C_q", [(1, 2), (3, 3), (4, 4), (5, 99)]), ("musique", "A_bc", "C_b", [(2, 2), (3, 3), (4, 4)])]:
        for lo, hi in bins:
            ids = [i for (d, i) in meta if d == ds and meta[(d, i)] and lo <= meta[(d, i)] <= hi and (d, i, t) in v and (d, i, s) in v]
            if ids:
                g = 100 * (sum(v[(ds, i, s)] for i in ids) - sum(v[(ds, i, t)] for i in ids)) / len(ids)
                out.append(f"{ds[:2]}{lo}{'+' if hi == 99 else ''}:{g:+.1f}(n={len(ids)})")
    print(m, " ".join(out))
