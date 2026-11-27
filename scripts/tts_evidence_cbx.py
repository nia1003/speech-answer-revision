"""Stage 2 smoke v2: evidence audio with Chatterbox, same model/settings/seeding/chunking as stage 1 questions
(tts_chatterbox.chunks, SEED, GAP; exaggeration 0.5, cfg 0.5, temperature 0.8, default voice). Synthesized once,
shared by all models. GSM8K text -> tts_speak_ops.speak (operators as words) around tts_textnorm_v4.normalize (numbers as words);
MuSiQue text as written. Unsupported ("Are you sure?") is one shared file. Only rows that passed verification.
usage: python tts_evidence_cbx.py <rq4_v2 dir> <evidence_final.jsonl> <out_dir>"""
import sys, json, time, pathlib
import numpy as np, soundfile as sf, torch
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from tts_chatterbox import chunks, SEED, GAP
from tts_textnorm_v4 import normalize
from tts_speak_ops import speak
B = pathlib.Path(sys.argv[1]); EV = B / sys.argv[2]; OUT = B / sys.argv[3]; (OUT / "audio").mkdir(parents=True, exist_ok=True)
from chatterbox.tts import ChatterboxTTS
import importlib.metadata as md
model = ChatterboxTTS.from_pretrained(device="cuda"); SR = model.sr; ver = md.version("chatterbox-tts")
man = open(OUT / "manifest.jsonl", "a"); jobs = []
for r in map(json.loads, open(EV)):
    if r["verification_status"] not in ("approved", "rule_passed", "nli_passed"): continue
    if r["evidence_type"] == "unsupported":
        if not any(j[0] == "unsupported" for j in jobs): jobs.append(("unsupported", r["evidence_text"], "none", None))
        continue
    t = speak(r["evidence_text"], normalize) if r["dataset"] == "gsm8k" else r["evidence_text"]
    jobs.append((f"{r['dataset']}_{r['item_id']}_{r['evidence_type']}", t, "speak_ops+tts_textnorm_v4+speak_ops_after" if r["dataset"] == "gsm8k" else "none", r))
for name, text, tn, r in jobs:
    path = OUT / "audio" / f"{name}.wav"
    if path.exists(): continue
    t0 = time.time(); parts = []; cs = chunks(text)
    for k, c in enumerate(cs):
        torch.manual_seed(SEED + k)
        with torch.inference_mode(): w = model.generate(c, exaggeration=0.5, cfg_weight=0.5, temperature=0.8)
        parts.append(w.squeeze(0).float().cpu().numpy())
        if k < len(cs) - 1: parts.append(np.zeros(int(GAP * SR), np.float32))
    a = np.concatenate(parts); tmp = path.with_suffix(".tmp.wav"); sf.write(tmp, a, SR); tmp.rename(path)
    man.write(json.dumps(dict(name=name, dataset=r["dataset"] if r else None, item_id=r["item_id"] if r else None,
                              evidence_type=r["evidence_type"] if r else "unsupported", evidence_text=r["evidence_text"] if r else text,
                              tts_text=text, textnorm=tn, n_chunks=len(cs), secs=round(len(a) / SR, 2), tts_secs=round(time.time() - t0, 2),
                              model="ResembleAI/chatterbox", version=ver, voice="default (built-in)", seed=SEED, sr=SR), ensure_ascii=False) + "\n")
    man.flush()
print("TTS_EVIDENCE_DONE", len(jobs), flush=True)
