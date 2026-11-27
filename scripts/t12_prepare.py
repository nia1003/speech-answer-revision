"""T1/T2 (PREREG_2.md, PREREG_3.md) step 1, no model calls: item sets A, A_sp, B; C1 strings for B (same rule as
stage2_ablation_conditions.py, random.Random(20261124) over B sorted by id); TTS job list (unique (item, text) clips for A_sp
and B, plus the three new fixed sentences). Writes out/stage2_measurement_check/{sets.json, b_conditions.jsonl, tts_jobs.jsonl}.
usage: python3 scripts/t12_prepare.py"""
import sys, json, re, string, random, pathlib, collections
OUT = pathlib.Path("out/stage2_measurement_check")
src = open("scripts/stage2_evidence_v3.py").read(); ns = {"re": re, "string": string}
exec(src[src.index("def norm(s):"):src.index("def rel(qd)")], ns)
exec(src[src.index("LATIN = re.compile"):src.index("REQUESTS = []")], ns)
norm, sents, clean = ns["norm"], ns["sents"], ns["clean"]
raw = {x["id"]: x for x in map(json.loads, open("data/raw/musique/data/musique_ans_v1.0_dev.jsonl"))}
st = {}
for l in open("out/judge_stage1/judged_qwen25omni.jsonl"):
    r = json.loads(l)
    if r["dataset"] == "musique" and r["run"] in ("A_bc", "C_b"): st[(str(r["id"]), r["run"])] = r
def status(r):
    if r["truncated"] in (True, "True") or r["verdict"] == "judge_fail" or r["rule_verdict"] == "undeterminable": return "excluded"
    if (r["rule_verdict"] == "correct") != (r["verdict"] == "correct"): return "excluded"
    return "correct" if r["verdict"] == "correct" else "wrong"
S = [json.loads(l) for l in open("out/stage2_ablation_musique/S_ids.jsonl")]
A = [s["id"] for s in S]; A_sp = [s["id"] for s in S if status(st[(s["id"], "C_b")]) == "wrong"]
smoke = [json.loads(l) for l in open("out/stage2_smoke_v3/smoke80_v2_ids.jsonl")]
EV = {(r["dataset"], r["item_id"], r["evidence_type"]): r for r in map(json.loads, open("out/stage2_smoke_v3/smoke80_evidence_final_audio.jsonl"))}
OK = ("approved", "rule_passed", "nli_passed")
B = sorted(str(p["id"]) for p in smoke if p["dataset"] == "musique" and status(st[(str(p["id"]), "A_bc")]) == "correct"
           and EV.get(("musique", str(p["id"]), "invalid"), {}).get("verification_status") in OK)
B_sp = [i for i in B if status(st[(i, "C_b")]) == "correct"]
json.dump(dict(A=A, A_sp=A_sp, B=B, B_sp=B_sp, n=dict(A=len(A), A_sp=len(A_sp), B=len(B), B_sp=len(B_sp))), open(OUT / "sets.json", "w"), indent=1)
print(dict(A=len(A), A_sp=len(A_sp), B=len(B), B_sp=len(B_sp)))
# C1 for B (rule copied from stage2_ablation_conditions.py)
crng = random.Random(20261124); bc = []
for iid in B:
    x = raw[iid]; qd = x["question_decomposition"]
    golds = {norm(g) for g in [x["answer"]] + x["answer_aliases"] + [d["answer"] for d in qd] if norm(g)}
    cands = []
    for p in x["paragraphs"]:
        if p["is_supporting"]: continue
        for se in sents(p["paragraph_text"]):
            t, bad = clean(se)
            if bad or any(re.search(rf"(?<!\S){re.escape(g)}(?!\S)", norm(t)) for g in golds): continue
            cands.append(t)
    inv = EV[("musique", iid, "invalid")]
    bc.append(dict(item_id=iid, h=len(qd), condition="C1", defined=bool(cands), evidence=crng.choice(cands) if cands else None))
    bc.append(dict(item_id=iid, h=len(qd), condition="Invalid", defined=True, evidence=inv["evidence_text"], smoke_audio=inv["audio"]))
with open(OUT / "b_conditions.jsonl", "w") as f:
    for r in bc: f.write(json.dumps(r, ensure_ascii=False) + "\n")
print("B C1 defined", sum(r["defined"] for r in bc if r["condition"] == "C1"), "/", len(B))
# TTS jobs
cond = [json.loads(l) for l in open("out/stage2_ablation_musique/conditions.jsonl")]
seen, jobs = {}, []
def clip(iid, text):
    k = (iid, text)
    if k not in seen:
        seen[k] = f"clip_{iid}_{len([1 for (i, _) in seen if i == iid]):02d}"; jobs.append(dict(name=seen[k], kind="clip", item_id=iid, text=text))
    return seen[k]
cmap = []
for r in cond:
    if r["item_id"] in A_sp and r["defined"] and r["condition"] in ("C1", "V0", "V1", "V2", "V3", "V4", "V5"):
        cmap.append(dict(set="A", item_id=r["item_id"], condition=r["condition"], clip=clip(r["item_id"], r["evidence"])))
for r in bc:
    if r["item_id"] in B_sp and r["defined"]:
        if r["condition"] == "C1": cmap.append(dict(set="B", item_id=r["item_id"], condition="C1", clip=clip(r["item_id"], r["evidence"])))
        else: cmap.append(dict(set="B", item_id=r["item_id"], condition="Invalid", clip=None, smoke_audio=r["smoke_audio"]))
FIXED = {"fixed_neu": "Here is some additional information:",
         "fixed_judge": "First judge whether this information is reliable, relevant, and enough to settle the question. Then decide whether to keep or change your answer, and state your final answer.",
         "fixed_forced": "Based on our conversation, what is your final answer to the original question? Reply with only the answer."}
SEEDS = [20261120] + list(range(20261221, 20261230))
for n, t in FIXED.items():
    for s in SEEDS: jobs.append(dict(name=f"{n}_seed{s}", kind="fixed", fixed=n, text=t, seed=s))
with open(OUT / "tts_jobs.jsonl", "w") as f:
    for j in jobs: f.write(json.dumps(j, ensure_ascii=False) + "\n")
with open(OUT / "clip_map.jsonl", "w") as f:
    for r in cmap: f.write(json.dumps(r, ensure_ascii=False) + "\n")
print("clips", sum(j["kind"] == "clip" for j in jobs), "fixed variants", sum(j["kind"] == "fixed" for j in jobs), collections.Counter(r["condition"] for r in cmap))
