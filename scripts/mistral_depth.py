"""H1 check 1 / CP3–CP4: Mistral dependency-depth annotation of the 40 GSM8K items.
Frozen settings (CP0): mistralai/Mistral-Small-24B-Instruct-2501 @ 9527884be6e5616bdd54de542f9ae13384489724, bf16,
greedy, max_new_tokens 1024, seed 20261120, no few-shot, prompt = plan text verbatim, one call per item.
usage: python mistral_depth.py <gsm8k_depth_smoke_40.jsonl> <out.jsonl>    (run twice: run1, run2)"""
import sys, json, re, random, time
import numpy as np, torch
from transformers import AutoTokenizer, AutoModelForCausalLM

REPO, REV, SEED, MAXN = "mistralai/Mistral-Small-24B-Instruct-2501", "9527884be6e5616bdd54de542f9ae13384489724", 20261120, 1024
PROMPT = """You are annotating the dependency structure of a grade-school math solution.

Definitions:
- A STEP is one line of the solution that computes a NEW quantity. A line with several operators is still one step.
- Do NOT count as a step: copying a number given in the question (for example "14 = 14"), or a constant that is common knowledge (12 months, 60 minutes, 7 days).
- DO count as a step: a computation that the solution performs even if it has no <<...>> marker, and a final comparison (for example "1600 > 1200") that the answer depends on.
- Step B DEPENDS ON step A only if B uses the RESULT of A. Two numbers that happen to be equal do not make a dependency. A number given in the question is not a step.
- DEPTH is the number of steps on the longest chain A -> B -> C where each step depends on the previous one.

Task: read the question and the solution. List the steps, say which earlier steps each one uses, then give the depth and the number of steps.

Question:
{question}

Solution:
{solution}

Answer with JSON only, in this exact shape:
{{
  "steps": [
    {{"id": "a", "computes": "short description", "expr": "e.g. 3*4", "uses": [], "has_marker": true}},
    {{"id": "b", "computes": "...", "expr": "...", "uses": ["a"], "has_marker": false}}
  ],
  "depth": 2,
  "n_steps": 2,
  "flags": []
}}

"uses" lists ids of earlier steps whose results this step uses (empty if it only uses numbers from the question or constants).
"has_marker" is false for a step the solution performs without a <<...>> marker.
"flags" may contain any of: "unmarked_step", "multiple_solution_paths", "needs_outside_knowledge", "solution_written_backwards", "comparison_step", "ambiguous_dependency". Use [] if none apply."""

def parse(raw):
    s = raw.strip()
    m = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", s, re.S)   # strip one code fence if the whole output is fenced
    if m: s = m.group(1)
    try:
        p = json.loads(s)
        return (p, False) if isinstance(p, dict) else (None, True)
    except Exception:
        return None, True

if __name__ == "__main__":
    src, out = sys.argv[1], sys.argv[2]
    random.seed(SEED); np.random.seed(SEED); torch.manual_seed(SEED)
    tok = AutoTokenizer.from_pretrained(REPO, revision=REV)
    lm = AutoModelForCausalLM.from_pretrained(REPO, revision=REV, torch_dtype=torch.bfloat16, device_map="cuda").eval()
    items = [json.loads(l) for l in open(src)]
    assert len(items) == 40
    with open(out, "w") as f:
        for k, it in enumerate(items):
            msgs = [{"role": "user", "content": PROMPT.format(question=it["question"], solution=it["solution"])}]
            ids = tok.apply_chat_template(msgs, add_generation_prompt=True, return_tensors="pt").to("cuda")
            t = time.time()
            with torch.no_grad():
                o = lm.generate(ids, max_new_tokens=MAXN, do_sample=False, pad_token_id=tok.eos_token_id)
            gen = o[0, ids.shape[1]:]
            truncated = len(gen) >= MAXN and gen[-1].item() != tok.eos_token_id
            raw = tok.decode(gen, skip_special_tokens=True)
            p, err = parse(raw)
            fenced = raw.strip().startswith("```")   # recorded so a strict "no fence" rule can still be applied later
            f.write(json.dumps({"idx": it["idx"], "raw_output": raw, "parsed": p, "parse_error": err, "fenced": fenced,
                                "truncated": truncated, "n_new_tokens": int(len(gen))}, ensure_ascii=False) + "\n"); f.flush()
            print(f"[{k+1}/40] idx {it['idx']} depth {p.get('depth') if p else 'PARSE_ERROR'} "
                  f"{len(gen)} tok {time.time()-t:.0f}s", flush=True)
    print("MISTRAL_DONE", flush=True)
