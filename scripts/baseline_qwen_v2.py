"""v2 (2026-11-21): a blank line separates paragraphs from each other and the paragraph block from the question (A_bc, C_b).
Stage-1 single-turn baseline, smoke 80, Qwen2.5-Omni-7B. No evidence, no challenge, no second turn.
Decoding (user decision 2026-11-20): greedy, max_new_tokens 1024, official Qwen system prompt, talker off,
user turn = the item only (no instruction text).
Runs per item:
  GSM8K   : A_q (text question), C_q (audio question)
  MuSiQue : A_a (text q) / C_a (audio q)                       -> setting (a) question-only
            A_bc (text paragraphs + text q)                    -> text condition of (b) and (c) (identical input)
            C_b (text paragraphs + audio q)                    -> setting (b)
            C_c (audio paragraphs + audio q)                   -> setting (c)
Paragraphs come first, question second, as two parts of one user turn; paragraph string = tts_kokoro.para_text.
usage: python baseline_qwen.py <smoke80_items.jsonl> <tts_dir> <out.jsonl>"""
import sys, json, time, pathlib
import torch, soundfile as sf
from transformers import Qwen2_5OmniForConditionalGeneration, Qwen2_5OmniProcessor
from qwen_omni_utils import process_mm_info

MID, REV = "Qwen/Qwen2.5-Omni-7B", "ae9e1690543ffd5c0221dc27f79834d0294cba00"
MAXN = 1024
SYS = ("You are Qwen, a virtual human developed by the Qwen Team, Alibaba Group, "
       "capable of perceiving auditory and visual inputs, as well as generating text and speech.")
para_text = lambda it: "\n\n".join(f"{p['title']}: {p['text']}" for p in it["paragraphs"])

src, tts, outp = sys.argv[1], pathlib.Path(sys.argv[2]), pathlib.Path(sys.argv[3])
torch.manual_seed(0)
import os
DEVMAP = os.environ.get("DEVMAP", "cuda")   # "auto" splits the model over all visible GPUs (2x3090 run)
MAXMEM = os.environ.get("MAXMEM")          # e.g. "0:8GiB,1:22GiB": keep GPU 0 light so the audio encoder has room
kw = {"max_memory": {int(k): v for k, v in (x.split(":") for x in MAXMEM.split(","))}} if MAXMEM else {}
model = Qwen2_5OmniForConditionalGeneration.from_pretrained(MID, revision=REV, torch_dtype=torch.bfloat16, device_map=DEVMAP, **kw)
print("max_memory:", kw.get("max_memory"), flush=True)
print("device_map:", DEVMAP, "| GPUs:", [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())], flush=True)
model.disable_talker(); proc = Qwen2_5OmniProcessor.from_pretrained(MID, revision=REV)
tc = getattr(model.config, "thinker_config", model.config)
AID = getattr(tc, "audio_token_index", None) or getattr(tc, "audio_token_id", None)
EOS = {proc.tokenizer.eos_token_id, proc.tokenizer.convert_tokens_to_ids("<|im_end|>")}

def run(parts):
    conv = [{"role": "system", "content": [{"type": "text", "text": SYS}]}, {"role": "user", "content": parts}]
    text = proc.apply_chat_template(conv, add_generation_prompt=True, tokenize=False)
    a, i, v = process_mm_info(conv, use_audio_in_video=False)
    inp = proc(text=text, audio=a, images=i, videos=v, return_tensors="pt", padding=True).to(model.device).to(model.dtype)
    ids = inp["input_ids"][0]
    n_audio_tok = int((ids == AID).sum()) if AID is not None else None
    t = time.time()
    with torch.no_grad():
        o = model.generate(**inp, max_new_tokens=MAXN, do_sample=False, return_audio=False)
    torch.cuda.synchronize(); dt = time.time() - t
    gen = o[0, ids.shape[0]:]
    trunc = len(gen) >= MAXN and int(gen[-1]) not in EOS
    return dict(raw_output=proc.batch_decode(gen[None], skip_special_tokens=True)[0].strip(), infer_secs=round(dt, 2),
                n_new_tokens=int(len(gen)), truncated=bool(trunc), n_input_tokens=int(ids.shape[0]),
                n_audio_tokens=n_audio_tok, audio_input_secs=[round(len(x) / 16000, 2) for x in (a or [])])

wav = lambda kind, it: str(tts / kind / f"{it['dataset']}_{it['id']}.wav")
items = [json.loads(l) for l in open(src)]
done = set()
if outp.exists():
    for l in open(outp): x = json.loads(l); done.add((x["dataset"], str(x["id"]), x["run"]))
f = open(outp, "a")
SKIP_CC_OVER = float(os.environ.get("SKIP_CC_OVER", "0"))   # user decision 2026-11-20: skip C_c with paragraph audio > 188.68 s
PSECS = {str(x["id"]): x["secs"] for x in map(json.loads, open(tts / "manifest.jsonl")) if x["kind"] == "paragraphs"}
skipf = open(outp.with_name(outp.stem + "_skipped.jsonl"), "a")
for it in items:
    q_txt, q_aud = {"type": "text", "text": it["question"]}, {"type": "audio", "audio": wav("question", it)}
    runs = [("A_q", "A", "-", [q_txt]), ("C_q", "C", "-", [q_aud])]
    if it["dataset"] == "musique":
        p_txt, p_aud = {"type": "text", "text": para_text(it) + "\n\n"}, {"type": "audio", "audio": wav("paragraphs", it)}
        runs = [("A_a", "A", "a", [q_txt]), ("C_a", "C", "a", [q_aud]),
                ("A_bc", "A", "b/c", [p_txt, q_txt]), ("C_b", "C", "b", [p_txt, q_aud]), ("C_c", "C", "c", [p_aud, q_aud])]
    for name, cond, setting, parts in runs:
        if (it["dataset"], str(it["id"]), name) in done: continue
        if name == "C_c" and SKIP_CC_OVER and PSECS.get(str(it["id"]), 0) > SKIP_CC_OVER:
            skipf.write(json.dumps(dict(dataset=it["dataset"], id=it["id"], run=name, paragraph_audio_secs=PSECS[str(it["id"])],
                                        reason=f"memory limit on 24GB GPUs (paragraph audio > {SKIP_CC_OVER}s); hardware, not model limit")) + "\n")
            skipf.flush(); print(f"{it['dataset']}_{it['id']} {name}: SKIPPED ({PSECS[str(it['id'])]}s)", flush=True); continue
        r = run(parts)
        rec = dict(dataset=it["dataset"], id=it["id"], run=name, condition=cond, musique_setting=setting,
                   model=MID, revision=REV, **r)
        f.write(json.dumps(rec, ensure_ascii=False) + "\n"); f.flush()
        print(f"{it['dataset']}_{it['id']} {name}: {r['n_new_tokens']} tok {r['infer_secs']}s trunc={r['truncated']}", flush=True)
print("BASELINE_DONE", flush=True)
