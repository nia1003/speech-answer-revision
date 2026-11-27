"""Supplementary S1: rewrite each truncated chain (k = 2..n, including the full chain k = n) into one natural question with
Qwen2.5-7B-Instruct (user approved 2026-11-21). The original MuSiQue question is NOT changed; the rewrite is a new field.
Prompt: the k sub-questions with their answers (#j = answer of step j) + 3 fixed examples taken from MuSiQue 2hop items
(decomposition -> crowd-written question; 2hop items are not part of S1). Greedy first; if the question leaks any
intermediate answer or the final answer (normalized whole-word match), or is not a single question, retry up to 3 times
with sampling (T 0.7, top_p 0.9, seed 20261121 + attempt). All attempts are kept.
usage: python rewrite_trunc.py <rq4_v2 dir>"""
import sys, json, re, string, pathlib, torch
from transformers import AutoModelForCausalLM, AutoTokenizer
B = pathlib.Path(sys.argv[1]); SK = B / "out/trunc/trunc_skeleton.jsonl"; OUT = B / "out/trunc/trunc_rewritten.jsonl"
MID = "Qwen/Qwen2.5-7B-Instruct"
def norm(s):
    s = s.lower(); s = "".join(c for c in s if c not in set(string.punctuation))
    return " ".join(re.sub(r"\b(a|an|the)\b", " ", s).split())
def leaks(q, answers):
    nq = norm(q); return [a for a in answers if norm(a) and re.search(rf"(?<!\S){re.escape(norm(a))}(?!\S)", nq)]
def steps_txt(sq, sa):
    return "\n".join(f"Step {i}: {q}  (answer: {a})" for i, (q, a) in enumerate(zip(sq, sa), 1))
dev = [json.loads(l) for l in open(B / "data/raw/musique/data/musique_ans_v1.0_dev.jsonl")]
shots = [d for d in dev if d["id"].startswith("2hop") and any(">>" in s["question"] for s in d["question_decomposition"])][:3]
SYS = ("You turn a chain of simple sub-questions into ONE natural English question. '#1', '#2' ... stand for the answer of "
       "step 1, step 2 .... The question must ask for the answer of the LAST step, must describe every intermediate entity "
       "only through the earlier steps, and must NOT contain the answer of any step. 'X >> relation' means 'the relation of X'. "
       "Output only the question.")
def msgs(sq, sa):
    m = [{"role": "system", "content": SYS}]
    for d in shots:
        m += [{"role": "user", "content": steps_txt([s["question"] for s in d["question_decomposition"]],
                                                    [s["answer"] for s in d["question_decomposition"]])},
              {"role": "assistant", "content": d["question"]}]
    return m + [{"role": "user", "content": steps_txt(sq, sa)}]
tok = AutoTokenizer.from_pretrained(MID)
model = AutoModelForCausalLM.from_pretrained(MID, torch_dtype=torch.bfloat16, attn_implementation="sdpa", device_map={"": 0}).eval()
done = set()
if OUT.exists(): done = {(json.loads(l)["chain_id"], json.loads(l)["k"]) for l in open(OUT)}
f = open(OUT, "a"); n = nbad = 0
for r in map(json.loads, open(SK)):
    if (r["chain_id"], r["k"]) in done: continue
    ids = tok.apply_chat_template(msgs(r["sub_questions"], r["sub_answers"]), add_generation_prompt=True, return_tensors="pt").to("cuda")
    attempts = []
    for a in range(4):
        kw = dict(do_sample=False) if a == 0 else dict(do_sample=True, temperature=0.7, top_p=0.9)
        if a: torch.manual_seed(20261121 + a)
        with torch.inference_mode(): o = model.generate(ids, max_new_tokens=120, pad_token_id=tok.eos_token_id, **kw)
        q = tok.decode(o[0][ids.shape[1]:], skip_special_tokens=True).strip().split("\n")[0].strip()
        lk = leaks(q, r["sub_answers"]); single = q.endswith("?") and q.count("?") == 1
        attempts.append(dict(attempt=a, question=q, leaked=lk, single_question=single))
        if not lk and single: break
    ok = not attempts[-1]["leaked"] and attempts[-1]["single_question"]
    rec = dict(chain_id=r["chain_id"], chain_type=r["chain_type"], k=r["k"], is_full=r["is_full"], rewritten_question=attempts[-1]["question"],
               auto_ok=ok, n_attempts=len(attempts), attempts=attempts, answer=r["answer"], original_question=r["original_question"],
               sub_questions=r["sub_questions"], sub_answers=r["sub_answers"], model=MID, few_shot_ids=[d["id"] for d in shots])
    f.write(json.dumps(rec, ensure_ascii=False) + "\n"); f.flush(); n += 1; nbad += not ok
    print(r["chain_id"], r["k"], "OK" if ok else "FLAG", "|", rec["rewritten_question"], flush=True)
print(f"REWRITE_DONE {n} new, {nbad} flagged", flush=True)
