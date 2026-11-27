"""Judge inputs for T1/T2 from t12_runner outputs (runs*.jsonl):
correct_input.jsonl : judge_correct_v2 rows for every newly generated round 2 and every round 3 (key t12|<rid>|r2 / |r3);
                      reused round 2 keep their earlier judge results (CP_S2_5 judge_v2.jsonl, smoke round2_judge_v2.jsonl).
extract_input.jsonl / stance_input.jsonl : every round 2 (key t12|<rid>|r2).
Rule verdicts = stage2_round2_metrics.rule (score_baseline_v2 rules), shown in the record only.
usage: python3 scripts/t12_judge_inputs.py <runs.jsonl> [more runs files]"""
import sys, json, re, pathlib
import os; D = pathlib.Path(os.environ.get("T12_D", "out/stage2_measurement_check"))
src = open("scripts/score_baseline_v2.py").read()
ns = {"__file__": "scripts/score_baseline_v2.py"}; sys.path.insert(0, "scripts")
exec(src[:src.index("items = {(x")], ns); last_number, num_eq, norm = ns["last_number"], ns["num_eq"], ns["norm"]
items = {(x["dataset"], str(x["id"])): x for x in map(json.loads, open("data/full_items.jsonl"))}
def rule(ds, it, o):
    if not o or not o.strip(): return "undeterminable"
    if ds == "gsm8k":
        ext = last_number(o); return "undeterminable" if ext is None else "correct" if num_eq(ext, it["answer"]) else "incorrect"
    golds = [it["answer"]] + list(it.get("answer_aliases") or []); no = norm(o)
    return "correct" if any(norm(g) and re.search(rf"(?<!\S){re.escape(norm(g))}(?!\S)", no) for g in golds) else "incorrect"
R = [json.loads(l) for fp in sys.argv[1:] for l in open(fp)]
fc, fe, fs = (open(D / n, "w") for n in ("correct_input.jsonl", "extract_input.jsonl", "stance_input.jsonl")); nc = ne = 0
for r in R:
    it = items[(r["dataset"], r["item_id"])]
    base = dict(model="qwen25omni", dataset=r["dataset"], id=r["item_id"], question=it["question"])
    for rd in ("r2", "r3"):
        o = r[rd].get("raw_output")
        if o is None or (rd == "r2" and r[rd].get("reused")): continue
        fc.write(json.dumps(dict(base, key=f"t12|{r['rid']}|{rd}", run=f"{r['rid']}|{rd}", answer=str(it["answer"]), aliases=list(it.get("answer_aliases") or []),
                                 response=o, truncated=r[rd].get("truncated"), rule_verdict=rule(r["dataset"], it, o)), ensure_ascii=False) + "\n"); nc += 1
    if r["r2"].get("raw_output") is not None:
        x = json.dumps(dict(base, key=f"t12|{r['rid']}|r2", run=f"{r['rid']}|r2", u2_text=r["u2_text"], response=r["r2"]["raw_output"]), ensure_ascii=False) + "\n"
        fe.write(x); fs.write(x); ne += 1
print("correct rows", nc, "extract/stance rows", ne)
