"""Stage 1 baseline for Ultravox (fixie-ai/ultravox-v0_4), same runs/inputs/output schema as baseline_qwen_v3.py (2026-11-21).
Aligned with Qwen (feedback: keep the 5 models consistent): attn_implementation="sdpa", greedy (do_sample=False),
max_new_tokens 1024, repetition_penalty 1.0 (the pipeline default is 1.1; not used so decoding is plain greedy like Qwen),
eos = <|eot_id|> + tokenizer eos (as in the official pipeline). System prompt = the model card's example system turn.
User message = the question only (text), or "<|audio|>" (audio question), or paragraphs + blank line + question.
Audio: soundfile, librosa resample to 16 kHz, UltravoxProcessor (handles >30 s by chunking).
  GSM8K   : A_q (text question), C_q (audio question)
  MuSiQue : A_a (question only), A_bc (text paragraphs + text q), C_b (text paragraphs + audio q)
usage: RUNS=... python baseline_ultravox.py <items.jsonl> <tts_dir> <out.jsonl>   (resumable)"""
import sys, json, time, os, pathlib
import torch, transformers, librosa, soundfile as sf
MID = "fixie-ai/ultravox-v0_4"; MAXN = 1024
SYS = "You are a friendly and helpful character. You love to answer questions for people."
para_text = lambda it: "\n\n".join(f"{p['title']}: {p['text']}" for p in it["paragraphs"])
src, tts, outp = sys.argv[1], pathlib.Path(sys.argv[2]), pathlib.Path(sys.argv[3])
torch.manual_seed(0)
pipe = transformers.pipeline(model=MID, trust_remote_code=True,
                             model_kwargs={"torch_dtype": torch.bfloat16, "device_map": {"": 0}, "attn_implementation": "sdpa"})
model, tok, proc = pipe.model.eval(), pipe.tokenizer, pipe.processor
REV = getattr(model.config, "_commit_hash", None)
seen = {}
for _, m in model.named_modules():
    c = getattr(m, "config", None); a = getattr(c, "_attn_implementation", None) if c is not None else None
    if a is not None: seen.setdefault(type(c).__name__, a)
print("attn per config:", seen, "| revision", REV, flush=True)
EOS = [tok.eos_token_id] + ([tok.convert_tokens_to_ids("<|eot_id|>")] if "<|eot_id|>" in tok.added_tokens_encoder else [])
RUNS = set(os.environ["RUNS"].split(",")) if os.environ.get("RUNS") else None
ONLY = set(os.environ["ONLY_IDS"].split(",")) if os.environ.get("ONLY_IDS") else None

def load16(p):
    a, sr = sf.read(p, dtype="float32")
    if a.ndim > 1: a = a.mean(1)
    return librosa.resample(a, orig_sr=sr, target_sr=16000) if sr != 16000 else a

def run(user_text, audio_path=None):
    text = tok.apply_chat_template([{"role": "system", "content": SYS}, {"role": "user", "content": user_text}],
                                   add_generation_prompt=True, tokenize=False)
    audio = load16(audio_path) if audio_path else None
    inp = proc(text=text, audio=audio, sampling_rate=16000) if audio is not None else proc(text=text)
    if "audio_values" in inp: inp["audio_values"] = inp["audio_values"].to(model.dtype)
    inp = {k: (v.to(model.device) if hasattr(v, "to") else v) for k, v in inp.items()}
    n_in = int(inp["input_ids"].shape[1]); t = time.time()
    with torch.no_grad():
        o = model.generate(**inp, do_sample=False, max_new_tokens=MAXN, repetition_penalty=1.0, eos_token_id=EOS)
    torch.cuda.synchronize(); dt = time.time() - t
    gen = o[0, n_in:]
    trunc = len(gen) >= MAXN and int(gen[-1]) not in EOS
    return dict(raw_output=tok.decode(gen, skip_special_tokens=True).strip(), infer_secs=round(dt, 2), n_new_tokens=int(len(gen)),
                truncated=bool(trunc), n_input_tokens=n_in, audio_input_secs=[round(len(audio) / 16000, 2)] if audio is not None else [])

wav = lambda it: str(tts / "question" / f"{it['dataset']}_{it['id']}.wav")
items = [json.loads(l) for l in open(src)]
done = set()
if outp.exists():
    for l in open(outp): x = json.loads(l); done.add((x["dataset"], str(x["id"]), x["run"]))
f = open(outp, "a")
for it in items:
    q = it["question"]
    runs = [("A_q", "A", "-", q, None), ("C_q", "C", "-", "<|audio|>", wav)]
    if it["dataset"] == "musique":
        p = para_text(it) + "\n\n"
        runs = [("A_a", "A", "a", q, None), ("A_bc", "A", "b/c", p + q, None), ("C_b", "C", "b", p + "<|audio|>", wav)]
    for name, cond, setting, utext, w in runs:
        if (it["dataset"], str(it["id"]), name) in done: continue
        if RUNS and name not in RUNS: continue
        if ONLY and str(it["id"]) not in ONLY: continue
        r = run(utext, w(it) if w else None)
        rec = dict(dataset=it["dataset"], id=it["id"], run=name, condition=cond, musique_setting=setting, model=MID, revision=REV, **r)
        f.write(json.dumps(rec, ensure_ascii=False) + "\n"); f.flush()
        print(f"{it['dataset']}_{it['id']} {name}: {r['n_new_tokens']} tok {r['infer_secs']}s trunc={r['truncated']}", flush=True)
print("BASELINE_DONE", flush=True)
