"""Chatterbox TTS for the stage-1 baseline (user decision 2026-11-21), resumable.
- chatterbox-tts 0.1.2, ResembleAI/chatterbox, built-in default voice (no reference clip), default exaggeration 0.5,
  cfg_weight 0.5, temperature 0.8. Sampling is seeded per clip (seed = 20261120 + chunk index) so a rerun gives the same audio
  on the same hardware.
- Text is sent as written (no number/fraction rewriting). Long text is split at sentence boundaries into chunks of
  <= 300 characters; chunks are synthesized separately and joined with 0.2 s of silence.
- Order: q80 (smoke questions) -> para40 (MuSiQue paragraph strings, same string as the text condition) -> gsm_frac96.
- Output: <out>/{question,paragraphs}/<dataset>_<id>.wav (24 kHz) and <out>/manifest.jsonl.
usage: python tts_chatterbox.py <rq4_v2 dir> [batch ...]"""
import sys, json, re, time, pathlib
import numpy as np, soundfile as sf, torch

B = pathlib.Path(sys.argv[1]); OUT = B / "out/tts_chatterbox"; SEED = 20261120; MAXC = 300; GAP = 0.2
only = set(sys.argv[2:])

def jobs():
    smoke = [json.loads(l) for l in open(B / "data/smoke80_items.jsonl")]
    q80 = [("q80", f"question/{x['dataset']}_{x['id']}", x["question"]) for x in smoke]
    para = [("para40", f"paragraphs/musique_{x['id']}", "\n\n".join(f"{p['title']}: {p['text']}" for p in x["paragraphs"]))
            for x in smoke if x["dataset"] == "musique"]
    g = [json.loads(l) for l in open(B / "data/raw/gsm8k_test.jsonl")]
    steps = {x["id"]: x for x in map(json.loads, open(B / "out/step_axis/item_steps.jsonl")) if x["dataset"] == "gsm8k"}
    frac = [("gsm_frac96", f"question/gsm8k_{i}", g[i]["question"]) for i in range(len(g))
            if not steps[i]["no_marker"] and re.search(r"\b\d+/\d+\b", g[i]["question"])]
    return q80 + para + frac

def chunks(text):
    sents = re.split(r"(?<=[.!?])\s+|\n\n+", text.strip()); out, cur = [], ""
    for s in sents:
        if not s: continue
        while len(s) > MAXC:                                   # very long sentence: split at the last comma/space
            cut = max(s.rfind(",", 0, MAXC), s.rfind(" ", 0, MAXC)); cut = cut if cut > 50 else MAXC
            if cur: out.append(cur); cur = ""
            out.append(s[:cut + 1].strip()); s = s[cut + 1:].strip()
        if len(cur) + len(s) + 1 > MAXC and cur: out.append(cur); cur = s
        else: cur = (cur + " " + s).strip()
    if cur: out.append(cur)
    return out

if __name__ == "__main__":
    from chatterbox.tts import ChatterboxTTS
    import importlib.metadata as md
    model = ChatterboxTTS.from_pretrained(device="cuda"); SR = model.sr
    ver = md.version("chatterbox-tts")
    (OUT / "question").mkdir(parents=True, exist_ok=True); (OUT / "paragraphs").mkdir(parents=True, exist_ok=True)
    man = open(OUT / "manifest.jsonl", "a")
    for batch, rel, text in jobs():
        if only and batch not in only: continue
        path = OUT / f"{rel}.wav"
        if path.exists(): continue
        t = time.time(); parts = []
        cs = chunks(text)
        for k, c in enumerate(cs):
            torch.manual_seed(SEED + k)
            with torch.inference_mode():
                w = model.generate(c, exaggeration=0.5, cfg_weight=0.5, temperature=0.8)
            parts.append(w.squeeze(0).float().cpu().numpy())
            if k < len(cs) - 1: parts.append(np.zeros(int(GAP * SR), np.float32))
        a = np.concatenate(parts); sf.write(path, a, SR); dt = time.time() - t
        rec = dict(batch=batch, item=rel, chars=len(text), n_chunks=len(cs), secs=round(len(a) / SR, 2), tts_secs=round(dt, 2),
                   model="ResembleAI/chatterbox", version=ver, voice="default (built-in)", seed=SEED, sr=SR)
        man.write(json.dumps(rec, ensure_ascii=False) + "\n"); man.flush()
        print(f"{batch} {rel}: {rec['secs']}s audio, {len(cs)} chunks, {dt:.1f}s", flush=True)
    print("TTS_CBX_DONE", flush=True)
