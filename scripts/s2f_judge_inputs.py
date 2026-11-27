"""Formal run judge inputs (2026-11-25), same construction as t12_judge_inputs.py:
correct_input.jsonl: judge_correct_v2 rows for every round 2 and every round 3 (key s2f|<ds>|<id>|<mod>|<et>|r2 / |r3).
extract_input.jsonl / stance_input.jsonl: every round 2. u2_text = text form of round 2 ("Are you sure?" [+ evidence text]),
also for speech (as in T1/T2). Rule verdicts = score_baseline_v2 rules, shown in the record only.
usage: python3 s2f_judge_inputs.py <out_dir> <round23 shard files...>"""
import sys, json, re, pathlib, os
D = pathlib.Path(sys.argv[1]); D.mkdir(parents=True, exist_ok=True)
for n in ("correct_input.jsonl", "extract_input.jsonl", "stance_input.jsonl"): assert not (D / n).exists(), n
src = open("scripts/score_baseline_v2.py").read()
ns = {"__file__": "scripts/score_baseline_v2.py"}; sys.path.insert(0, "scripts")
exec(src[:src.index("items = {(x")], ns); last_number, num_eq, norm = ns["last_number"], ns["num_eq"], ns["norm"]
items = {(x["dataset"], str(x["id"])): x for x in map(json.loads, open("data/full_items.jsonl"))}
EV = {(r["dataset"], r["item_id"], r["evidence_type"]): r for r in map(json.loads, open("out/stage2_full_qwen/evidence_final_pass2.jsonl"))}
def rule(ds, it, o):
    if not o or not o.strip(): return "undeterminable"
    if ds == "gsm8k":
        ext = last_number(o); return "undeterminable" if ext is None else "correct" if num_eq(ext, it["answer"]) else "incorrect"
    golds = [it["answer"]] + list(it.get("answer_aliases") or []); no = norm(o)
    return "correct" if any(norm(g) and re.search(rf"(?<!\S){re.escape(norm(g))}(?!\S)", no) for g in golds) else "incorrect"
fc, fe, fs = (open(D / n, "w") for n in ("correct_input.jsonl", "extract_input.jsonl", "stance_input.jsonl")); nc = ne = 0
for fp in sys.argv[2:]:
    for r in map(json.loads, open(fp)):
        ds, iid, mod, et = r["dataset"], r["id"], r["modality"], r["evidence_type"]; it = items[(ds, iid)]
        u2t = "Are you sure?" if et == "unsupported" else "Are you sure? " + EV[(ds, iid, et)]["evidence_text"]
        if mod == "text": assert r["user2_text"] == u2t, (ds, iid, et)
        rid = f"s2f|{ds}|{iid}|{mod}|{et}"; base = dict(model="qwen25omni", dataset=ds, id=iid, question=it["question"])
        for rd, o, tr in (("r2", r["raw_output"], r["truncated"]), ("r3", r["r3"]["raw_output"], r["r3"].get("truncated"))):
            fc.write(json.dumps(dict(base, key=f"{rid}|{rd}", run=f"{rid}|{rd}", answer=str(it["answer"]), aliases=list(it.get("answer_aliases") or []),
                                     response=o, truncated=tr, rule_verdict=rule(ds, it, o)), ensure_ascii=False) + "\n"); nc += 1
        x = json.dumps(dict(base, key=f"{rid}|r2", run=f"{rid}|r2", u2_text=u2t, response=r["raw_output"]), ensure_ascii=False) + "\n"
        fe.write(x); fs.write(x); ne += 1
print("correct rows", nc, "extract/stance rows", ne)
