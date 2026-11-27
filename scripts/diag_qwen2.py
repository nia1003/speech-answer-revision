"""Diagnosis round 2 (2026-11-21). Same 10 GSM8K items, text, greedy, max_new_tokens 1024. One change per variant:
  nosys        : Omni, bf16, eager, NO system prompt
  sdpa         : Omni, bf16, attn_implementation="sdpa", official system prompt
  thinker_bf16 : thinker-only class, bf16, eager, official system prompt (control: must equal 'base' to justify fp32 path)
  fp32         : thinker-only class, float32, eager, official system prompt (full Omni in fp32 does not fit 2x24GB)
  instruct     : Qwen/Qwen2.5-7B-Instruct, bf16, its own default chat template/system prompt, text only
usage: python diag_qwen2.py <variant> <smoke80_items.jsonl> <out.jsonl>"""
import sys, json, re, time, torch, transformers
from transformers import AutoTokenizer, AutoModelForCausalLM, Qwen2_5OmniForConditionalGeneration, Qwen2_5OmniProcessor
var, src, outp = sys.argv[1], sys.argv[2], sys.argv[3]
MID, REV = "Qwen/Qwen2.5-Omni-7B", "ae9e1690543ffd5c0221dc27f79834d0294cba00"
SYS = ("You are Qwen, a virtual human developed by the Qwen Team, Alibaba Group, "
       "capable of perceiving auditory and visual inputs, as well as generating text and speech.")
items = [json.loads(l) for l in open(src) if json.loads(l)["dataset"] == "gsm8k"][:10]

if var == "instruct":
    tok = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-7B-Instruct")
    lm = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-7B-Instruct", torch_dtype=torch.bfloat16, device_map="auto").eval()
    def gen(q):
        ids = tok.apply_chat_template([{"role": "user", "content": q}], add_generation_prompt=True, return_tensors="pt").to(lm.device)
        o = lm.generate(ids, max_new_tokens=1024, do_sample=False)
        return tok.decode(o[0, ids.shape[1]:], skip_special_tokens=True).strip(), tok.decode(ids[0])
else:
    proc = Qwen2_5OmniProcessor.from_pretrained(MID, revision=REV)
    if var in ("thinker_bf16", "fp32"):
        from transformers import Qwen2_5OmniThinkerForConditionalGeneration as T
        dt = torch.float32 if var == "fp32" else torch.bfloat16
        cfg = transformers.AutoConfig.from_pretrained(MID, revision=REV).thinker_config
        lm = T.from_pretrained(MID, revision=REV, config=cfg, torch_dtype=dt, device_map="auto").eval()
        gkw = {}
    else:
        kw = dict(torch_dtype=torch.bfloat16, device_map="auto")
        if var == "sdpa": kw["attn_implementation"] = "sdpa"
        lm = Qwen2_5OmniForConditionalGeneration.from_pretrained(MID, revision=REV, **kw); lm.disable_talker()
        gkw = {"return_audio": False}
    def gen(q):
        conv = ([] if var == "nosys" else [{"role": "system", "content": [{"type": "text", "text": SYS}]}]) + \
               [{"role": "user", "content": [{"type": "text", "text": q}]}]
        text = proc.apply_chat_template(conv, add_generation_prompt=True, tokenize=False)
        inp = proc(text=text, return_tensors="pt", padding=True).to(lm.device)
        o = lm.generate(**inp, max_new_tokens=1024, do_sample=False, **gkw)
        return proc.batch_decode(o[:, inp["input_ids"].shape[1]:], skip_special_tokens=True)[0].strip(), text
print("transformers", transformers.__version__, "| variant", var, "| dtype", next(lm.parameters()).dtype,
      "| attn(top)", getattr(lm.config, "_attn_implementation", None),
      "| attn(thinker LM)", getattr(getattr(getattr(lm, "thinker", lm), "model", lm).config, "_attn_implementation", None),
      "| attn(audio)", getattr(getattr(getattr(lm, "thinker", lm), "audio_tower", None), "config", None) and
      getattr(lm.thinker if hasattr(lm, "thinker") else lm, "audio_tower").config._attn_implementation if var != "instruct" else None, flush=True)
f = open(outp, "w")
for k, it in enumerate(items):
    t = time.time()
    with torch.no_grad(): out, prompt = gen(it["question"])
    if k == 0: print("PROMPT:", repr(prompt), flush=True)
    flags = dict(other_other=bool(re.search(r"\bother other\b", out)), human="Human:" in out, doubled=len(re.findall(r"\b(\w+) \1\b", out)))
    f.write(json.dumps(dict(variant=var, id=it["id"], answer=it["answer"], output=out, secs=round(time.time() - t, 2), **flags)) + "\n"); f.flush()
    print(it["id"], flags, "| tail:", out[-120:].replace("\n", " "), flush=True)
print("DIAG_DONE", var, flush=True)
