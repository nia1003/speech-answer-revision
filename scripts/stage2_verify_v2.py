"""Stage 2 smoke: rule verification of the generated evidence (G1) + offline evidence stats (2026-11-23). No LLM.
GSM8K invalid: the mutated step's expression evaluates to its stated result; the step differs from the gold step; the
  mutated final answer differs from gold; the evidence text states the mutated result. Valid: text states the gold result.
MuSiQue invalid: text differs from the gold sentence, contains the substitute, no longer contains the hop answer;
  substitute NER label recorded. Independent NLI check is NOT done here (needs a model) -> status stays rule_passed.
Also writes leakage (evidence states the item's final gold answer), length (words) and k/h per row.
v2 copy: field leaks_gold (user 2026-11-23). usage: python3 stage2_verify_v2.py <evidence.jsonl> <out.jsonl>"""
import sys, json, re, string, ast, operator
def norm(s):
    s = s.lower(); s = "".join(c for c in s if c not in set(string.punctuation)); s = re.sub(r"\b(a|an|the)\b", " ", s)
    return " ".join(s.split())
OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}
def ev(e):
    def f(n):
        if isinstance(n, ast.Expression): return f(n.body)
        if isinstance(n, ast.BinOp): return OPS[type(n.op)](f(n.left), f(n.right))
        if isinstance(n, ast.UnaryOp): return -f(n.operand)
        return n.value
    return f(ast.parse(e, mode="eval"))
def nums(t): return [float(x.replace(",", "")) for x in re.findall(r"\d[\d,]*(?:\.\d+)?", t)]
gsm = [json.loads(l) for l in open("data/raw/gsm8k_test.jsonl")]
mus = {x["id"]: x for x in map(json.loads, open("data/raw/musique/data/musique_ans_v1.0_dev.jsonl"))}
out = open(sys.argv[2], "w")
for r in map(json.loads, open(sys.argv[1])):
    t = r.get("evidence_text"); checks = {}
    if r["verification_status"] in ("pending",) and t:
        if r["dataset"] == "gsm8k":
            gold = float(gsm[int(r["item_id"])]["answer"].split("####")[-1].strip().replace(",", ""))
            if r["evidence_type"] == "invalid":
                e, res = r["mutated_step"].rsplit("=", 1)
                checks["arithmetic_consistent"] = abs(ev(e) - float(res)) < 1e-6
                checks["step_differs"] = r["mutated_step"] != r["original_step"]
                checks["final_differs"] = abs(float(r["mutated_final"]) - gold) > 1e-6
                checks["text_states_mutated_result"] = any(abs(v - float(res)) < 1e-6 for v in nums(t))
            else:
                res = float(r["original_step"].rsplit("=", 1)[1])
                checks["text_states_gold_result"] = any(abs(v - res) < 1e-6 for v in nums(t))
            leak = any(abs(v - gold) < 1e-6 for v in nums(t))
        else:
            x = mus[r["item_id"]]; golds = [x["answer"]] + x["answer_aliases"]
            if r["evidence_type"] == "invalid":
                a = r["original_step"].rsplit(" -> ", 1)[1]
                checks["differs_from_gold_sentence"] = t != r["gold_sentence"]
                checks["contains_substitute"] = r["substitute"].lower() in t.lower()
                checks["hop_answer_removed"] = re.search(r"(?<!\w)" + re.escape(a) + r"(?!\w)", t, re.I) is None
            else:
                a = r["original_step"].rsplit(" -> ", 1)[1]
                checks["contains_hop_answer"] = a.lower() in t.lower()
            leak = any(norm(g) and re.search(rf"(?<!\S){re.escape(norm(g))}(?!\S)", norm(t)) for g in golds)
        r["rule_checks"] = checks
        r["verification_status"] = "rule_passed" if all(checks.values()) else "rejected"
        if not all(checks.values()): r["reason"] = [k for k, v in checks.items() if not v]
        r["leaks_gold"] = bool(leak); r["evidence_words"] = len(t.split())
        r["nli_check"] = "not_run" if r["dataset"] == "musique" and r["evidence_type"] == "invalid" else "n/a"
    out.write(json.dumps(r, ensure_ascii=False) + "\n")
