"""Build the LLM-judge input for stage 1 (2026-11-22, user decision: rescore all five models with one LLM judge).
One line per model output: key, model, dataset, id, run, question, reference answer (+ MuSiQue aliases), response,
truncated, rule verdict (for agreement only; the judge never sees it).
usage: python3 build_judge_input.py <full_items.jsonl> <out.jsonl> name=scored1[,scored2] ..."""
import sys, json
items = {(x["dataset"], str(x["id"])): x for x in map(json.loads, open(sys.argv[1]))}
out = open(sys.argv[2], "w"); n = 0
for arg in sys.argv[3:]:
    name, files = arg.split("=", 1)
    for fp in files.split(","):
        for l in open(fp):
            r = json.loads(l); it = items[(r["dataset"], str(r["id"]))]
            rec = dict(key=f"{name}|{r['dataset']}|{r['id']}|{r['run']}", model=name, dataset=r["dataset"], id=str(r["id"]),
                       run=r["run"], question=it["question"], answer=str(it["answer"]),
                       aliases=list(it.get("answer_aliases") or []), response=r["raw_output"],
                       truncated=r["truncated"] in (True, "True", "true"), rule_verdict=r["verdict"])
            out.write(json.dumps(rec, ensure_ascii=False) + "\n"); n += 1
print("wrote", n)
