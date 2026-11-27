"""T1/T2 TTS (PREREG_2 sec. 2): Chatterbox, stage-1/smoke settings (default voice, exaggeration 0.5, cfg 0.5, temp 0.8,
tts_chatterbox.chunks, seed = SEED + chunk index, 0.2 s between chunks). MuSiQue text as written. Evidence clips use SEED;
fixed-sentence variants use their listed seed (+ chunk index). Resumable, never overwrites.
usage: python t12_tts.py <rq4_v2 dir> <tts_jobs.jsonl> <out_dir>"""
import sys, json, time, pathlib
import numpy as np, soundfile as sf, torch
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from tts_chatterbox import chunks, SEED, GAP
from chatterbox.tts import ChatterboxTTS
import importlib.metadata as md
B = pathlib.Path(sys.argv[1]); OUT = B / sys.argv[3]; (OUT / "audio").mkdir(parents=True, exist_ok=True)
model = ChatterboxTTS.from_pretrained(device="cuda"); SR = model.sr; ver = md.version("chatterbox-tts")
man = open(OUT / "manifest.jsonl", "a")
for j in map(json.loads, open(B / sys.argv[2])):
    path = OUT / "audio" / f"{j['name']}.wav"
    if path.exists(): continue
    s0 = j.get("seed", SEED); t0 = time.time(); parts = []; cs = chunks(j["text"])
    for k, c in enumerate(cs):
        torch.manual_seed(s0 + k)
        with torch.inference_mode(): w = model.generate(c, exaggeration=0.5, cfg_weight=0.5, temperature=0.8)
        parts.append(w.squeeze(0).float().cpu().numpy())
        if k < len(cs) - 1: parts.append(np.zeros(int(GAP * SR), np.float32))
    a = np.concatenate(parts); tmp = path.with_suffix(".tmp.wav"); sf.write(tmp, a, SR); tmp.rename(path)
    man.write(json.dumps(dict(j, tts_text=j["text"], textnorm="none", n_chunks=len(cs), secs=round(len(a) / SR, 2), tts_secs=round(time.time() - t0, 2),
                              model="ResembleAI/chatterbox", version=ver, voice="default (built-in)", seed=s0, sr=SR), ensure_ascii=False) + "\n"); man.flush()
    print(j["name"], len(cs), round(len(a) / SR, 2), flush=True)
print("T12_TTS_DONE", flush=True)
