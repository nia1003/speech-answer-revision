"""Ablation scoring + metrics (out/stage2_ablation_musique/PREREG.md).
build  : judge input for round2.jsonl (judge_correct_v2 format) + rule verdicts.
metrics: per condition N / unchanged / changed-to-wrong / changed-to-correct (correct by judge; changed = token F1 between
         the round-2 judge final_answer and the stage-1 judge final_answer < 0.5), W->C with Wilson 95% CI; paired exact
         McNemar (two-sided) on items defined in both; "clearly higher" = diff >= 10 pp and p < 0.05; P1-P4; decision table
         and adoption rule evaluated mechanically.
usage: python3 stage2_ablation_metrics.py build|metrics <dir>"""
import sys, json, re, string, math, pathlib, collections
from math import comb
MODE, D = sys.argv[1], pathlib.Path(sys.argv[2])
src = open(pathlib.Path(__file__).parent / "score_baseline_v2.py").read()
ns = {"__file__": str(pathlib.Path(__file__).parent / "score_baseline_v2.py")}; sys.path.insert(0, str(pathlib.Path(__file__).parent))
exec(src[:src.index("items = {(x")], ns); rnorm = ns["norm"]
items = {str(x["id"]): x for x in map(json.loads, open("data/full_items.jsonl")) if x["dataset"] == "musique"}
R = [json.loads(l) for l in open(D / "round2.jsonl")]
def rule(it, o):
    if not o: return "undeterminable"
    golds = [it["answer"]] + list(it.get("answer_aliases") or [])
    return "correct" if any(rnorm(g) and re.search(rf"(?<!\S){re.escape(rnorm(g))}(?!\S)", rnorm(o)) for g in golds) else "incorrect"
key = lambda r: f"qwen25omni|musique|{r['item_id']}|{r['condition']}"
if MODE == "build":
    with open(D / "judge_input.jsonl", "w") as f:
        for r in R:
            if r.get("raw_output") is None: continue
            it = items[r["item_id"]]
            f.write(json.dumps(dict(key=key(r), model="qwen25omni", dataset="musique", id=r["item_id"], run=r["condition"], question=it["question"],
                                    answer=str(it["answer"]), aliases=list(it.get("answer_aliases") or []), response=r["raw_output"],
                                    truncated=r.get("truncated"), rule_verdict=rule(it, r["raw_output"])), ensure_ascii=False) + "\n")
    print("judge rows", sum(r.get("raw_output") is not None for r in R)); sys.exit(0)
J = {x["key"]: x for x in map(json.loads, open(D / "judge_v2.jsonl"))}
S1 = {}
for l in open("out/judge_stage1/judged_qwen25omni.jsonl"):
    x = json.loads(l)
    if x["dataset"] == "musique" and x["run"] == "A_bc": S1[str(x["id"])] = x
def norm(s): s = (s or "").lower(); s = "".join(c for c in s if c not in set(string.punctuation)); return " ".join(re.sub(r"\b(a|an|the)\b", " ", s).split())
def f1(a, b):
    ta, tb = norm(a).split(), norm(b).split()
    if not ta or not tb: return 0.0
    c = sum((collections.Counter(ta) & collections.Counter(tb)).values())
    return 0.0 if c == 0 else 2 * (c / len(ta)) * (c / len(tb)) / (c / len(ta) + c / len(tb))
def wilson(k, n, z=1.959964):
    if n == 0: return (float("nan"), float("nan"))
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d; return c - h, c + h
def mcnemar(b, c):
    n = b + c; k = min(b, c); return 1.0 if n == 0 else min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n)
O = open(D / "metrics.txt", "w")
def P(*a): print(*a); print(*a, file=O)
COND = ["C0", "C1", "V0", "V1", "V2", "V3", "V4", "V5", "V6"]
cond_rows = [json.loads(l) for l in open(D / "conditions.jsonl")]
defined = collections.Counter(r["condition"] for r in cond_rows if r["defined"])
res = collections.defaultdict(dict); errs = collections.Counter(); trunc = collections.Counter()
for r in R:
    c, iid = r["condition"], r["item_id"]
    if r.get("raw_output") is None: errs[c] += 1; continue
    j = J.get(key(r))
    if j is None or j["judge_correct"] is None: errs[c] += 1; continue
    trunc[c] += bool(r.get("truncated"))
    y = int(j["judge_correct"]); ch = f1(j["judge_final"], S1[iid].get("judge_final")) < 0.5
    res[c][iid] = dict(y=y, changed=ch, rule=int(rule(items[iid], r["raw_output"]) == "correct"), out=r["raw_output"])
# P1 purity
p1 = [iid for iid, x in S1.items() if iid in {r["item_id"] for r in cond_rows} and
      any(norm(x.get("judge_final")) == norm(g) or (norm(g) and re.search(rf"(?<!\S){re.escape(norm(g))}(?!\S)", norm(x.get("judge_final")))) or f1(x.get("judge_final"), g) >= 0.8
          for g in [items[iid]["answer"]] + list(items[iid].get("answer_aliases") or []))]
nS = len({r["item_id"] for r in cond_rows})
def table(excl=set(), title=""):
    P(f"\n== Raw counts per condition {title} (correct by judge; rule correct in brackets)")
    P("| condition | defined | N scored | errors | truncated | unchanged | changed to wrong | changed to correct | W->C | Wilson 95% | rule correct |")
    P("|---" * 11 + "|")
    W = {}
    for c in COND:
        d = {i: v for i, v in res[c].items() if i not in excl}; n = len(d); k = sum(v["y"] for v in d.values())
        un = sum(1 for v in d.values() if not v["y"] and not v["changed"]); tw = sum(1 for v in d.values() if not v["y"] and v["changed"])
        lo, hi = wilson(k, n); W[c] = k / n if n else float("nan")
        P(f"| {c} | {defined[c]} | {n} | {errs[c]} | {trunc[c]} | {un} | {tw} | {k} | {100*W[c]:.1f}% | {100*lo:.1f}–{100*hi:.1f}% | {sum(v['rule'] for v in d.values())} |")
    return W
def cmp(a, b, excl=set()):
    ids = [i for i in res[a] if i in res[b] and i not in excl]; n = len(ids)
    if not n: return dict(n=0, diff=float("nan"), p=1.0, clearly_higher=False)
    ya = sum(res[a][i]["y"] for i in ids) / n; yb = sum(res[b][i]["y"] for i in ids) / n
    bb = sum(res[a][i]["y"] and not res[b][i]["y"] for i in ids); cc = sum(res[b][i]["y"] and not res[a][i]["y"] for i in ids)
    p = mcnemar(bb, cc); d = 100 * (ya - yb)
    return dict(n=n, a=round(100 * ya, 1), b=round(100 * yb, 1), diff=round(d, 1), a_only=bb, b_only=cc, p=p, clearly_higher=d >= 10 and p < 0.05)
W = table()
P(f"\nP1 first-round purity: stage-1 final answers that match gold/alias, contain it, or F1>=0.8: {len(p1)}/{nS} ({100*len(p1)/nS:.1f}%) -> {p1}")
if len(p1) / nS >= 0.10: W2 = table(set(p1), "(P1: excluding items whose first-round answer is actually correct)")
PAIRS = [("V1", "V0"), ("V3", "V0"), ("V2", "V1"), ("V4", "V1"), ("V6", "V1"), ("V0", "C0"), ("V0", "C1"), ("V1", "C0"), ("V1", "C1"),
         ("V2", "C0"), ("V2", "C1"), ("V4", "C0"), ("V5", "C0"), ("C1", "C0"), ("V3", "C0")]
P("\n== Paired comparisons (items defined in both; exact McNemar two-sided)")
P("| A vs B | paired N | A W->C | B W->C | diff pp | A only | B only | p | A clearly higher |"); P("|---" * 9 + "|")
CMP = {}
for a, b in PAIRS:
    x = cmp(a, b); CMP[(a, b)] = x
    P(f"| {a} vs {b} | {x['n']} | {x.get('a')} | {x.get('b')} | {x['diff']} | {x.get('a_only')} | {x.get('b_only')} | {x['p']:.3g} | {x['clearly_higher']} |")
yes = lambda o: bool(re.match(r"^[\W_]*(yes|i'm sure|i am sure)", (o or "").strip().lower()))
for c in ("V0", "C0"):
    d = res[c]; P(f"P2 {c}: responses starting with yes / I'm sure / I am sure: {sum(yes(v['out']) for v in d.values())}/{len(d)}")
PR = [json.loads(l) for l in open(D / "probe.jsonl")]
P("\nP3 probe accuracy per hop, by hop count:")
for h in (2, 3, 4):
    ph = [p for p in PR if p["h"] == h]
    acc = [f"hop{j+1} {sum(p['steps'][j]['correct'] for p in ph)}/{len(ph)}" for j in range(h)]
    P(f"  {h}-hop (n={len(ph)}): " + ", ".join(acc) + f"; all correct {sum(p['all_correct'] for p in ph)}/{len(ph)}; probe-k {dict(sorted(collections.Counter(p['k'] for p in ph).items()))}")
allc = sum(p["all_correct"] for p in PR); P(f"  all correct overall: {allc}/{len(PR)} ({100*allc/len(PR):.1f}%)")
v0k = {r["item_id"]: r.get("smoke_rule_k") for r in cond_rows if r["condition"] == "V0"}
both = [p for p in PR if v0k.get(p["item_id"]) is not None]
agree = sum(p["k"] == v0k[p["item_id"]] for p in both)
P(f"P4 probe-k vs smoke rule k agreement: {agree}/{len(both)} ({100*agree/max(1,len(both)):.1f}%)")
P("\n== Decision table (as preregistered)")
pct = lambda c: 100 * W[c]
P(f"- V5 W->C < 50%? {pct('V5'):.1f}% -> {'YES: protocol/judging problem; look at P1, P2; no other conclusions' if pct('V5') < 50 else 'no'}")
r2 = (CMP[("V1", "V0")]["clearly_higher"] or CMP[("V3", "V0")]["clearly_higher"]); p4ok = agree / max(1, len(both)) >= 0.8
P(f"- V1>V0 or V3>V0 clearly? {r2} (V1vsV0 {CMP[('V1','V0')]['clearly_higher']}, V3vsV0 {CMP[('V3','V0')]['clearly_higher']}); P4 >= 80%? {p4ok} -> "
  f"{'k mislocation is one cause' if r2 and not p4ok else 'not supported'}")
P(f"- V2>V1 clearly? {CMP[('V2','V1')]['clearly_higher']} -> {'evidence sentence not self-contained' if CMP[('V2','V1')]['clearly_higher'] else 'not supported'}")
r4 = pct("V4") - pct("V1") >= 20 and pct("V1") < 10
P(f"- V4 >= V1 + 20 pp and V1 < 10%? {r4} (V4 {pct('V4'):.1f}%, V1 {pct('V1'):.1f}%) -> {'evidence insufficient; model needs to see the answer' if r4 else 'not supported'}")
inert = all(abs(pct(v) - pct(c)) < 5 for v in ("V0", "V1", "V2") for c in ("C0", "C1")) and pct("V4") > max(pct("C0"), pct("C1")) and pct("V5") > max(pct("C0"), pct("C1"))
P(f"- V0,V1,V2 within 5 pp of C0 and C1, V4 and V5 high? {inert} -> {'hop-level evidence is inert' if inert else 'not supported'}")
P(f"- V6>V1 clearly? {CMP[('V6','V1')]['clearly_higher']} -> {'missing assertive tone' if CMP[('V6','V1')]['clearly_higher'] else 'not supported'}")
P(f"- P3 all correct >= 50%? {allc/len(PR) >= 0.5} -> {'composition, not retrieval; single-hop evidence cannot fix it in principle' if allc/len(PR) >= 0.5 else 'not supported'}")
P("\n== Adoption rule")
ad = {}
for v in ("V1", "V2"):
    c1 = W[v] >= 0.15; c2 = CMP[(v, "C0")]["clearly_higher"] and CMP[(v, "C1")]["clearly_higher"]; c3 = W[v] > W["C0"]
    ad[v] = c1 and c2 and c3
    P(f"{v}: W->C >= 15% {c1} ({pct(v):.1f}%); clearly higher than C0 and C1 {c2}; > C0 (C2) {c3} -> {'MEETS' if ad[v] else 'does not meet'}")
choice = None
if ad["V1"] and ad["V2"]: choice = "V2" if W["V2"] > W["V1"] else "V1"
elif ad["V1"] or ad["V2"]: choice = "V1" if ad["V1"] else "V2"
P(f"ADOPTED: {choice}")
errate = {c: errs[c] / max(1, defined[c]) for c in COND}
P(f"error rates per condition: { {c: round(100*e,1) for c, e in errate.items()} }; any > 5%: {any(e > 0.05 for e in errate.values())}")
json.dump(dict(adopted=choice, W={c: W[c] for c in COND}, p1=p1, p4=[agree, len(both)]), open(D / "summary.json", "w"), indent=1)
