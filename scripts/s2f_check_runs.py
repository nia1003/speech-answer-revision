"""Formal run: check round23 outputs against the evidence files. Exit 1 on: missing/extra rows, duplicates, r3 errors or
missing r3, round-2 truncation > 5%. usage: python3 s2f_check_runs.py <text|speech> <shard files...>"""
import sys, json, collections
mod = sys.argv[1]; ev = "evidence_final_pass2.jsonl" if mod == "text" else "evidence_final_audio_pass2.jsonl"
OK = ("approved", "rule_passed", "nli_passed")
exp = set()
for e in map(json.loads, open(f"out/stage2_full_qwen/{ev}")):
    if e["evidence_type"] == "unsupported" or (e["verification_status"] in OK and not (e["dataset"] == "musique" and e["evidence_type"] == "valid_corrective")):
        exp.add((e["dataset"], e["item_id"], e["evidence_type"]))
R = [json.loads(l) for fp in sys.argv[2:] for l in open(fp)]
got = collections.Counter((r["dataset"], r["id"], r["evidence_type"]) for r in R)
dup = sum(v > 1 for v in got.values()); miss = exp - set(got); extra = set(got) - exp
bad3 = sum(bool(r.get("r3_error")) or not r.get("r3") or r["r3"].get("raw_output") is None for r in R)
wrongmod = sum(r["modality"] != mod for r in R); tr = sum(r["truncated"] in (True, "True") for r in R)
print(mod, "rows", len(R), "expected", len(exp), "missing", len(miss), "extra", len(extra), "dups", dup, "r3 bad", bad3,
      "wrong modality", wrongmod, "r2 trunc", tr, collections.Counter((r["dataset"], r["evidence_type"]) for r in R))
sys.exit(1 if miss or extra or dup or bad3 or wrongmod or tr > 0.05 * len(R) else 0)
