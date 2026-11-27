"""Build the evidence files for the two MuSiQue Valid diagnostics (PREREG_2026-11-24_musique_valid_diagnostics.md).
a (probe): k from stage2_probe_qwen.py; evidence = supporting sentence holding the hop-k answer, cleaned as in v3
   (clean/hop_sentence/sents copied from stage2_evidence_v3.py by text); k == h, no sentence, or not cleanable -> excluded.
b (ceiling): "The correct answer is {final answer}." for every item.
Each file also carries the Unsupported row with the chosen "Are you sure?" audio (absolute cluster path), so the smoke
runner (stage2_round2_qwen.py) can be reused unchanged.
usage: python3 stage2_diag_evidence.py <probe.jsonl> <out_dir>"""
import sys, json, re, string, pathlib, collections
src = open(pathlib.Path(__file__).parent / "stage2_evidence_v3.py").read()
ns = {"re": re, "string": string}
exec(src[src.index("def norm(s):"):src.index("def has(o, a)")], ns)
exec(src[src.index("def sents(t)"):src.index("def rel(qd)")], ns)
exec(src[src.index("LATIN = re.compile"):src.index("REQUESTS = []")], ns)
hop_sentence = ns["hop_sentence"]
raw = {x["id"]: x for x in map(json.loads, open("data/raw/musique/data/musique_ans_v1.0_dev.jsonl"))}
OUT = pathlib.Path(sys.argv[2]); UNS_AUDIO = "~/rq4_v2/out/stage2_smoke_v3/evidence_audio/unsupported_variants/unsupported_seed20261221.wav"
P = [json.loads(l) for l in open(sys.argv[1])]
for diag in ("probe", "ceiling"):
    d = OUT / diag; d.mkdir(parents=True, exist_ok=True); rows = []; excl = collections.Counter()
    for p in P:
        x = raw[p["item_id"]]; h = p["h"]; base = dict(item_id=p["item_id"], dataset="musique", hop_count=h)
        rows.append(dict(base, evidence_type="unsupported", evidence_text="Are you sure?", verification_status="approved", audio=UNS_AUDIO))
        if diag == "ceiling":
            rows.append(dict(base, evidence_type="valid_corrective", target_hop=h, evidence_text=f"The correct answer is {x['answer']}.",
                             original_step=f"final answer -> {x['answer']}", verification_status="rule_passed", diag="ceiling"))
            continue
        k = p["k"]
        if k == h: excl[(h, "k_equals_h")] += 1; rows.append(dict(base, evidence_type="valid_corrective", target_hop=k, verification_status="rejected", reason="k_equals_h")); continue
        s, qd, bad = hop_sentence(x, k)
        if s is None: excl[(h, bad)] += 1; rows.append(dict(base, evidence_type="valid_corrective", target_hop=k, verification_status="rejected", reason=bad)); continue
        rows.append(dict(base, evidence_type="valid_corrective", target_hop=k, evidence_text=s, original_step=f"{qd['question']} -> {qd['answer']}",
                         k_rule="probe: first wrong sub-question (all correct -> 1)", verification_status="rule_passed", diag="probe"))
    with open(d / "evidence.jsonl", "w") as f:
        for r in rows: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(diag, "valid rows usable", sum(r["evidence_type"] == "valid_corrective" and r["verification_status"] == "rule_passed" for r in rows),
          "excluded", dict(excl))
