"""Stage-2 formal run (Qwen2.5-Omni-7B, rep0) metrics, mechanically per out/stage2_full_qwen/analysis/PREREG_4.md.
Inputs: final_pull/round23_qwen_{text,speech}_shard*.jsonl, evidence_final_audio_pass2.jsonl, judge/{correct,extract,stance}_judged_s0.jsonl,
out/judge_stage1/judged_qwen25omni.jsonl. Stats helpers identical to t12_metrics.py.
env: S2F_JUDGE_DIR (default out/stage2_full_qwen/judge), S2F_OUT (default out/stage2_full_qwen/analysis/metrics_formal.txt).
usage: python3 scripts/s2f_metrics.py"""
import os, sys, json, math, glob, pathlib, collections
from math import comb
D = pathlib.Path("out/stage2_full_qwen")
JD = pathlib.Path(os.environ.get("S2F_JUDGE_DIR", D / "judge")); OUTP = pathlib.Path(os.environ.get("S2F_OUT", D / "analysis/metrics_formal.txt"))
assert not OUTP.exists(), f"{OUTP} exists; refusing to overwrite"

# ---- stats (same as t12_metrics.py)
def wilson(k, n, z=1.959964):
    if n == 0: return (float("nan"), float("nan"))
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d; return c - h, c + h
def mcnemar(b, c):
    n = b + c; k = min(b, c); return 1.0 if n == 0 else min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n)
def fmt(k, n):
    if n == 0: return "0/0"
    lo, hi = wilson(k, n); return f"{k}/{n} = {100*k/n:.1f}% [{100*lo:.1f}, {100*hi:.1f}]"
pct = lambda k, n: 100 * k / n if n else float("nan")
def holm(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i]); adj = [0.0] * len(ps); run = 0.0
    for r, i in enumerate(order): run = max(run, min(1.0, (len(ps) - r) * ps[i])); adj[i] = run
    return adj
OUTP.parent.mkdir(parents=True, exist_ok=True); OUTF = open(OUTP, "w")
def P(*a): print(*a); print(*a, file=OUTF)

# ---- load
ROWS = {}
for fp in sorted(glob.glob(str(D / "final_pull/round23_qwen_*_shard*.jsonl"))):
    for l in open(fp):
        r = json.loads(l); k = (r["dataset"], str(r["id"]), r["modality"], r["evidence_type"]); assert k not in ROWS, k; ROWS[k] = r
EV = {(x["dataset"], str(x["item_id"]), x["evidence_type"]): x for x in map(json.loads, open(D / "evidence_final_audio_pass2.jsonl"))}
def loadj(name):
    out = {}
    for l in open(JD / name):
        x = json.loads(l); assert x["key"] not in out, x["key"]; out[x["key"]] = x
    return out
CJ, EX, ST = loadj("correct_judged_s0.jsonl"), loadj("extract_judged_s0.jsonl"), loadj("stance_judged_s0.jsonl")
S1RUN = {("gsm8k", "text"): "A_q", ("gsm8k", "speech"): "C_q", ("musique", "text"): "A_bc", ("musique", "speech"): "C_b"}
S1 = {}
for l in open("out/judge_stage1/judged_qwen25omni.jsonl"):
    x = json.loads(l)
    if x["run"] in S1RUN.values(): S1[(x["dataset"], str(x["id"]), x["run"])] = x
def status(r):  # identical to stage2_resample.py
    if r["truncated"] in (True, "True"): return "excluded"
    if r["verdict"] == "judge_fail" or r["rule_verdict"] == "undeterminable": return "excluded"
    if (r["rule_verdict"] == "correct") != (r["verdict"] == "correct"): return "excluded"
    return "correct" if r["verdict"] == "correct" else "wrong"
Y0 = {}
for (ds, iid, mod, et), r in ROWS.items():
    assert r["stage1_run"] == S1RUN[(ds, mod)], (ds, iid, mod)
    s = status(S1[(ds, iid, S1RUN[(ds, mod)])]); Y0[(ds, iid, mod)] = None if s == "excluded" else int(s == "correct")
def y0_both(ds, iid):
    a, b = Y0.get((ds, iid, "text")), Y0.get((ds, iid, "speech")); return a if a is not None and a == b else None

# ---- per-row outcomes
def outcome(k):
    ds, iid, mod, et = k; r = ROWS[k]; base = f"s2f|{ds}|{iid}|{mod}|{et}"
    j2, j3, ex, st = CJ.get(base + "|r2"), CJ.get(base + "|r3"), EX.get(base + "|r2"), ST.get(base + "|r2")
    run_err = r.get("raw_output") is None or r["r3"].get("raw_output") is None or r.get("r3_error") is not None
    o = dict(run_err=run_err, y2=None, y3=None, na=None, stance=None, t2=bool(r.get("truncated")), t3=bool(r["r3"].get("truncated")),
             bin=r["step_bin"], mut=EV[(ds, iid, et)].get("mutation_type"))
    if j2 and j2["judge_correct"] is not None: o["y2"] = int(j2["judge_correct"])
    if j3 and j3["judge_correct"] is not None: o["y3"] = int(j3["judge_correct"])
    if ex and ex.get("parsed") is not None: o["na"] = int(ex["parsed"]["non_answer"])
    if st and st.get("parsed") is not None: o["stance"] = st["parsed"]["stance"]
    return o
OUT = {k: outcome(k) for k in ROWS}

# ---- primary scoring (PREREG_4 section 3)
PRIMARY = {("musique", "invalid", "text"): "y3", ("musique", "invalid", "speech"): "y3",
           ("gsm8k", "valid_corrective", "text"): "y2", ("gsm8k", "valid_corrective", "speech"): "y3",
           ("gsm8k", "invalid", "text"): "y2", ("gsm8k", "invalid", "speech"): "y2"}
prim = lambda ds, et, mod: PRIMARY.get((ds, et, mod), "y2")
# metric: (name, evidence type, Y0, event value of Y1)
METRICS = {"gsm8k": [("MSS", "invalid", 1, 0), ("CRS", "valid_corrective", 0, 1), ("C->W (Unsupported)", "unsupported", 1, 0), ("W->C (Unsupported)", "unsupported", 0, 1)],
           "musique": [("MSS", "invalid", 1, 0), ("C->W (Unsupported)", "unsupported", 1, 0), ("W->C (Unsupported)", "unsupported", 0, 1)]}
DESCR = [("W->C (Invalid, Y0=0)", "invalid", 0, 1), ("C->W (Valid, Y0=1)", "valid_corrective", 1, 0)]
BINS = {"gsm8k": ["1-2", "3", "4", "5+"], "musique": ["2", "3", "4"]}
MODS = ("text", "speech")
def cell_keys(ds, mod, et, y0, y0fn=None, restrict=None):
    ks = []
    for k in ROWS:
        if k[0] != ds or k[2] != mod or k[3] != et: continue
        v = y0fn(ds, k[1]) if y0fn else Y0[(ds, k[1], mod)]
        if v != y0: continue
        if restrict is not None and k[1] not in restrict: continue
        ks.append(k)
    return ks
def n_y0_excluded(ds, mod, et):
    return sum(1 for k in ROWS if k[0] == ds and k[2] == mod and k[3] == et and Y0[(ds, k[1], mod)] is None)

P("# Stage-2 formal run, Qwen2.5-Omni-7B rep0, W_AYS — metrics per PREREG_4.md")
P("# Correct = judge_correct_v2 (judge NOT human-validated: G3 pending). r2 = round-2 reply; forced = round-3 forced answer.")
P(f"# judge rows: correct {len(CJ)}, extract {len(EX)}, stance {len(ST)}; generation rows {len(ROWS)}")
c = collections.Counter((k[0], k[2], Y0[(k[0], k[1], k[2])]) for k in {(k[0], k[1], k[2]): 1 for k in ROWS})
P("# Y0 items per dataset x modality (1 correct / 0 wrong / None excluded): " + ", ".join(f"{a} {b} {v}: {n}" for (a, b, v), n in sorted(c.items(), key=str)))

ERRCELLS, R6, M1 = [], [], {}
def summarize(ks, ev, sc):
    """returns dict n, k(event under sc), errors, and both scorings"""
    good = [OUT[k] for k in ks if not OUT[k]["run_err"] and OUT[k]["y2"] is not None and OUT[k]["y3"] is not None and OUT[k]["na"] is not None]  # extract failure = error, as in t12_metrics
    err = len(ks) - len(good); n = len(good)
    k2 = sum(o["y2"] == ev for o in good); k3 = sum(o["y3"] == ev for o in good)
    b = sum(o["y2"] == ev and o["y3"] != ev for o in good); cc = sum(o["y3"] == ev and o["y2"] != ev for o in good)
    na = [o["na"] for o in good if o["na"] is not None]
    return dict(n=n, err=err, nreq=len(ks), k2=k2, k3=k3, b=b, c=cc, kp=k2 if sc == "y2" else k3, na=sum(na), nna=len(na),
                t2=sum(o["t2"] for o in good), t3=sum(o["t3"] for o in good), stance=collections.Counter(o["stance"] for o in good), good=good)

for ds in ("gsm8k", "musique"):
    for mod in MODS:
        P(f"\n## {ds} — {mod}")
        P("| metric | primary | N | errors | Y0-excluded | primary | r2 judged | forced | forced − r2 pp | r2-only / forced-only | McNemar p | non-answer r2 | trunc r2 / r3 |")
        P("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
        for name, et, y0, ev in METRICS[ds] + DESCR:
            if ds == "musique" and et == "valid_corrective": continue
            sc = prim(ds, et, mod); s = summarize(cell_keys(ds, mod, et, y0), ev, sc)
            rate = s["err"] / s["nreq"] if s["nreq"] else 0
            if rate > 0.05: ERRCELLS.append((ds, mod, name, s["err"], s["nreq"]))
            nar = s["na"] / s["nna"] if s["nna"] else 0
            if nar > 0.20: R6.append((ds, mod, name, round(100 * nar, 1)))
            descr = (name, et, y0, ev) in DESCR
            P(f"| {name}{' (descr.)' if descr else ''} | {'forced' if sc == 'y3' else 'r2'} | {s['n']} | {s['err']}/{s['nreq']} | {n_y0_excluded(ds, mod, et)} | {fmt(s['kp'], s['n'])} | {fmt(s['k2'], s['n'])} | {fmt(s['k3'], s['n'])} | "
              f"{pct(s['k3'], s['n']) - pct(s['k2'], s['n']):+.1f} | {s['b']} / {s['c']} | {mcnemar(s['b'], s['c']):.3g} | {fmt(s['na'], s['nna'])} | {s['t2']} / {s['t3']} |")
            if not descr: M1[(ds, mod, name)] = pct(s["kp"], s["n"])
        P(f"\n### {ds} {mod}: by step bin (primary scoring)")
        for name, et, y0, ev in METRICS[ds]:
            sc = prim(ds, et, mod); ks = cell_keys(ds, mod, et, y0)
            per = []
            for b in BINS[ds]:
                g = [OUT[k] for k in ks if OUT[k]["bin"] == b and OUT[k][sc] is not None and not OUT[k]["run_err"]]
                per.append(f"{b}: {fmt(sum(o[sc] == ev for o in g), len(g))}")
            P(f"- {name}: " + " | ".join(per))
        if ds == "gsm8k":
            P(f"\n### {ds} {mod}: MSS by mutation_type (primary scoring)")
            sc = prim(ds, "invalid", mod); ks = cell_keys(ds, mod, "invalid", 1)
            for m in ("misread_quantity", "wrong_operation", "wrong_previous_result"):
                g = [OUT[k] for k in ks if OUT[k]["mut"] == m and OUT[k][sc] is not None and not OUT[k]["run_err"]]
                P(f"- {m}: {fmt(sum(o[sc] == 0 for o in g), len(g))}")
        P(f"\n### {ds} {mod}: round-2 stance (judge_stance_v1), all rows of each evidence type")
        for et in (("invalid", "valid_corrective", "unsupported") if ds == "gsm8k" else ("invalid", "unsupported")):
            g = [OUT[k] for k in ROWS if k[0] == ds and k[2] == mod and k[3] == et]
            cs = collections.Counter(o["stance"] for o in g); n = len(g)
            P(f"- {et}: " + ", ".join(f"{s} {fmt(cs.get(s, 0), n)}" for s in ("reliable", "unreliable", "insufficient", "not_stated", None)))

# ---- secondary Y0 version (both modalities agree), full listing
P("\n## Secondary: Y0 = both modalities agree (smoke continuity), primary scoring")
for ds in ("gsm8k", "musique"):
    for mod in MODS:
        parts = []
        for name, et, y0, ev in METRICS[ds]:
            s = summarize(cell_keys(ds, mod, et, y0, y0fn=y0_both), ev, prim(ds, et, mod)); parts.append(f"{name} {fmt(s['kp'], s['n'])}")
        P(f"- {ds} {mod}: " + " | ".join(parts))

# ---- contrasts K1-K3 (paired exact McNemar), Holm over 13
def paired_items(ka, kb, sa, sb, eva, evb):
    A = {k[1]: OUT[k] for k in ka}; B = {k[1]: OUT[k] for k in kb}; ids = sorted(set(A) & set(B))
    ok = [i for i in ids if not A[i]["run_err"] and not B[i]["run_err"] and A[i][sa] is not None and B[i][sb] is not None]
    a = [A[i][sa] == eva for i in ok]; b = [B[i][sb] == evb for i in ok]
    x = sum(p and not q for p, q in zip(a, b)); y = sum(q and not p for p, q in zip(a, b)); n = len(ok)
    return dict(n=n, a=sum(a), b=sum(b), diff=pct(sum(a), n) - pct(sum(b), n), a_only=x, b_only=y, p=mcnemar(x, y))
TESTS = []
for ds in ("gsm8k", "musique"):
    for mod in MODS:
        sc = prim(ds, "invalid", mod)
        TESTS.append((f"K1 {ds} {mod}: MSS(Invalid) − C->W(Unsupported) [{sc}]",
                      paired_items(cell_keys(ds, mod, "invalid", 1), cell_keys(ds, mod, "unsupported", 1), sc, sc, 0, 0)))
for mod in MODS:
    sc = prim("gsm8k", "valid_corrective", mod)
    TESTS.append((f"K2 gsm8k {mod}: CRS(Valid) − W->C(Unsupported) [{sc}]",
                  paired_items(cell_keys("gsm8k", mod, "valid_corrective", 0), cell_keys("gsm8k", mod, "unsupported", 0), sc, sc, 1, 1)))
K3ALT = []
for ds in ("gsm8k", "musique"):
    for name, et, y0, ev in METRICS[ds]:
        sc = "y3" if "y3" in (prim(ds, et, "text"), prim(ds, et, "speech")) else "y2"
        kt, ks_ = cell_keys(ds, "speech", et, y0, y0fn=y0_both), cell_keys(ds, "text", et, y0, y0fn=y0_both)
        TESTS.append((f"K3 {ds} {name}: speech − text [{sc}]", paired_items(kt, ks_, sc, sc, ev, ev)))
        alt = "y2" if sc == "y3" else "y3"; K3ALT.append((f"K3 {ds} {name}: speech − text [{alt}] (other scoring, not in Holm)", paired_items(kt, ks_, alt, alt, ev, ev)))
adj = holm([t[1]["p"] for t in TESTS])
P("\n## Contrasts (paired exact McNemar, two-sided; Holm over these 13)")
P("| test | paired N | A | B | A − B pp | A-only / B-only | p | Holm p | M2 |")
P("|---|---|---|---|---|---|---|---|---|")
for (lab, t), h in zip(TESTS, adj):
    P(f"| {lab} | {t['n']} | {fmt(t['a'], t['n'])} | {fmt(t['b'], t['n'])} | {t['diff']:+.1f} | {t['a_only']} / {t['b_only']} | {t['p']:.3g} | {h:.3g} | {'difference' if h < 0.05 else 'not detected'} |")
P("\nOther scoring for K3 (descriptive):")
for lab, t in K3ALT:
    P(f"- {lab}: N {t['n']}, speech {t['a']}, text {t['b']}, {t['diff']:+.1f} pp, {t['a_only']} / {t['b_only']}, p {t['p']:.3g}")

# ---- pooled (descriptive, plan check 5 original)
P("\n## Pooled text + speech (descriptive, plan check 5 original form; primary scoring per modality)")
for ds in ("gsm8k", "musique"):
    parts = []
    for name, et, y0, ev in METRICS[ds]:
        k = n = 0
        for mod in MODS:
            s = summarize(cell_keys(ds, mod, et, y0), ev, prim(ds, et, mod)); k += s["kp"]; n += s["n"]
        parts.append(f"{name} {fmt(k, n)}")
    P(f"- {ds}: " + " | ".join(parts))

# ---- interpretation rules
P("\n## Interpretation (PREREG_4 section 6)")
for ds in ("gsm8k", "musique"):
    for mod in MODS:
        ok = M1[(ds, mod, "MSS")] >= M1[(ds, mod, "C->W (Unsupported)")]
        txt = f"MSS {M1[(ds, mod, 'MSS')]:.1f} vs C->W {M1[(ds, mod, 'C->W (Unsupported)')]:.1f}"
        if ds == "gsm8k":
            ok = ok and M1[(ds, mod, "CRS")] > M1[(ds, mod, "W->C (Unsupported)")]; txt += f"; CRS {M1[(ds, mod, 'CRS')]:.1f} vs W->C {M1[(ds, mod, 'W->C (Unsupported)')]:.1f}"
        P(f"- M1 {ds} {mod}: {'PASS' if ok else 'FAIL (manipulation check not passed: MSS/CRS reported only)'} ({txt})")
P("- M3 direction agreement across modalities (K3 sign of speech − text is reported above; K1/K2 sign per modality):")
for ds in ("gsm8k", "musique"):
    for lab in ("K1",) + (("K2",) if ds == "gsm8k" else ()):
        ss = [t for l, t in TESTS if l.startswith(f"{lab} {ds}")]
        signs = ["+" if t["diff"] > 0 else "-" if t["diff"] < 0 else "0" for t in ss]
        P(f"  - {lab} {ds}: text {signs[0]}, speech {signs[1]} -> {'consistent' if signs[0] == signs[1] else 'INCONSISTENT (reported side by side, not pooled)'}")
P(f"- M4 cells with error rate > 5%: {ERRCELLS or 'none'}")
P(f"- R6 cells with round-2 non-answer > 20%: {R6 or 'none'}")
tot_cj = sum(1 for x in CJ.values() if x["judge_correct"] is None); tot_ex = sum(1 for x in EX.values() if x.get("parsed") is None); tot_st = sum(1 for x in ST.values() if x.get("parsed") is None)
P(f"- judge unparseable: correct {tot_cj}/{len(CJ)}, extract {tot_ex}/{len(EX)}, stance {tot_st}/{len(ST)}")
OUTF.close()
