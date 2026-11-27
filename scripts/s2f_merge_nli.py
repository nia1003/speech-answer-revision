"""Formal run (2026-11-25): merge NLI into MuSiQue Invalid rows, same rule as smoke v3 (smoke80_evidence_final_auto):
rule_passed + NLI forward argmax CONTRADICTION -> nli_passed; otherwise rejected, reason ['nli_not_contradiction'].
No manual reading (GO_CRITERIA v1). usage: python3 s2f_merge_nli.py <evidence_verified.jsonl> <nli.jsonl> <out.jsonl>"""
import sys, json, os, collections
assert not os.path.exists(sys.argv[3]), "output exists"
N = {}
for l in open(sys.argv[2]): r = json.loads(l); assert r["item_id"] not in N; N[r["item_id"]] = r
rows = [json.loads(l) for l in open(sys.argv[1])]; c = collections.Counter(); miss = 0
for r in rows:
    if r["dataset"] == "musique" and r["evidence_type"] == "invalid" and r["verification_status"] == "rule_passed":
        n = N.get(r["item_id"])
        if n is None: miss += 1; continue
        r["nli_check"] = dict(model=n["nli_model"], revision=n["nli_revision"], forward=n["forward"], backward=n["backward"], passed=n["nli_pass"])
        if n["nli_pass"]: r["verification_status"] = "nli_passed"
        else: r["verification_status"] = "rejected"; r["reason"] = ["nli_not_contradiction"]
        c[r["verification_status"]] += 1
assert miss == 0, f"{miss} rule_passed rows without NLI"
with open(sys.argv[3], "w") as f:
    for r in rows: f.write(json.dumps(r, ensure_ascii=False) + "\n")
print("MERGED", dict(c), collections.Counter((r["dataset"], r["evidence_type"], r["verification_status"]) for r in rows))
