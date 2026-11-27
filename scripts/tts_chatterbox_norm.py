"""Chatterbox re-synthesis of GSM8K questions whose TTS text changes under tts_textnorm.normalize (fractions -> words,
ratios -> "a to b"; user decision 2026-11-21). Same model/settings/seeding/chunking as tts_chatterbox.py.
New output dir out/tts_chatterbox_norm (the earlier out/tts_chatterbox is kept unchanged). Manifest stores the TTS text.
usage: python tts_chatterbox_norm.py <rq4_v2 dir>"""
import sys, json, time, pathlib
import numpy as np, soundfile as sf, torch
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from tts_chatterbox import chunks, SEED, GAP
from tts_textnorm import normalize
B = pathlib.Path(sys.argv[1]); OUT = B / "out/tts_chatterbox_norm"
g = [json.loads(l) for l in open(B / "data/raw/gsm8k_test.jsonl")]
todo = [(i, g[i]["question"], normalize(g[i]["question"])) for i in range(len(g)) if normalize(g[i]["question"]) != g[i]["question"]]
print("to synthesize:", len(todo), flush=True)
from chatterbox.tts import ChatterboxTTS
import importlib.metadata as md
model = ChatterboxTTS.from_pretrained(device="cuda"); SR = model.sr; ver = md.version("chatterbox-tts")
(OUT / "question").mkdir(parents=True, exist_ok=True); man = open(OUT / "manifest.jsonl", "a")
for i, orig, text in todo:
    path = OUT / f"question/gsm8k_{i}.wav"
    if path.exists(): continue
    t = time.time(); parts = []; cs = chunks(text)
    for k, c in enumerate(cs):
        torch.manual_seed(SEED + k)
        with torch.inference_mode(): w = model.generate(c, exaggeration=0.5, cfg_weight=0.5, temperature=0.8)
        parts.append(w.squeeze(0).float().cpu().numpy())
        if k < len(cs) - 1: parts.append(np.zeros(int(GAP * SR), np.float32))
    a = np.concatenate(parts); sf.write(path, a, SR); dt = time.time() - t
    rec = dict(item=f"question/gsm8k_{i}", tts_text=text, chars=len(text), n_chunks=len(cs), secs=round(len(a) / SR, 2),
               tts_secs=round(dt, 2), model="ResembleAI/chatterbox", version=ver, voice="default (built-in)", seed=SEED, sr=SR,
               textnorm="tts_textnorm.py v1")
    man.write(json.dumps(rec, ensure_ascii=False) + "\n"); man.flush(); print(rec["item"], rec["secs"], f"{dt:.1f}s", flush=True)
print("TTS_CBXN_DONE", flush=True)
