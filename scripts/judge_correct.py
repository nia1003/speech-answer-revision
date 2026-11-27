"""Stage 1 correctness judge (2026-11-22, user decision "Yes, use LLM judge": one judge for all five models).
Judge = mistralai/Mistral-Small-24B-Instruct-2501 @ 9527884be6e5616bdd54de542f9ae13384489724 (the plan's judge, same
revision as CP3), bf16, greedy, max_new_tokens 96, seed 20261120, zero-shot, one call per output.
The judge sees question + reference answer (+ MuSiQue aliases) + the response; never the rule verdict.
Language-agnostic (GLM answers partly in Chinese) and accepts number words (LLaMA-Omni2).
Batched with left padding, sorted by length (bf16 batching can flip a rare greedy token vs. batch size 1; noted).
Resumable: keys already in <out> are skipped.  Sharding: line index % n == shard.
usage: python judge_correct.py <judge_input.jsonl> <out.jsonl> [shard n]"""
import sys, os, json, re, time, random
import numpy as np, torch
from transformers import AutoTokenizer, AutoModelForCausalLM
REPO, REV, SEED, MAXN = "mistralai/Mistral-Small-24B-Instruct-2501", "9527884be6e5616bdd54de542f9ae13384489724", 20261120, 96
TOK_BUDGET = int(os.environ.get("TOK_BUDGET", "24000"))   # padded tokens per batch
SYS = "You grade whether a model's response answers a question correctly. Return one JSON object and nothing else."
RUB = """Rules:
- First decide which final answer the response commits to. If the response gives no final answer, gives several different final answers without settling on one, or is cut off before giving one, it is incorrect.
- The response may be written in any language (for example Chinese) and may write numbers as words. Judge the meaning, not the language or the wording.
- Math word problem: correct only if the response's final numeric answer equals the reference value. Ignore units, currency signs, commas and trailing zeros.
- Factual question: correct if the response's final answer refers to the same entity, date or value as the reference answer or one of the accepted aliases. Extra correct detail is fine. A different entity, or one that is clearly more general or more specific than the reference, is incorrect.
- Do not solve the question yourself, and do not use your own knowledge to decide whether the reference answer is right. The reference answer is always taken as right.

Return exactly: {"final_answer": "<the response's final answer in English, under 15 words, or null>", "is_correct": true or false}"""

def prompt(x):
    ref = x["answer"] + (f"\nAlso accepted: {'; '.join(x['aliases'])}" if x["aliases"] else "")
    kind = "Math word problem" if x["dataset"] == "gsm8k" else "Factual question"
    return f"{kind}: {x['question']}\n\nReference answer: {ref}\n\nResponse:\n<<<\n{x['response']}\n>>>\n\n{RUB}"

def parse(raw):
    s = raw.strip(); m = re.search(r"\{.*\}", s, re.S)
    if not m: return None
    try:
        p = json.loads(m.group(0))
    except Exception:
        return None
    return p if isinstance(p, dict) and isinstance(p.get("is_correct"), bool) else None

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
        rec = dict(key=x["key"], model=x["model"], dataset=x["dataset"], id=x["id"], run=x["run"],
                   judge_correct=(p["is_correct"] if p else None), judge_final=(p.get("final_answer") if p else None),
                   judge_raw=raw, judge_input_tokens=lens[i], rule_verdict=x["rule_verdict"], truncated=x["truncated"],
                   judge=REPO, judge_rev=REV)
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    f.flush()
    print(f"{k}/{len(order)} judged, {nfail} parse failures, {time.time()-t0:.0f}s", flush=True)
print("JUDGE_DONE", flush=True)
