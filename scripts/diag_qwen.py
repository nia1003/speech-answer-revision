"""Diagnose degraded Qwen2.5-Omni outputs (doubled words, leaked 'Human:', arithmetic slips).
Same 10 GSM8K items, text condition, greedy, max_new_tokens 1024, official system prompt. Variants via argv:
  base | sdpa | fp32 | nosys
Prints thinker generation_config and, per item, artifact flags; writes <out>.
usage: python diag_qwen.py <variant> <smoke80_items.jsonl> <out.jsonl>"""
import sys, json, re, os, time, torch, transformers
from transformers import Qwen2_5OmniForConditionalGeneration, Qwen2_5OmniProcessor
var, src, outp = sys.argv[1], sys.argv[2], sys.argv[3]
MID, REV = "Qwen/Qwen2.5-Omni-7B", "ae9e1690543ffd5c0221dc27f79834d0294cba00"
SYS = ("You are Qwen, a virtual human developed by the Qwen Team, Alibaba Group, "
       "capable of perceiving auditory and visual inputs, as well as generating text and speech.")
kw = dict(torch_dtype=torch.float32 if var == "fp32" else torch.bfloat16, device_map="auto")
if var == "sdpa": kw["attn_implementation"] = "sdpa"
model = Qwen2_5OmniForConditionalGeneration.from_pretrained(MID, revision=REV, **kw)
model.disable_talker(); proc = Qwen2_5OmniProcessor.from_pretrained(MID, revision=REV)
print("transformers", transformers.__version__, "| variant", var, "| attn", model.thinker.config._attn_implementation, flush=True)
print("thinker generation_config:", model.thinker.generation_config.to_diff_dict(), flush=True)
items = [json.loads(l) for l in open(src) if json.loads(l)["dataset"] == "gsm8k"][:10]
f = open(outp, "w")
for it in items:
    conv = ([] if var == "nosys" else [{"role": "system", "content": [{"type": "text", "text": SYS}]}]) + \
           [{"role": "user", "content": [{"type": "text", "text": it["question"]}]}]
    text = proc.apply_chat_template(conv, add_generation_prompt=True, tokenize=False)
    inp = proc(text=text, return_tensors="pt", padding=True).to(model.device)
    t = time.time()
    with torch.no_grad():
        o = model.generate(**inp, max_new_tokens=1024, do_sample=False, return_audio=False)
    out = proc.batch_decode(o[:, inp["input_ids"].shape[1]:], skip_special_tokens=True)[0].strip()
    flags = dict(other_other=bool(re.search(r"\bother other\b", out)), human="Human:" in out,
                 doubled=len(re.findall(r"\b(\w+) \1\b", out)))
    f.write(json.dumps(dict(variant=var, id=it["id"], answer=it["answer"], output=out, secs=round(time.time()-t, 2), **flags)) + "\n"); f.flush()
    print(it["id"], flags, "| tail:", out[-120:].replace("\n", " "), flush=True)
print("DIAG_DONE", flush=True)
