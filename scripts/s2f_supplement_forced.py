"""NOT pre-registered supplement to PREREG_4 (written 2026-11-27, after seeing metrics_formal.txt).
Recomputes M1 / K1 / K2 / K3 with the forced final answer (round 3) on BOTH sides, plus a table of
r2 vs forced and round-2 non-answer rate for every evidence type x Y0 x modality.
Reuses the locked scripts/s2f_metrics.py unchanged (run via runpy into a scratch output) for loading and Y0.
usage: python3 scripts/s2f_supplement_forced.py <scratch_dir>"""
import os, sys, runpy, pathlib, io, contextlib
OUT = pathlib.Path("out/stage2_full_qwen/analysis/supplement_forced_nonprereg.txt"); assert not OUT.exists(), OUT
os.environ["S2F_OUT"] = str(pathlib.Path(sys.argv[1]) / "metrics_rerun_for_supplement.txt")
with contextlib.redirect_stdout(io.StringIO()):
    G = runpy.run_path("scripts/s2f_metrics.py")
cell_keys, OUTR, fmt, pct, mcnemar, holm, paired_items, y0_both = (G[k] for k in ("cell_keys", "OUT", "fmt", "pct", "mcnemar", "holm", "paired_items", "y0_both"))
METRICS = G["METRICS"]; MODS = ("text", "speech")
f = open(OUT, "w")
def P(*a): print(*a); print(*a, file=f)
P("# NOT PRE-REGISTERED supplement (after seeing results). Forced final answer (r3) on both sides. Judge not human-validated.")
P("\n## A. All cells: r2 vs forced, round-2 non-answer (judge_extract_v1)")
P("| dataset | modality | evidence | Y0 | event | N | r2 judged | forced | non-answer r2 | event among non-answers (r2) |")
P("|---|---|---|---|---|---|---|---|---|---|")
CELLS = [("invalid", 1, 0, "MSS"), ("invalid", 0, 1, "W->C"), ("valid_corrective", 0, 1, "CRS"), ("valid_corrective", 1, 0, "C->W"), ("unsupported", 1, 0, "C->W"), ("unsupported", 0, 1, "W->C")]
for ds in ("gsm8k", "musique"):
    for mod in MODS:
        for et, y0, ev, name in CELLS:
            if ds == "musique" and et == "valid_corrective": continue
            g = [OUTR[k] for k in cell_keys(ds, mod, et, y0) if not OUTR[k]["run_err"] and None not in (OUTR[k]["y2"], OUTR[k]["y3"], OUTR[k]["na"])]
            n = len(g); na = [o for o in g if o["na"]]
            P(f"| {ds} | {mod} | {et} | {y0} | {name} | {n} | {fmt(sum(o['y2'] == ev for o in g), n)} | {fmt(sum(o['y3'] == ev for o in g), n)} | {fmt(len(na), n)} | {sum(o['y2'] == ev for o in na)}/{len(na)} |")
P("\n## B. M1 with forced answer on both sides (point estimates, same rule as PREREG_4 M1)")
for ds in ("gsm8k", "musique"):
    for mod in MODS:
        def rate(et, y0, ev):
            g = [OUTR[k] for k in cell_keys(ds, mod, et, y0) if not OUTR[k]["run_err"] and None not in (OUTR[k]["y2"], OUTR[k]["y3"], OUTR[k]["na"])]
            return pct(sum(o["y3"] == ev for o in g), len(g))
        mss, cw = rate("invalid", 1, 0), rate("unsupported", 1, 0); ok = mss >= cw; txt = f"MSS {mss:.1f} vs C->W {cw:.1f}"
        if ds == "gsm8k":
            crs, wc = rate("valid_corrective", 0, 1), rate("unsupported", 0, 1); ok = ok and crs > wc; txt += f"; CRS {crs:.1f} vs W->C {wc:.1f}"
        P(f"- M1' {ds} {mod}: {'pass' if ok else 'fail'} ({txt})")
P("\n## C. K1 / K2 / K3 with forced answer on both sides (paired exact McNemar; Holm over these 13, separate family from the pre-registered one)")
T = []
for ds in ("gsm8k", "musique"):
    for mod in MODS:
        T.append((f"K1' {ds} {mod}: MSS − C->W", paired_items(cell_keys(ds, mod, "invalid", 1), cell_keys(ds, mod, "unsupported", 1), "y3", "y3", 0, 0)))
for mod in MODS:
    T.append((f"K2' gsm8k {mod}: CRS − W->C", paired_items(cell_keys("gsm8k", mod, "valid_corrective", 0), cell_keys("gsm8k", mod, "unsupported", 0), "y3", "y3", 1, 1)))
for ds in ("gsm8k", "musique"):
    for name, et, y0, ev in METRICS[ds]:
        T.append((f"K3' {ds} {name}: speech − text", paired_items(cell_keys(ds, "speech", et, y0, y0fn=y0_both), cell_keys(ds, "text", et, y0, y0fn=y0_both), "y3", "y3", ev, ev)))
adj = holm([t["p"] for _, t in T])
P("| test | paired N | A | B | A − B pp | A-only / B-only | p | Holm p |")
P("|---|---|---|---|---|---|---|---|")
for (lab, t), h in zip(T, adj):
    P(f"| {lab} | {t['n']} | {fmt(t['a'], t['n'])} | {fmt(t['b'], t['n'])} | {t['diff']:+.1f} | {t['a_only']} / {t['b_only']} | {t['p']:.3g} | {h:.3g} |")
f.close()
