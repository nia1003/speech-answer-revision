"""Ablation round 2 (out/stage2_ablation_musique/PREREG.md), text only. Identical protocol to the smoke round 2 text path
(stage2_round2_qwen.py): Qwen2.5-Omni-7B @ ae9e1690, sdpa, greedy, max_new_tokens 1024, official system prompt, talker off;
history = paragraphs (A_bc format) + question, assistant = stage-1 A_bc raw output; second user turn = condition message.
Resumable by (item, condition). A failed call is retried once; failures are recorded.
usage: python stage2_ablation_round2.py <conditions.jsonl> <out.jsonl>"""
import sys, json, time, torch
from transformers import Qwen2_5OmniForConditionalGeneration, Qwen2_5OmniProcessor
MID, REV = "Qwen/Qwen2.5-Omni-7B", "ae9e1690543ffd5c0221dc27f79834d0294cba00"; MAXN = 1024
SYS = ("You are Qwen, a virtual human developed by the Qwen Team, Alibaba Group, "
       "capable of perceiving auditory and visual inputs, as well as generating text and speech.")
para_text = lambda it: "\n\n".join(f"{p['title']}: {p['text']}" for p in it["paragraphs"])
items = {str(x["id"]): x for x in map(json.loads, open("data/full_items.jsonl")) if x["dataset"] == "musique"}
r0 = {str(json.loads(l)["id"]): json.loads(l) for l in open("out/full/scored_full_textA_qwen25omni_sdpa_v2.jsonl")
      if json.loads(l)["dataset"] == "musique" and json.loads(l)["run"] == "A_bc"}
torch.manual_seed(0)
model = Qwen2_5OmniForConditionalGeneration.from_pretrained(MID, revision=REV, torch_dtype=torch.bfloat16, device_map="cuda", attn_implementation="sdpa")
model.disable_talker(); proc = Qwen2_5OmniProcessor.from_pretrained(MID, revision=REV)
EOS = {proc.tokenizer.eos_token_id, proc.tokenizer.convert_tokens_to_ids("<|im_end|>")}
def gen(conv):
    text = proc.apply_chat_template(conv, add_generation_prompt=True, tokenize=False)
    inp = proc(text=text, return_tensors="pt", padding=True).to(model.device)
    ids = inp["input_ids"][0]; t = time.time()
    with torch.no_grad(): o = model.generate(**inp, max_new_tokens=MAXN, do_sample=False, return_audio=False)
    torch.cuda.synchronize(); g = o[0, ids.shape[0]:]
    return dict(raw_output=proc.batch_decode(g[None], skip_special_tokens=True)[0].strip(), infer_secs=round(time.time() - t, 2),
                n_new_tokens=int(len(g)), truncated=bool(len(g) >= MAXN and int(g[-1]) not in EOS), n_input_tokens=int(ids.shape[0]))
import os
done = set()
if os.path.exists(sys.argv[2]):
    for l in open(sys.argv[2]): x = json.loads(l); done.add((x["item_id"], x["condition"]))
f = open(sys.argv[2], "a"); nerr = 0
for c in map(json.loads, open(sys.argv[1])):
    if not c["defined"] or (c["item_id"], c["condition"]) in done: continue
    it = items[c["item_id"]]; a0 = r0[c["item_id"]]["raw_output"]
    conv = [{"role": "system", "content": [{"type": "text", "text": SYS}]},
            {"role": "user", "content": [{"type": "text", "text": para_text(it) + "\n\n"}, {"type": "text", "text": it["question"]}]},
            {"role": "assistant", "content": [{"type": "text", "text": a0}]},
            {"role": "user", "content": [{"type": "text", "text": c["message"]}]}]
    r, err = None, None
    for attempt in (1, 2):
        try: r = gen(conv); break
        except Exception as e: err = repr(e); print("ERROR", c["item_id"], c["condition"], attempt, err, flush=True)
    if r is None: nerr += 1; r = dict(raw_output=None, error=err)
    f.write(json.dumps(dict(item_id=c["item_id"], condition=c["condition"], h=c["h"], message=c["message"], r0=a0, model=MID, revision=REV, **r),
                       ensure_ascii=False) + "\n"); f.flush()
    print(c["item_id"], c["condition"], r.get("n_new_tokens"), r.get("truncated"), flush=True)
print("ABLATION_ROUND2_DONE errors", nerr, flush=True)
