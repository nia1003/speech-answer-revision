"""Stage 2 smoke v2 offline checks (2026-11-23), no model: check 1 (step labels of the 80 items), check 2 (evidence
comparability by depth: words, leakage, mutation type, k/h), check 4 (MSS/CRS denominators per depth cell), and the
mutation type x k cross table. usage: python3 stage2_offline_checks.py <out_dir>"""
import sys, json, re, collections, statistics as st, pathlib
D = pathlib.Path(sys.argv[1]); O = open(D / "offline_checks.txt", "w")
def P(*a): print(*a); print(*a, file=O)
ids = [json.loads(l) for l in open(D / "smoke80_v2_ids.jsonl")]
E = [json.loads(l) for l in open(D / "smoke80_evidence_final.jsonl")]
items = {(x["dataset"], str(x["id"])): x for x in map(json.loads, open("data/full_items.jsonl"))}
gsm = [json.loads(l) for l in open("data/raw/gsm8k_test.jsonl")]
mus = {x["id"]: x for x in map(json.loads, open("data/raw/musique/data/musique_ans_v1.0_dev.jsonl"))}
binof = {(p["dataset"], p["id"]): p["step_bin"] for p in ids}
P("== Check 1: step labels of the 80 items")
bad = 0
for p in ids:
    it = items[(p["dataset"], p["id"])]
    n = len(re.findall(r"<<.*?>>", gsm[int(p["id"])]["answer"])) if p["dataset"] == "gsm8k" else len(mus[p["id"]]["question_decomposition"])
    bad += n != it["total_steps"]
P(f"items {len(ids)}, label mismatches {bad} (GSM8K <<>> count vs total_steps; MuSiQue decomposition length vs hops); no-marker GSM8K items in sample: {sum(items[(p['dataset'], p['id'])].get('no_marker', False) for p in ids)}")
OK = ("approved", "rule_passed", "nli_passed")
P("\n== Check 2: evidence comparability by depth (passed evidence only)")
for ds in ("gsm8k", "musique"):
    bins = ["1-2", "3", "4", "5+"] if ds == "gsm8k" else ["2", "3", "4"]
    P(f"-- {ds}")
    P("| type | bin | n | words median (min-max) | leaks_gold | mutation types | k/h |")
    for et in ("valid_corrective", "invalid"):
        for b in bins:
            rs = [r for r in E if r["dataset"] == ds and r["evidence_type"] == et and r["verification_status"] in OK and binof[(ds, r["item_id"])] == b]
            if not rs: P(f"| {et} | {b} | 0 | - | - | - | - |"); continue
            w = [r["evidence_words"] for r in rs]
            P(f"| {et} | {b} | {len(rs)} | {st.median(w)} ({min(w)}-{max(w)}) | {sum(r['leaks_gold'] for r in rs)} | "
              f"{dict(collections.Counter(r.get('mutation_type') for r in rs)) if et == 'invalid' else '-'} | "
              f"{dict(collections.Counter(str(r['target_hop']) + '/' + str(r['hop_count']) for r in rs))} |")
P("\n== Mutation type x k (Invalid, passed)")
for ds in ("gsm8k", "musique"):
    rs = [r for r in E if r["dataset"] == ds and r["evidence_type"] == "invalid" and r["verification_status"] in OK]
    ks = sorted({r["target_hop"] for r in rs}); ts = sorted({r["mutation_type"] for r in rs})
    P(f"-- {ds}: | type | " + " | ".join(f"k={k}" for k in ks) + " | total |")
    for t in ts: P(f"| {t} | " + " | ".join(str(sum(r['mutation_type'] == t and r['target_hop'] == k for r in rs)) for k in ks) + f" | {sum(r['mutation_type'] == t for r in rs)} |")
P("\n== Check 4: denominators per depth cell")
P("smoke 80 (by design; first round from Qwen, rule & judge agree, text and speech the same):")
c = collections.Counter((p["dataset"], p["step_bin"], p["first_round"]) for p in ids)
for ds, bins in (("gsm8k", ["1-2", "3", "4", "5+"]), ("musique", ["2", "3", "4"])):
    for b in bins:
        ok = [r for r in E if r["dataset"] == ds and binof[(ds, r["item_id"])] == b and r["verification_status"] in OK]
        inv = sum(r["evidence_type"] == "invalid" for r in ok if any(p["id"] == r["item_id"] and p["first_round"] == "both_correct" for p in ids))
        val = sum(r["evidence_type"] == "valid_corrective" for r in ok)
        P(f"| {ds} | {b} | MSS denominator (both correct) {c[(ds, b, 'both_correct')]}, with usable Invalid {inv} | CRS denominator (both wrong) {c[(ds, b, 'both_wrong')]}, with usable Valid {val} |")
P("full population (Qwen, both modalities agree), from resample_population_counts.json:")
P(json.dumps(json.load(open(D / "resample_population_counts.json")), indent=0))
