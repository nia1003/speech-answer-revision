"""T1/T2 generation (PREREG_2 sec. 1-2, PREREG_3). Qwen2.5-Omni-7B @ ae9e1690, sdpa, bf16, greedy, official system prompt,
talker off, torch.manual_seed(0). First turn = stage-1 input of that modality (MuSiQue A_bc / C_b: text paragraphs + text/audio
question; GSM8K A_q / C_q), assistant = stage-1 raw output. Round 2 (max_new_tokens 1024) only when the request has no stored
round-2 output; round 3 (max_new_tokens 64) = forced final answer, text or the fixed audio sentence. Speech round-2 audio =
the request's parts joined with 300 ms silence (a single part is used as is). Each call is retried once; failures recorded.
Resumable by rid. Sharding: request index % n == shard.
usage: python t12_runner.py <requests.jsonl> <out.jsonl> [shard n]"""
import sys, os, json, time, pathlib
import numpy as np, torch, soundfile as sf
from transformers import Qwen2_5OmniForConditionalGeneration, Qwen2_5OmniProcessor
from qwen_omni_utils import process_mm_info
MID, REV = "Qwen/Qwen2.5-Omni-7B", "ae9e1690543ffd5c0221dc27f79834d0294cba00"
SYS = ("You are Qwen, a virtual human developed by the Qwen Team, Alibaba Group, "
       "capable of perceiving auditory and visual inputs, as well as generating text and speech.")
FORCED = "Based on our conversation, what is your final answer to the original question? Reply with only the answer."
SIL = 0.3
B = pathlib.Path.cwd(); TTS = B / "out/tts_speech_final_view"; CAT = B / "out/stage2_measurement_check/round2_audio"; CAT.mkdir(exist_ok=True)
FIXED = json.load(open(B / "out/stage2_measurement_check/fixed_choice.json"))
para_text = lambda it: "\n\n".join(f"{p['title']}: {p['text']}" for p in it["paragraphs"])
items = {(x["dataset"], str(x["id"])): x for x in map(json.loads, open(B / "data/full_items.jsonl"))}
first = {}
for fp in ("out/full/scored_full_textA_qwen25omni_sdpa_v2.jsonl", "out/full/scored_full_speechC_qwen25omni_sdpa_v2.jsonl"):
    p = B / fp
    if not p.exists(): p = B / fp.replace("out/full/scored_full_speechC", "out/full_speechC/scored_full_speechC")
    for l in open(p):
        r = json.loads(l); first[(r["dataset"], str(r["id"]), r["run"])] = r
inp_f, outp = sys.argv[1], pathlib.Path(sys.argv[2])
sh, nsh = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (0, 1)
torch.manual_seed(0)
model = Qwen2_5OmniForConditionalGeneration.from_pretrained(MID, revision=REV, torch_dtype=torch.bfloat16, device_map="cuda", attn_implementation="sdpa")
model.disable_talker(); proc = Qwen2_5OmniProcessor.from_pretrained(MID, revision=REV)
EOS = {proc.tokenizer.eos_token_id, proc.tokenizer.convert_tokens_to_ids("<|im_end|>")}
def concat(name, files):
    if len(files) == 1: return files[0]
    p = CAT / f"{name}.wav"
    if not p.exists():
        parts, sr0 = [], None
        for i, f in enumerate(files):
            a, sr = sf.read(f, dtype="float32"); sr0 = sr0 or sr; assert sr == sr0, (f, sr, sr0)
            if a.ndim > 1: a = a.mean(1)
            if i: parts.append(np.zeros(int(SIL * sr), np.float32))
            parts.append(a)
        tmp = p.with_suffix(".tmp.wav"); sf.write(tmp, np.concatenate(parts), sr0); tmp.rename(p)
    return str(p)
def gen(conv, maxn):
    text = proc.apply_chat_template(conv, add_generation_prompt=True, tokenize=False)
    a, i, v = process_mm_info(conv, use_audio_in_video=False)
    inp = proc(text=text, audio=a, images=i, videos=v, return_tensors="pt", padding=True).to(model.device).to(model.dtype)
    ids = inp["input_ids"][0]; t = time.time()
    with torch.no_grad(): o = model.generate(**inp, max_new_tokens=maxn, do_sample=False, return_audio=False)
    torch.cuda.synchronize(); g = o[0, ids.shape[0]:]
    return dict(raw_output=proc.batch_decode(g[None], skip_special_tokens=True)[0].strip(), infer_secs=round(time.time() - t, 2),
                n_new_tokens=int(len(g)), truncated=bool(len(g) >= maxn and int(g[-1]) not in EOS), n_input_tokens=int(ids.shape[0]))
def call(conv, maxn):
    err = None
    for attempt in (1, 2):
        try: return gen(conv, maxn), None
        except Exception as e: err = repr(e); print("ERROR", attempt, err, flush=True)
    return dict(raw_output=None), err
done = set()
if outp.exists():
    for l in open(outp): done.add(json.loads(l)["rid"])
f = open(outp, "a"); nerr = 0
for n, q in enumerate(map(json.loads, open(inp_f))):
    if n % nsh != sh or q["rid"] in done: continue
    ds, iid, mod = q["dataset"], q["item_id"], q["modality"]; it = items[(ds, iid)]
    run1 = ("A_q" if mod == "text" else "C_q") if ds == "gsm8k" else ("A_bc" if mod == "text" else "C_b")
    qq = {"type": "text", "text": it["question"]} if mod == "text" else {"type": "audio", "audio": str(TTS / "question" / f"{ds}_{iid}.wav")}
    parts1 = [qq] if ds == "gsm8k" else [{"type": "text", "text": para_text(it) + "\n\n"}, qq]
    r0 = first[(ds, iid, run1)]["raw_output"]
    conv = [{"role": "system", "content": [{"type": "text", "text": SYS}]}, {"role": "user", "content": parts1},
            {"role": "assistant", "content": [{"type": "text", "text": r0}]}]
    if mod == "text": u2 = [{"type": "text", "text": q["u2_text"]}]; u2_audio = None
    else: u2_audio = concat(q["rid"].replace("|", "__"), [str(B / p) for p in q["u2_audio_parts"]]); u2 = [{"type": "audio", "audio": u2_audio}]
    conv.append({"role": "user", "content": u2})
    if q.get("r2_existing") is not None: r2, e2 = dict(raw_output=q["r2_existing"], reused=True), None
    else: r2, e2 = call(conv, 1024)
    rec = dict(rid=q["rid"], dataset=ds, item_id=iid, modality=mod, stage1_run=run1, r0=r0, u2_text=q["u2_text"], u2_audio=u2_audio,
               r2=r2, r2_error=e2, model=MID, revision=REV)
    if r2.get("raw_output") is not None:
        conv3 = conv + [{"role": "assistant", "content": [{"type": "text", "text": r2["raw_output"]}]},
                        {"role": "user", "content": [{"type": "text", "text": FORCED} if mod == "text" else {"type": "audio", "audio": str(B / FIXED["fixed_forced"]) if not FIXED["fixed_forced"].startswith("/") else FIXED["fixed_forced"]}]}]
        r3, e3 = call(conv3, 64)
    else: r3, e3 = dict(raw_output=None), "no_round2"
    rec.update(r3=r3, r3_error=e3); nerr += (e2 is not None) + (e3 is not None)
    f.write(json.dumps(rec, ensure_ascii=False) + "\n"); f.flush()
    print(q["rid"], r2.get("n_new_tokens"), r3.get("raw_output", "")[:60] if r3.get("raw_output") else None, flush=True)
print("T12_RUN_DONE errors", nerr, flush=True)
