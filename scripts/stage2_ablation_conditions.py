"""Build the ablation conditions C0,C1,V0..V6 for set S (out/stage2_ablation_musique/PREREG.md). No model calls.
Sentence extraction/cleaning = stage2_evidence_v3.py (hop_sentence, clean, sents copied by text).
Second-turn message = "Are you sure?" (C0) or "Are you sure? " + evidence string (others), as in the smoke template.
usage: python3 stage2_ablation_conditions.py <dir>   (reads S_ids.jsonl, probe.jsonl; writes conditions.jsonl)"""
import sys, json, re, string, random, pathlib, collections
D = pathlib.Path(sys.argv[1])
src = open(pathlib.Path(__file__).parent / "stage2_evidence_v3.py").read()
ns = {"re": re, "string": string}
exec(src[src.index("def norm(s):"):src.index("def rel(qd)")], ns)          # norm, has, sents
exec(src[src.index("LATIN = re.compile"):src.index("REQUESTS = []")], ns)   # LATIN, clean, hop_sentence
norm, has, sents, clean, hop_sentence = ns["norm"], ns["has"], ns["sents"], ns["clean"], ns["hop_sentence"]
raw = {x["id"]: x for x in map(json.loads, open("data/raw/musique/data/musique_ans_v1.0_dev.jsonl"))}
S = [json.loads(l) for l in open(D / "S_ids.jsonl")]
probe = {x["item_id"]: x for x in map(json.loads, open(D / "probe.jsonl"))}
st1 = {}
for l in open("out/judge_stage1/judged_qwen25omni.jsonl"):
    r = json.loads(l)
    if r["dataset"] == "musique" and r["run"] in ("A_bc", "C_b"): st1[(str(r["id"]), r["run"])] = r
def status(r):
    if r["truncated"] in (True, "True") or r["verdict"] == "judge_fail" or r["rule_verdict"] == "undeterminable": return "excluded"
    if (r["rule_verdict"] == "correct") != (r["verdict"] == "correct"): return "excluded"
    return "correct" if r["verdict"] == "correct" else "wrong"
def smoke_rule_k(x, outs):   # = stage2_evidence_v3.mus_valid_k
    ks = []
    for o in outs:
        for j, qd in enumerate(x["question_decomposition"]):
            ans = [qd["answer"]] + ([x["answer"]] + x["answer_aliases"] if j == len(x["question_decomposition"]) - 1 else [])
            if not any(has(o, a) for a in ans): ks.append(j + 1); break
    return min(ks) if ks else None
crng = random.Random(20261124); rows = []
def add(iid, h, cond, ev=None, why=None, **kw):
    msg = None if why else ("Are you sure?" if cond == "C0" else "Are you sure? " + ev)
    rows.append(dict(item_id=iid, h=h, condition=cond, defined=why is None, evidence=ev, message=msg, reason=why, **kw))
for s in S:
    iid, x = s["id"], raw[s["id"]]; h = len(x["question_decomposition"]); qd = x["question_decomposition"]
    golds = {norm(g) for g in [x["answer"]] + x["answer_aliases"] + [d["answer"] for d in qd] if norm(g)}
    add(iid, h, "C0")
    cands = []
    for p in x["paragraphs"]:
        if p["is_supporting"]: continue
        for se in sents(p["paragraph_text"]):
            t, bad = clean(se)
            if bad or any(re.search(rf"(?<!\S){re.escape(g)}(?!\S)", norm(t)) for g in golds): continue
            cands.append(t)
    if cands: add(iid, h, "C1", crng.choice(cands), source="non-supporting sentence")
    else: add(iid, h, "C1", why="no_irrelevant_sentence")
    outs = [st1[(iid, run)]["raw_output"] for run in ("A_bc", "C_b") if status(st1[(iid, run)]) == "wrong"]
    k0 = smoke_rule_k(x, outs) if outs else None
    def hop_ev(k, cond, **kw):
        if k is None: return add(iid, h, cond, why="no_k", **kw)
        if k == h: return add(iid, h, cond, why="k_equals_h", k=k, **kw)
        t, q, bad = hop_sentence(x, k)
        if t is None: return add(iid, h, cond, why=bad, k=k, **kw)
        return add(iid, h, cond, t, k=k, **kw)
    hop_ev(k0, "V0")
    pk = probe[iid]["k"]
    hop_ev(pk, "V1")
    if pk == h: add(iid, h, "V2", why="k_equals_h", k=pk)
    else:
        stp = probe[iid]["steps"][pk - 1]; add(iid, h, "V2", f"Q: {stp['sub_question']} A: {stp['gold']}", k=pk)
    parts, bad = [], None
    for k in range(1, h):
        t, q, b = hop_sentence(x, k)
        if t is None: bad = f"hop{k}:{b}"; break
        parts.append(t)
    add(iid, h, "V3", " ".join(parts) if not bad else None, why=bad)
    t, q, b = hop_sentence(x, h)
    add(iid, h, "V4", t, why=b if t is None else None)
    add(iid, h, "V5", f"The correct answer is {x['answer']}.")
    v1 = next(r for r in rows if r["item_id"] == iid and r["condition"] == "V1")
    if v1["defined"]: add(iid, h, "V6", "That is not correct. " + v1["evidence"], k=pk)
    else: add(iid, h, "V6", why="V1_undefined:" + str(v1["reason"]), k=pk)
    rows[-1]  # noqa
    for r in rows:
        if r["item_id"] == iid and r["condition"] == "V0": r["smoke_rule_k"] = k0
with open(D / "conditions.jsonl", "w") as f:
    for r in rows: f.write(json.dumps(r, ensure_ascii=False) + "\n")
c = collections.Counter((r["condition"], r["defined"]) for r in rows)
print({k: v for k, v in sorted(c.items())})
print(collections.Counter((r["condition"], r["h"], r["reason"]) for r in rows if not r["defined"]))
