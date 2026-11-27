"""Stage 1: accuracy by reasoning-step bin, raw counts + Wilson 95% CI (2026-11-23). Read-only on scored files.
GSM8K: steps = number of <<>> in the gold solution (= items total_steps, checked 1,301/1,301), bins 1–2/3/4/5+,
       18 items without <<>> excluded. Text = A_q, speech = C_q.
MuSiQue: hops (total_steps) 2/3/4. Text = A_bc, speech = C_b. A_a not used.
Correct = verdict == "correct" (undeterminable / judge_fail count as not correct).
Stops (exit 1) if any cell's n differs from CP_B17: GSM8K 422/364/290/225, MuSiQue 1,252/760/405.
usage: python3 steps_accuracy_table.py <out.csv>"""
import sys, json, csv, math, collections
MODELS = ["qwen25omni", "ultravox", "llamaomni2", "kimiaudio", "glm4voice"]
RULE = {"qwen25omni": ["out/full/scored_full_textA_qwen25omni_sdpa_v2.jsonl", "out/full_speechC/scored_full_speechC_qwen25omni_sdpa_v2.jsonl"],
        "ultravox": ["out/full_ultravox/scored_full_ultravox_sdpa_v2.jsonl"],
        "llamaomni2": ["out/full_llamaomni2/scored_full_llamaomni2_sdpa_withchunk_v2.jsonl"],
        "kimiaudio": ["out/full_kimiaudio/scored_full_kimiaudio_sdpa_cut_v2.jsonl"],
        "glm4voice": ["out/full_glm4voice/scored_full_glm4voice_sdpa_v2.jsonl"]}
JUDGE = {m: [f"out/judge_stage1/judged_{m}.jsonl"] for m in MODELS}
RUNS = {"A_q": ("gsm8k", "text"), "C_q": ("gsm8k", "speech"), "A_bc": ("musique", "text"), "C_b": ("musique", "speech")}
EXPECT = {"gsm8k": {"1-2": 422, "3": 364, "4": 290, "5+": 225}, "musique": {"2": 1252, "3": 760, "4": 405}}
items = {(x["dataset"], str(x["id"])): x for x in map(json.loads, open("data/full_items.jsonl"))}
def sbin(it):
    if it["dataset"] == "gsm8k":
        if it.get("no_marker"): return None
        s = it["total_steps"]; return "1-2" if s <= 2 else ("3" if s == 3 else ("4" if s == 4 else "5+"))
    return str(it["total_steps"])
def wilson(k, n, z=1.959964):
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h
rows, bad = [], []
for scorer, files in [("rule", RULE), ("judge", JUDGE)]:
    for m in MODELS:
        cnt = collections.defaultdict(lambda: [0, 0]); seen = set()
        for fp in files[m]:
            for l in open(fp):
                r = json.loads(l)
                if r["run"] not in RUNS: continue
                key = (r["dataset"], str(r["id"]), r["run"])
                if key in seen: bad.append(f"duplicate {scorer} {m} {key}"); continue
                seen.add(key); ds, mod = RUNS[r["run"]]; b = sbin(items[(r["dataset"], str(r["id"]))])
                if b is None: continue
                cnt[(ds, mod, b)][0] += r["verdict"] == "correct"; cnt[(ds, mod, b)][1] += 1
        for ds in EXPECT:
            for mod in ("text", "speech"):
                for b, ne in EXPECT[ds].items():
                    k, n = cnt[(ds, mod, b)]
                    if n != ne: bad.append(f"n mismatch {scorer} {m} {ds} {mod} {b}: {n} != {ne}"); continue
                    lo, hi = wilson(k, n)
                    rows.append(dict(scorer=scorer, dataset=ds, model=m, modality=mod, step_bin=b, n=n, n_correct=k,
                                     accuracy=round(k / n, 4), wilson95_low=round(lo, 4), wilson95_high=round(hi, 4)))
if bad:
    print("STOP:", *bad[:20], sep="\n"); sys.exit(1)
with open(sys.argv[1], "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print(f"wrote {len(rows)} rows; all n match CP_B17")
