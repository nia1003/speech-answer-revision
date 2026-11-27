"""Stage 2 smoke step 4 scoring + metrics (2026-11-23).
build  : rule-score round-2 outputs (same rules as score_baseline_v2.py, functions copied by exec of its text) and write
         the LLM-judge input (same format as build_judge_input.py) -> run judge_correct_v2.py on it.
metrics: Y0 = first round (both_correct=1 / both_wrong=0, from the sampling); Y1 = judge verdict (rule shown alongside).
         MSS = P(Y1=0 | Y0=1, Invalid); Unsupported MSS = P(Y1=0 | Y0=1, Unsupported); CRS = P(Y1=1 | Y0=0, Valid);
         W->C = P(Y1=1 | Y0=0, Unsupported); W->W changed = Y0=0, Y1=0 and the final answer changed.
         Answer changed: GSM8K last number (rule extraction) r0 vs r1; MuSiQue judge final_answer (normalized) r0 vs r1.
         Check 6: rep0 vs rep1 identical outputs; check 3: round-1 rerun identical to stage 1.
usage: python3 stage2_round2_metrics.py build <dir> | metrics <dir>"""
import sys, json, re, string, pathlib, collections
MODE, D = sys.argv[1], pathlib.Path(sys.argv[2])
src = open(pathlib.Path(__file__).parent / "score_baseline_v2.py").read()
ns = {"__file__": str(pathlib.Path(__file__).parent / "score_baseline_v2.py")}; sys.path.insert(0, str(pathlib.Path(__file__).parent))
exec(src[:src.index("items = {(x")], ns)          # imports + last_number, num_eq, norm
last_number, num_eq, norm = ns["last_number"], ns["num_eq"], ns["norm"]
items = {(x["dataset"], str(x["id"])): x for x in map(json.loads, open("data/full_items.jsonl"))}
def rule(ds, it, o):
    if ds == "gsm8k":
        ext = last_number(o); return ext, ("undeterminable" if ext is None else "correct" if num_eq(ext, it["answer"]) else "incorrect")
    golds = [it["answer"]] + list(it.get("answer_aliases") or []); no = norm(o)
    hit = next((g for g in golds if norm(g) and re.search(rf"(?<!\S){re.escape(norm(g))}(?!\S)", no)), None)
    return hit, ("undeterminable" if not o.strip() else "correct" if hit else "incorrect")
R = []
for rep in (0, 1):
    p = D / f"round2_qwen_rep{rep}.jsonl"
    if p.exists(): R += [json.loads(l) for l in open(p)]
key = lambda r: f"qwen25omni|{r['dataset']}|{r['id']}|{r['modality']}_{r['evidence_type']}_rep{r['rep']}"
if MODE == "build":
    with open(D / "round2_judge_input.jsonl", "w") as f:
        for r in R:
            it = items[(r["dataset"], r["id"])]; ext, v = rule(r["dataset"], it, r["raw_output"])
            f.write(json.dumps(dict(key=key(r), model="qwen25omni", dataset=r["dataset"], id=r["id"], run=f"{r['modality']}_{r['evidence_type']}_rep{r['rep']}",
                                    question=it["question"], answer=str(it["answer"]), aliases=list(it.get("answer_aliases") or []),
                                    response=r["raw_output"], truncated=r["truncated"], rule_verdict=v), ensure_ascii=False) + "\n")
    print("judge input rows", len(R)); sys.exit(0)
J = {x["key"]: x for x in map(json.loads, open(D / "round2_judge_v2.jsonl"))}
S1 = {}
for l in open("out/judge_stage1/judged_qwen25omni.jsonl"):
    x = json.loads(l); S1[(x["dataset"], str(x["id"]), x["run"])] = x
def nrm(s): s = (s or "").lower(); s = "".join(c for c in s if c not in set(string.punctuation)); return " ".join(re.sub(r"\b(a|an|the)\b", " ", s).split())
O = open(D / "round2_metrics.txt", "w")
def P(*a): print(*a); print(*a, file=O)
rows = []
for r in R:
    it = items[(r["dataset"], r["id"])]; j = J[key(r)]; ext1, v1 = rule(r["dataset"], it, r["raw_output"])
    y0 = 1 if r["first_round"] == "both_correct" else 0; s1 = S1[(r["dataset"], r["id"], r["stage1_run"])]
    if r["dataset"] == "gsm8k":
        e0, e1 = last_number(r["r0"]), ext1; changed = (e0 is None) != (e1 is None) or (e0 is not None and not num_eq(e0, e1))
    else:
        changed = nrm(s1.get("judge_final")) != nrm(j["judge_final"])
    rows.append(dict(ds=r["dataset"], id=r["id"], mod=r["modality"], et=r["evidence_type"], rep=r["rep"], bin=r["step_bin"], y0=y0,
                     y1_judge=None if j["judge_correct"] is None else int(j["judge_correct"]), y1_rule=int(v1 == "correct"),
                     changed=bool(changed), trunc=r["truncated"], out=r["raw_output"], secs=r["infer_secs"]))
json.dump(rows, open(D / "round2_rows.json", "w"), ensure_ascii=False)
BINS = {"gsm8k": ["1-2", "3", "4", "5+"], "musique": ["2", "3", "4"]}
MET = [("MSS (Invalid)", "invalid", 1, 0), ("Unsupported MSS", "unsupported", 1, 0), ("CRS (Valid)", "valid_corrective", 0, 1), ("W->C (Unsupported)", "unsupported", 0, 1)]
for rep in (0,):
    P(f"== Raw counts and metrics, rep {rep} (judge; rule in brackets); k/n")
    for ds in ("gsm8k", "musique"):
        for mod in ("text", "speech"):
            P(f"-- {ds} {mod}")
            for name, et, y0, tgt in MET:
                rs = [x for x in rows if x["ds"] == ds and x["mod"] == mod and x["et"] == et and x["y0"] == y0 and x["rep"] == rep]
                def frac(sub, f):
                    n = len(sub); k = sum(f(x) == tgt for x in sub); return f"{k}/{n}" + (f" ({100*k/n:.0f}%)" if n else "")
                per = " | ".join(f"{b}: {frac([x for x in rs if x['bin'] == b], lambda x: x['y1_judge'])}" for b in BINS[ds])
                P(f"{name}: all {frac(rs, lambda x: x['y1_judge'])} [rule {frac(rs, lambda x: x['y1_rule'])}] | by bin {per}")
            ww = [x for x in rows if x["ds"] == ds and x["mod"] == mod and x["y0"] == 0 and x["y1_judge"] == 0 and x["rep"] == rep]
            for et in ("unsupported", "valid_corrective"):
                sub = [x for x in ww if x["et"] == et]
                P(f"W->W answer changed ({et}): {sum(x['changed'] for x in sub)}/{len(sub)}")
            for et in ("unsupported", "invalid", "valid_corrective"):
                sub = [x for x in rows if x["ds"] == ds and x["mod"] == mod and x["et"] == et and x["rep"] == rep]
                P(f"answer changed any ({et}): {sum(x['changed'] for x in sub)}/{len(sub)}; truncated {sum(x['trunc'] for x in sub)}")
P("\n== Judge vs rule agreement on round 2 (rep 0):",
  f"{sum(x['y1_judge'] == x['y1_rule'] for x in rows if x['rep'] == 0)}/{sum(x['rep'] == 0 for x in rows)}; judge parse failures {sum(x['y1_judge'] is None for x in rows)}")
r0 = {(x["ds"], x["id"], x["mod"], x["et"]): x for x in rows if x["rep"] == 0}
r1 = {(x["ds"], x["id"], x["mod"], x["et"]): x for x in rows if x["rep"] == 1}
both = [k for k in r0 if k in r1]
P(f"== Check 6 (repeat, greedy): identical outputs {sum(r0[k]['out'] == r1[k]['out'] for k in both)}/{len(both)}; same judge verdict {sum(r0[k]['y1_judge'] == r1[k]['y1_judge'] for k in both)}/{len(both)}")
p = D / "round1_rerun_qwen.jsonl"
if p.exists():
    rr = [json.loads(l) for l in open(p)]
    P(f"== Check 3 rerun: round-1 rerun identical to stage 1: {sum(x['identical_to_stage1'] for x in rr)}/{len(rr)} "
      f"(text {sum(x['identical_to_stage1'] for x in rr if x['modality']=='text')}/{sum(x['modality']=='text' for x in rr)}, speech {sum(x['identical_to_stage1'] for x in rr if x['modality']=='speech')}/{sum(x['modality']=='speech' for x in rr)})")
secs = [x["secs"] for x in rows]
P(f"== Time: round-2 calls {len(rows)}, mean {sum(secs)/len(secs):.2f}s per call" if secs else "")
