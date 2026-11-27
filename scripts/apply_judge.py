"""Write judge-scored copies of the stage-1 scored files (2026-11-22). Same records as the rule-scored file, plus
rule_verdict (old verdict) and judge fields; verdict = judge (correct / incorrect / judge_fail when the judge output
could not be parsed; judge_fail counts as not correct). Rule-scored files are not modified.
usage: python3 apply_judge.py <judge_full_v2.jsonl> <model_name> <out.jsonl> <scored1.jsonl> [scored2.jsonl]"""
import sys, json
J = {x["key"]: x for x in map(json.loads, open(sys.argv[1]))}
name, out = sys.argv[2], open(sys.argv[3], "w"); n = 0
for fp in sys.argv[4:]:
    for l in open(fp):
        r = json.loads(l); j = J[f"{name}|{r['dataset']}|{r['id']}|{r['run']}"]
        r["rule_verdict"] = r["verdict"]
        r["verdict"] = "judge_fail" if j["judge_correct"] is None else ("correct" if j["judge_correct"] else "incorrect")
        r["judge_final"] = j["judge_final"]; r["judge"] = j["judge"]; r["judge_prompt"] = "v2"
        out.write(json.dumps(r, ensure_ascii=False) + "\n"); n += 1
print(name, n)
