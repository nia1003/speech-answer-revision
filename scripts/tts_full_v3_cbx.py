"""v3 copy (2026-11-21): GSM8K only, TTS text = tts_textnorm_v3.normalize (all numbers in words), output out/tts_full_v3.
Original docstring of tts_full_cbx.py:
Full question-audio synthesis with Chatterbox (user decision 2026-11-21 "改寫後跑全量").
All 3,736 items of data/full_items.jsonl (GSM8K 1,319 + MuSiQue 2,417), questions only (no paragraph audio).
TTS text: GSM8K -> tts_textnorm_v2.normalize (fractions, ratios, clock times, "N$"); MuSiQue -> question as written.
Model/settings/seeding/chunking identical to tts_chatterbox.py. Sharded: item index % N == k. Resumable.
Output: out/tts_full/question/<dataset>_<id>.wav, out/tts_full/manifest_shard<k>.jsonl
usage: python tts_full_cbx.py <rq4_v2 dir> <k> <N>"""
import sys, json, time, pathlib
import numpy as np, soundfile as sf, torch
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from tts_chatterbox import chunks, SEED, GAP
from tts_textnorm_v3 import normalize
B, K, N = pathlib.Path(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]); OUT = B / "out/tts_full_v3"
items = [x for x in map(json.loads, open(B / "data/full_items.jsonl")) if x["dataset"] == "gsm8k"]
todo = [x for j, x in enumerate(items) if j % N == K]
print(f"shard {K}/{N}: {len(todo)} items", flush=True)
from chatterbox.tts import ChatterboxTTS
import importlib.metadata as md
model = ChatterboxTTS.from_pretrained(device="cuda"); SR = model.sr; ver = md.version("chatterbox-tts")
(OUT / "question").mkdir(parents=True, exist_ok=True); man = open(OUT / f"manifest_shard{K}.jsonl", "a")
for x in todo:
    rel = f"question/{x['dataset']}_{x['id']}"; path = OUT / f"{rel}.wav"
    if path.exists(): continue
    text = normalize(x["question"]) if x["dataset"] == "gsm8k" else x["question"]
    t = time.time(); parts = []; cs = chunks(text)
    for k, c in enumerate(cs):
        torch.manual_seed(SEED + k)
        with torch.inference_mode(): w = model.generate(c, exaggeration=0.5, cfg_weight=0.5, temperature=0.8)
        parts.append(w.squeeze(0).float().cpu().numpy())
        if k < len(cs) - 1: parts.append(np.zeros(int(GAP * SR), np.float32))
    a = np.concatenate(parts); tmp = path.with_suffix(".tmp.wav"); sf.write(tmp, a, SR); tmp.rename(path); dt = time.time() - t
    rec = dict(dataset=x["dataset"], id=x["id"], item=rel, tts_text=text, text_changed=text != x["question"], chars=len(text),
               n_chunks=len(cs), secs=round(len(a) / SR, 2), tts_secs=round(dt, 2), model="ResembleAI/chatterbox", version=ver,
               voice="default (built-in)", seed=SEED, sr=SR, textnorm="tts_textnorm_v3" if x["dataset"] == "gsm8k" else "none")
    man.write(json.dumps(rec, ensure_ascii=False) + "\n"); man.flush()
print("TTS_FULL_DONE", K, flush=True)
