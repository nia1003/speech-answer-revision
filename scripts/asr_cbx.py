"""Whisper check for Chatterbox clips: number/$/%/fraction tokens of the original text vs the transcript, after
converting English number words and spoken fractions to digits on both sides (numwords.py); plus normalized WER.
usage: python asr_cbx.py <rq4_v2 dir> <out.jsonl> [whisper_model] [device]"""
import sys, json, re, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from numwords import words_to_digits
import whisper
B, outp = pathlib.Path(sys.argv[1]), sys.argv[2]
OUT = B / "out/tts_chatterbox"
model = whisper.load_model(sys.argv[3] if len(sys.argv) > 3 else "large-v3", device=sys.argv[4] if len(sys.argv) > 4 else "cuda")
keys = lambda s: re.findall(r"\$?\d+(?:\.\d+)?(?:/\d+)?%?|\$|%", words_to_digits(s).replace(",", ""))
tok = lambda s: re.sub(r"[^\w\s$%./]", " ", words_to_digits(s).lower().replace(",", "")).split()
def wer(r, h):
    r, h = tok(r), tok(h); d = list(range(len(h) + 1))
    for i in range(1, len(r) + 1):
        p, d[0] = d[0], i
        for j in range(1, len(h) + 1): p, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, p + (r[i - 1] != h[j - 1]))
    return d[-1] / max(1, len(r))
src = {}
for x in map(json.loads, open(B / "data/smoke80_items.jsonl")):
    src[f"question/{x['dataset']}_{x['id']}"] = x["question"]
    if x["dataset"] == "musique": src[f"paragraphs/musique_{x['id']}"] = "\n\n".join(f"{p['title']}: {p['text']}" for p in x["paragraphs"])
g = [json.loads(l) for l in open(B / "data/raw/gsm8k_test.jsonl")]
for i, r in enumerate(g): src.setdefault(f"question/gsm8k_{i}", r["question"])
f = open(outp, "w"); n = bad = 0
for m in map(json.loads, open(OUT / "manifest.jsonl")):
    text = src[m["item"]]
    hyp = model.transcribe(str(OUT / f"{m['item']}.wav"), language="en", fp16=False)["text"].strip()
    k1, k2 = keys(text), keys(hyp)
    rec = dict(batch=m["batch"], item=m["item"], secs=m["secs"], wer=round(wer(text, hyp), 3), keys_text=k1, keys_heard=k2,
               keys_match=k1 == k2, has_fraction=bool(re.search(r"\b\d+/\d+\b", text)), text=text, transcript=hyp)
    f.write(json.dumps(rec, ensure_ascii=False) + "\n"); f.flush(); n += 1; bad += not rec["keys_match"]
    print(m["item"], rec["wer"], "OK" if rec["keys_match"] else f"MISMATCH {k1} | {k2}", flush=True)
print(f"ASR_CBX_DONE: {n} clips, {bad} number/fraction mismatches", flush=True)
