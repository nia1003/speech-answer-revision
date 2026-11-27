"""Spot-check Kokoro readings of GSM8K numbers, $ and % : Whisper transcript next to the original question,
with the number/$/% tokens of each side listed for manual comparison. Also a rough WER after normalization
(lowercase, punctuation removed, commas in numbers removed). CPU is fine for 40 short clips.
usage: python asr_check.py <smoke80_items.jsonl> <tts_dir> <out.jsonl> [whisper_model]"""
import sys, json, re, pathlib
import whisper

items = [json.loads(l) for l in open(sys.argv[1]) if json.loads(l)["dataset"] == "gsm8k"]
tts, out = pathlib.Path(sys.argv[2]), open(sys.argv[3], "w")
name = sys.argv[4] if len(sys.argv) > 4 else "large-v3"
asr = whisper.load_model(name, device="cpu")
tok = lambda s: re.sub(r"[^\w\s$%.]", " ", s.lower().replace(",", "")).split()
keys = lambda s: re.findall(r"\$?\d+(?:\.\d+)?%?|\$|%", s.replace(",", ""))
def wer(r, h):
    r, h = tok(r), tok(h); d = list(range(len(h) + 1))
    for i in range(1, len(r) + 1):
        p, d[0] = d[0], i
        for j in range(1, len(h) + 1):
            p, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, p + (r[i - 1] != h[j - 1]))
    return d[-1] / max(1, len(r))
for it in items:
    hyp = asr.transcribe(str(tts / "question" / f"gsm8k_{it['id']}.wav"), language="en", fp16=False)["text"].strip()
    rec = dict(id=it["id"], question=it["question"], transcript=hyp, wer=round(wer(it["question"], hyp), 3),
               keys_text=keys(it["question"]), keys_heard=keys(hyp), asr_model=name)
    out.write(json.dumps(rec, ensure_ascii=False) + "\n"); out.flush()
    print(it["id"], rec["wer"], rec["keys_text"], "|", rec["keys_heard"], flush=True)
print("ASR_DONE")
