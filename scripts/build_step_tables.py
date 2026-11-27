"""Plan 2026-11-20 (step axis): per-item step fields, length quartile cutpoints, step x length-quartile counts,
and the 80-item smoke sample. No model is called.
- GSM8K total steps = number of <<>> markers (parser_original.py), no exclusions; 18 items without markers excluded.
- parallel steps = total steps - longest chain (GSM8K: parser_original depth; MuSiQue: #k reference chain).
- length = characters of the question text. Quartile cutpoints per dataset, over the main-analysis items,
  numpy-style linear interpolation (statistics.quantiles method="inclusive").
- Sampling: random.Random(20261120) per dataset; strata in the listed order; candidates sorted by id; rng.sample.
usage: python3 build_step_tables.py <rq4_v2 dir>"""
import sys, json, re, random, statistics as st, pathlib, csv
from collections import Counter
B = pathlib.Path(sys.argv[1]); sys.path.insert(0, str(B / "data/reference"))
import parser_original as P
OUT = B / "out/step_axis"; OUT.mkdir(parents=True, exist_ok=True)
SEED = 20261120

# GSM8K
g = []
for i, l in enumerate(open(B / "data/raw/gsm8k_test.jsonl")):
    r = json.loads(l); steps, deps, depth, amb = P.parse(r)
    g.append(dict(dataset="gsm8k", id=i, total_steps=len(steps), longest_chain=depth,
                  parallel_steps=len(steps) - depth, question_chars=len(r["question"]), no_marker=len(steps) == 0))
# MuSiQue
m = []
for l in open(B / "data/raw/musique/data/musique_ans_v1.0_dev.jsonl"):
    r = json.loads(l); d = r["question_decomposition"]; D = []
    for k, s in enumerate(d):
        refs = [int(x) for x in re.findall(r"#(\d+)", s["question"])]
        D.append(1 + max([D[x - 1] for x in refs], default=0))
    m.append(dict(dataset="musique", id=r["id"], subtype=r["id"].split("__")[0], total_steps=len(d),
                  longest_chain=max(D), parallel_steps=len(d) - max(D), question_chars=len(r["question"])))

def quart(rows):
    q = st.quantiles([x["question_chars"] for x in rows], n=4, method="inclusive"); return [round(v, 2) for v in q]
def qbin(c, q): return 1 + sum(c > v for v in q)          # Q1: <=q1, Q2: (q1,q2], Q3: (q2,q3], Q4: >q3

gm = [x for x in g if not x["no_marker"]]
cut = {"gsm8k_main_1301": quart(gm), "gsm8k_all_1319": quart(g), "musique_2417": quart(m)}
for x in gm: x["len_q"] = qbin(x["question_chars"], cut["gsm8k_main_1301"])
for x in m: x["len_q"] = qbin(x["question_chars"], cut["musique_2417"])
json.dump(cut, open(OUT / "length_quartile_cutpoints.json", "w"), indent=1)
with open(OUT / "item_steps.jsonl", "w") as f:
    for x in g + m: f.write(json.dumps(x, ensure_ascii=False) + "\n")

def table(rows, name):
    keys = sorted(set(x["total_steps"] for x in rows))
    with open(OUT / f"{name}_steps_x_lenq.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["total_steps", "Q1", "Q2", "Q3", "Q4", "total"])
        for k in keys:
            c = Counter(x["len_q"] for x in rows if x["total_steps"] == k)
            w.writerow([k] + [c[q] for q in (1, 2, 3, 4)] + [sum(c.values())])
    print(open(OUT / f"{name}_steps_x_lenq.csv").read())
table(gm, "gsm8k"); table(m, "musique")

# 80-item smoke sample
rng = random.Random(SEED); smoke = []
for lab, cond, k in [("hop2", lambda x: x["total_steps"] == 2, 14), ("hop3", lambda x: x["total_steps"] == 3, 13),
                     ("hop4", lambda x: x["total_steps"] == 4, 13)]:
    ids = sorted(x["id"] for x in m if cond(x))
    for i in rng.sample(ids, k): smoke.append(dict(dataset="musique", stratum=lab, id=i))
rng = random.Random(SEED)
for lab, cond in [("<=2", lambda x: x["total_steps"] <= 2), ("3", lambda x: x["total_steps"] == 3),
                  ("4", lambda x: x["total_steps"] == 4), (">=5", lambda x: x["total_steps"] >= 5)]:
    ids = sorted(x["id"] for x in gm if cond(x))
    for i in rng.sample(ids, 10): smoke.append(dict(dataset="gsm8k", stratum=lab, id=i))
with open(OUT / "smoke80_ids.jsonl", "w") as f:
    for s in smoke: f.write(json.dumps(s, ensure_ascii=False) + "\n")
info = {x["id"]: x for x in g + m}
print("cutpoints", cut)
print("MuSiQue 子類型抽到", dict(Counter(info[s["id"]]["subtype"] for s in smoke if s["dataset"] == "musique")))
print("GSM8K 各層步數", {lab: dict(Counter(info[s["id"]]["total_steps"] for s in smoke if s["dataset"] == "gsm8k" and s["stratum"] == lab)) for lab in ("<=2", "3", "4", ">=5")})
print("smoke 長度四分位", {d: dict(Counter(info[s["id"]]["len_q"] for s in smoke if s["dataset"] == d)) for d in ("musique", "gsm8k")})
old = [json.loads(l)["idx"] for l in open(B / "data/gsm8k_depth_smoke_40.jsonl")]
print("與舊 GSM8K 40 題重疊", len(set(old) & {s["id"] for s in smoke if s["dataset"] == "gsm8k"}))
