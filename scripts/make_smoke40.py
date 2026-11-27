"""H1 check 1 / CP1: build gsm8k_depth_smoke_40.jsonl from the fixed idx list in the frozen plan (2026-11-20).
Only idx, question, solution (answer before ####, stripped). No depth or labels of any kind.
usage: python3 make_smoke40.py <gsm8k_test.jsonl> <out.jsonl>"""
import sys, json

BUCKETS = {
    "淺": [800, 1061, 990, 740, 635, 488, 302, 995, 222, 1020, 288, 268, 708, 493],
    "中": [1256, 711, 554, 1140, 505, 306, 1078, 1261, 1017, 588, 178, 97, 240],
    "深": [844, 1211, 975, 936, 735, 606, 1230, 596, 601, 25, 994, 1052, 430],
}
src, out = sys.argv[1], sys.argv[2]
rows = [json.loads(l) for l in open(src)]
assert len(rows) == 1319, len(rows)
ids = [i for b in BUCKETS.values() for i in b]
assert len(ids) == 40 and len(set(ids)) == 40
with open(out, "w") as f:
    for i in ids:
        r = rows[i]
        assert "####" in r["answer"], i
        f.write(json.dumps({"idx": i, "question": r["question"],
                            "solution": r["answer"].split("####")[0].strip()}, ensure_ascii=False) + "\n")
print("wrote", len(ids), "rows to", out)
