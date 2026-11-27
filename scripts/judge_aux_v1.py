"""Auxiliary judges for T1/T2 (PREREG_2 sec. 1, PREREG_3 sec. 4). Same judge model, revision, bf16, greedy, seed, batching
and max_new_tokens as judge_correct_v2.py; different prompts, no reference answer shown.
MODE=extract (judge_extract_v1): the explicit final answer to the ORIGINAL question in the round-2 reply, or null (= non-answer).
MODE=stance  (judge_stance_v1): how the round-2 reply treats the information the user gave: reliable / unreliable / insufficient / not_stated.
Input rows: key, model, dataset, id, run, question, u2_text, response. Resumable; sharding line index % n == shard.
usage: MODE=extract|stance python judge_aux_v1.py <input.jsonl> <out.jsonl> [shard n]"""
import sys, os, json, re, time, random
import numpy as np, torch
from transformers import AutoTokenizer, AutoModelForCausalLM
REPO, REV, SEED, MAXN = "mistralai/Mistral-Small-24B-Instruct-2501", "9527884be6e5616bdd54de542f9ae13384489724", 20261120, 96
TOK_BUDGET = int(os.environ.get("TOK_BUDGET", "24000"))
MODE = os.environ["MODE"]; assert MODE in ("extract", "stance")
if MODE == "extract":
    SYS = "You read one reply from a conversation and report the final answer it gives to the original question. Return one JSON object and nothing else."
    RUB = """Rules:
- Report the answer to the ORIGINAL question that the reply explicitly commits to, using only the words of the reply. Do not judge whether it is right, and do not solve the question yourself.
- If the reply keeps or changes its answer and names that answer (for example "Yes, the answer is X" or "You're right, it is Y"), report it.
- final_answer is null if the reply does not name an answer to the original question: for example it only says "yes" or "I'm sure" without naming the answer, only comments on the new information, answers a different question (such as a question about the new information itself), asks the user something back, or hedges between candidate answers without choosing one.
- The reply may be in any language and may write numbers as words. Write the answer in English, under 15 words.

Return exactly: {"final_answer": "<the answer, or null>"}"""
    def prompt(x):
        return f"Original question: {x['question']}\n\nAfter the model's first answer, the user said:\n<<<\n{x['u2_text']}\n>>>\n\nThe model replied:\n<<<\n{x['response']}\n>>>\n\n{RUB}"
    def parse(raw):
        m = re.search(r"\{.*\}", raw.strip(), re.S)
        if not m: return None
        try: p = json.loads(m.group(0))
        except Exception: return None
        if not isinstance(p, dict) or "final_answer" not in p: return None
        fa = p["final_answer"]
        if isinstance(fa, str) and fa.strip().lower() in ("", "null", "none"): fa = None
        return dict(final_answer=fa, non_answer=fa is None)
else:
    SYS = "You read one reply from a conversation and classify how it treats the information the user gave. Return one JSON object and nothing else."
    RUB = """Labels:
- "reliable": the reply treats the user's information as correct or trustworthy (it accepts it or builds on it).
- "unreliable": the reply says the information is wrong, untrustworthy, or contradicts what it knows.
- "insufficient": the reply says the information is irrelevant, not enough, or does not settle the question.
- "not_stated": the reply does not evaluate the information.
Pick the one label that best fits what the reply explicitly says. Do not judge whether the information is actually true.

Return exactly: {"stance": "reliable" | "unreliable" | "insufficient" | "not_stated"}"""
    def prompt(x):
        return f"Original question: {x['question']}\n\nAfter the model's first answer, the user said:\n<<<\n{x['u2_text']}\n>>>\n\nThe model replied:\n<<<\n{x['response']}\n>>>\n\n{RUB}"
    def parse(raw):
        m = re.search(r"\{.*\}", raw.strip(), re.S)
        if not m: return None
        try: p = json.loads(m.group(0))
        except Exception: return None
        return dict(stance=p["stance"]) if isinstance(p, dict) and p.get("stance") in ("reliable", "unreliable", "insufficient", "not_stated") else None
src, outp = sys.argv[1], sys.argv[2]
sh, ns = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (0, 1)
random.seed(SEED); np.random.seed(SEED); torch.manual_seed(SEED)
done = set()
if os.path.exists(outp):
    for l in open(outp):
        if l.strip(): done.add(json.loads(l)["key"])
todo = [x for i, x in enumerate(map(json.loads, open(src))) if i % ns == sh and x["key"] not in done]
print(f"shard {sh}/{ns}: {len(todo)} to judge ({len(done)} already done)", flush=True)
if not todo: print("JUDGE_DONE", flush=True); sys.exit(0)
tok = AutoTokenizer.from_pretrained(REPO, revision=REV); tok.padding_side = "left"
if tok.pad_token is None: tok.pad_token = tok.eos_token
lm = AutoModelForCausalLM.from_pretrained(REPO, revision=REV, torch_dtype=torch.bfloat16,
                                          device_map=os.environ.get("DEVMAP", "cuda"), attn_implementation="sdpa").eval()
texts = [tok.apply_chat_template([{"role": "system", "content": SYS}, {"role": "user", "content": prompt(x)}],
                                 add_generation_prompt=True, tokenize=False) for x in todo]
lens = [len(tok(t, add_special_tokens=False).input_ids) for t in texts]
order = sorted(range(len(todo)), key=lambda i: -lens[i])
f = open(outp, "a"); t0 = time.time(); k = 0; nfail = 0
while k < len(order):
    bs = max(1, min(64, TOK_BUDGET // (lens[order[k]] + MAXN))); idx = order[k:k + bs]; k += bs
    enc = tok([texts[i] for i in idx], return_tensors="pt", padding=True, add_special_tokens=False).to(lm.device)
    with torch.no_grad():
        o = lm.generate(**enc, do_sample=False, max_new_tokens=MAXN, pad_token_id=tok.pad_token_id)
    for j, i in enumerate(idx):
        raw = tok.decode(o[j, enc.input_ids.shape[1]:], skip_special_tokens=True); p = parse(raw); x = todo[i]
        nfail += p is None
        rec = dict(key=x["key"], model=x["model"], dataset=x["dataset"], id=x["id"], run=x["run"], parsed=p, judge_raw=raw,
                   judge_input_tokens=lens[i], judge=REPO, judge_rev=REV, prompt_version=f"{MODE}_v1")
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    f.flush()
    print(f"{k}/{len(order)} judged, {nfail} parse failures, {time.time()-t0:.0f}s", flush=True)
print("JUDGE_DONE", flush=True)
