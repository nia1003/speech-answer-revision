"""Rule vs LLM-judge agreement for stage 1 (2026-11-22). Prints parse failures, agreement per model x run,
the disagreement direction (rule✓judge✗ / rule✗judge✓), and optionally dumps disagreements for inspection.
Rule 'undeterminable' counts as not correct.
usage: python3 judge_agreement.py <judge_out.jsonl> <judge_input.jsonl> [dump_disagreements.jsonl]"""
import sys, json, collections
J = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
I = {x["key"]: x for x in map(json.loads, open(sys.argv[2]))}
c = collections.defaultdict(collections.Counter); fails = [j for j in J if j["judge_correct"] is None]
print(f"judged {len(J)}, parse failures {len(fails)}")
for j in J:
    if j["judge_correct"] is None: continue
    r = j["rule_verdict"] == "correct"; g = j["judge_correct"]
    c[(j["model"], j["run"])][("agree" if r == g else ("rule✓judge✗" if r else "rule✗judge✓"))] += 1
print("| model | run | n | agree | rule✓judge✗ | rule✗judge✓ |"); print("|---" * 6 + "|")
tot = collections.Counter()
for k in sorted(c):
    n = sum(c[k].values()); tot.update(c[k])
    print(f"| {k[0]} | {k[1]} | {n} | {c[k]['agree']} | {c[k]['rule✓judge✗']} | {c[k]['rule✗judge✓']} |")
n = sum(tot.values()); print(f"| all | | {n} | {tot['agree']} ({100*tot['agree']/max(n,1):.1f}%) | {tot['rule✓judge✗']} | {tot['rule✗judge✓']} |")
if len(sys.argv) > 3:
    with open(sys.argv[3], "w") as f:
        for j in J:
            if j["judge_correct"] is None or (j["rule_verdict"] == "correct") != j["judge_correct"]:
                x = I[j["key"]]
                f.write(json.dumps(dict(key=j["key"], question=x["question"], answer=x["answer"], aliases=x["aliases"],
                                        response=x["response"], rule=j["rule_verdict"], judge=j["judge_correct"],
                                        judge_final=j["judge_final"], judge_raw=j["judge_raw"]), ensure_ascii=False) + "\n")
