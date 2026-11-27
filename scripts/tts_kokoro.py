"""Kokoro TTS for the stage-1 baseline. One fixed voice; every clip is synthesized once and reused by all models.
Writes <out>/question/<dataset>_<id>.wav and (MuSiQue) <out>/paragraphs/musique_<id>.wav, 24 kHz mono,
plus <out>/manifest.jsonl with seconds and synthesis time per clip.
Paragraph text (same string the text condition sees) = "\n\n".join(f"{title}: {text}") in dataset order.
usage: python tts_kokoro.py <smoke80_items.jsonl> <out_dir>"""
import sys, json, time, pathlib
import numpy as np, soundfile as sf, torch
from kokoro import KPipeline
import kokoro

VOICE, LANG, SR, SPEED = "af_heart", "a", 24000, 1.0
REPO = "hexgrad/Kokoro-82M"

def para_text(item):
    return "\n\n".join(f"{p['title']}: {p['text']}" for p in item["paragraphs"])

def synth(pipe, text):
    chunks = [np.asarray(a, dtype=np.float32) for _, _, a in pipe(text, voice=VOICE, speed=SPEED)]
    return np.concatenate(chunks) if chunks else np.zeros(0, np.float32)

if __name__ == "__main__":
    src, out = sys.argv[1], pathlib.Path(sys.argv[2])
    (out / "question").mkdir(parents=True, exist_ok=True); (out / "paragraphs").mkdir(parents=True, exist_ok=True)
    torch.manual_seed(0)
    pipe = KPipeline(lang_code=LANG, repo_id=REPO)
    items = [json.loads(l) for l in open(src)]
    man = open(out / "manifest.jsonl", "w")
    for it in items:
        jobs = [("question", it["question"])]
        if it["dataset"] == "musique": jobs.append(("paragraphs", para_text(it)))
        for kind, text in jobs:
            path = out / kind / f"{it['dataset']}_{it['id']}.wav"
            t = time.time(); a = synth(pipe, text); dt = time.time() - t
            sf.write(path, a, SR)
            rec = dict(dataset=it["dataset"], id=it["id"], kind=kind, path=str(path), chars=len(text),
                       secs=round(len(a) / SR, 2), tts_secs=round(dt, 2), voice=VOICE, model=REPO,
                       kokoro_version=getattr(kokoro, "__version__", "?"))
            man.write(json.dumps(rec, ensure_ascii=False) + "\n"); man.flush()
            print(f"{kind:10s} {it['dataset']}_{it['id']}: {rec['secs']}s audio, {dt:.1f}s", flush=True)
    print("TTS_DONE", flush=True)
