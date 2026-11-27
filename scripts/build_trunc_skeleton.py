"""Supplementary analysis (user 2026-11-21): MuSiQue truncated linear chains -- same chain, different number of hops.
Builds the skeleton only (no rewriting): for every linear chain (2hop/3hop1/4hop1; each step k>1 references only #(k-1)),
the k-step prefixes for k = 2..n. Each record: sub-questions 1..k (raw, with #j references), target answer = answer of
sub-question k, supporting paragraphs = the paragraphs of steps 1..k (in step order), and the original full question for
k = n. Non-linear chains (3hop2/4hop2/4hop3) are skipped.
usage: python3 build_trunc_skeleton.py <musique_dev.jsonl> <out.jsonl>"""
import sys, json, re
out = open(sys.argv[2], "w"); n = {}
for d in map(json.loads, open(sys.argv[1])):
    t = d["id"].split("__")[0]; sq = d["question_decomposition"]
    if t not in ("3hop1", "4hop1"): continue                     # 2hop prefixes = the item itself (no truncation)
    assert all(re.findall(r"#(\d)", s["question"]) == [str(k)] for k, s in enumerate(sq[1:], 1))
    for k in range(2, len(sq) + 1):
        steps = sq[:k]
        rec = dict(chain_id=d["id"], chain_type=t, n_full=len(sq), k=k, is_full=k == len(sq),
                   original_question=d["question"] if k == len(sq) else None,
                   sub_questions=[s["question"] for s in steps], sub_answers=[s["answer"] for s in steps],
                   kb_style=[">>" in s["question"] for s in steps],
                   answer=steps[-1]["answer"], answer_aliases=d["answer_aliases"] if k == len(sq) else [],
                   paragraphs=[{"title": d["paragraphs"][s["paragraph_support_idx"]]["title"],
                                "text": d["paragraphs"][s["paragraph_support_idx"]]["paragraph_text"]} for s in steps])
        out.write(json.dumps(rec, ensure_ascii=False) + "\n"); n[(t, k)] = n.get((t, k), 0) + 1
print(sorted(n.items()), "new (non-full):", sum(v for (t, k), v in n.items() if not (t == "3hop1" and k == 3 or t == "4hop1" and k == 4)))
