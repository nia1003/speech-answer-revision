"""Ablation probe (out/stage2_ablation_musique/PREREG.md): max_new_tokens 32; correct = exact (normalized) match to gold or
alias, or gold contained in the response, or token F1 >= 0.8. Items from S_ids.jsonl (all, no first_round filter).
--- copied from ---
Diagnostic a (PREREG_2026-11-24_musique_valid_diagnostics.md): probe where Qwen's MuSiQue chain breaks.
Sub-questions of question_decomposition asked one by one to Qwen2.5-Omni-7B (text, greedy, max_new_tokens 1024, official
system prompt), user turn = supporting paragraphs + blank line + sub-question (same format as A_bc). "#j" -> gold answer of
hop j; "X >> relation" -> "What is the relation of X?". Sub-answer correct = normalized gold hop answer (last hop: + final
answer aliases) appears as a whole-word span in the response. k = first wrong sub-question; all correct -> k = 1.
usage: python stage2_probe_qwen.py <ids.jsonl> <out.jsonl>"""
import sys, json, re, string, time, pathlib, torch
from transformers import Qwen2_5OmniForConditionalGeneration, Qwen2_5OmniProcessor
MID, REV = "Qwen/Qwen2.5-Omni-7B", "ae9e1690543ffd5c0221dc27f79834d0294cba00"; MAXN = 32
SYS = ("You are Qwen, a virtual human developed by the Qwen Team, Alibaba Group, "
       "capable of perceiving auditory and visual inputs, as well as generating text and speech.")
para_text = lambda it: "\n\n".join(f"{p['title']}: {p['text']}" for p in it["paragraphs"])
def norm(s):
    s = s.lower(); s = "".join(c for c in s if c not in set(string.punctuation)); s = re.sub(r"\b(a|an|the)\b", " ", s)
    return " ".join(s.split())
def has(o, a): return bool(norm(a)) and re.search(rf"(?<!\S){re.escape(norm(a))}(?!\S)", norm(o)) is not None
from collections import Counter
def f1(a, b):
    ta, tb = norm(a).split(), norm(b).split()
    if not ta or not tb: return 0.0
    c = sum((Counter(ta) & Counter(tb)).values())
    if c == 0: return 0.0
    p, r = c / len(ta), c / len(tb); return 2 * p * r / (p + r)
def ok(resp, a): return norm(resp) == norm(a) or has(resp, a) or f1(resp, a) >= 0.8
def subq(q, golds):
    q = re.sub(r"#(\d+)", lambda m: golds[int(m.group(1)) - 1], q)
    if ">>" in q:
        subj, rel = [x.strip() for x in q.split(">>", 1)]; q = f"What is the {rel} of {subj}?"
    return q
items = {(x["dataset"], str(x["id"])): x for x in map(json.loads, open("data/full_items.jsonl"))}
raw = {x["id"]: x for x in map(json.loads, open("data/raw/musique/data/musique_ans_v1.0_dev.jsonl"))}
model = Qwen2_5OmniForConditionalGeneration.from_pretrained(MID, revision=REV, torch_dtype=torch.bfloat16, device_map="cuda", attn_implementation="sdpa")
model.disable_talker(); proc = Qwen2_5OmniProcessor.from_pretrained(MID, revision=REV)
out = open(sys.argv[2], "w")
for p in map(json.loads, open(sys.argv[1])):
    if p["dataset"] != "musique": continue
    it = items[("musique", p["id"])]; x = raw[p["id"]]; qd = x["question_decomposition"]; golds = [d["answer"] for d in qd]; steps = []
    for j, d in enumerate(qd):
        q = subq(d["question"], golds)
        conv = [{"role": "system", "content": [{"type": "text", "text": SYS}]},
                {"role": "user", "content": [{"type": "text", "text": para_text(it) + "\n\n"}, {"type": "text", "text": q}]}]
        text = proc.apply_chat_template(conv, add_generation_prompt=True, tokenize=False)
        inp = proc(text=text, return_tensors="pt", padding=True).to(model.device)
        with torch.no_grad(): o = model.generate(**inp, max_new_tokens=MAXN, do_sample=False, return_audio=False)
        resp = proc.batch_decode(o[:, inp["input_ids"].shape[1]:], skip_special_tokens=True)[0].strip()
        acc = [d["answer"]] + ([x["answer"]] + x["answer_aliases"] if j == len(qd) - 1 else [])
        steps.append(dict(hop=j + 1, sub_question=q, gold=d["answer"], response=resp, correct=any(ok(resp, a) for a in acc)))
    k = next((s["hop"] for s in steps if not s["correct"]), 1)
    out.write(json.dumps(dict(item_id=p["id"], h=len(qd), step_bin=str(p.get("h")), k=k, all_correct=all(s["correct"] for s in steps),
                              steps=steps, model=MID, revision=REV), ensure_ascii=False) + "\n"); out.flush()
    print(p["id"], "k =", k, [s["correct"] for s in steps], flush=True)
print("PROBE_DONE", flush=True)
