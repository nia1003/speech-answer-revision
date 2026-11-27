"""Whisper large-v3 check of out/tts_full (one shard). Keys = numbers (and a/b, a:b) of the TTS text vs the transcript.
Both sides: number words/spoken fractions -> digits (numwords, denominators extended to 20), "<digit> <denominator word>"
-> a/b, "a over b" -> a/b, "a to b" -> a:b, "H o'clock"/"H hundred" -> H, H:00 -> H; $ % and commas dropped.
Also normalized WER vs the TTS text. Mismatches are reviewed by hand afterwards.
usage: python asr_full_cbx.py <rq4_v2 dir> <k>"""
import sys, json, re, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import numwords
from numwords import words_to_digits
EXT = {"eleventh": 11, "twelfth": 12, "thirteenth": 13, "fourteenth": 14, "fifteenth": 15, "sixteenth": 16,
       "seventeenth": 17, "eighteenth": 18, "nineteenth": 19, "twentieth": 20}
numwords.DEN.update({**EXT, **{k + "s": v for k, v in EXT.items()}})
DENRE = "|".join(sorted(numwords.DEN, key=len, reverse=True))
import whisper
B, K = pathlib.Path(sys.argv[1]), int(sys.argv[2]); OUT = B / "out/tts_full"
model = whisper.load_model("large-v3", device="cuda")
def prep(s):
    s = words_to_digits(s).replace(",", "")
    s = re.sub(rf"\b(\d+)(?:st|nd|rd|th)?[ -]({DENRE})\b", lambda m: f"{m.group(1)}/{numwords.DEN[m.group(2).lower()]}", s, flags=re.I)
    s = re.sub(r"\b(\d+) (1[1-9]|20)ths?\b", r"\1/\2", s)                  # "1 16th" -> 1/16
    s = re.sub(r"\b(\d+) over (\d+)\b", r"\1/\2", s)
    s = re.sub(r"\b(\d+) to (\d+)\b", r"\1:\2", s)
    s = re.sub(r"\b(\d+) (?:o'clock|hundred hours|hundred)\b", r"\1", s)
    s = re.sub(r"\b(\d{1,2}):00\b", r"\1", s)
    s = re.sub(r"\b(\d+) and (?:1 )?(\d+/\d+)", r"\1 \2", s)
    s = re.sub(r"\b(\d+) and a (half|quarter)\b", lambda m: f"{m.group(1)} 1/{2 if m.group(2) == 'half' else 4}", s)
    return s.replace("$", " ").replace("%", " ")
keys = lambda s: re.findall(r"\d+(?:\.\d+)?(?:[/:]\d+)?", prep(s))
tok = lambda s: re.sub(r"[^\w\s./:]", " ", prep(s).lower()).split()
def wer(r, h):
    r, h = tok(r), tok(h); d = list(range(len(h) + 1))
    for i in range(1, len(r) + 1):
        p, d[0] = d[0], i
        for j in range(1, len(h) + 1): p, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, p + (r[i - 1] != h[j - 1]))
    return d[-1] / max(1, len(r))
done = set()
outp = OUT / f"asr_shard{K}.jsonl"
if outp.exists(): done = {json.loads(l)["item"] for l in open(outp)}
f = open(outp, "a"); n = bad = 0
for m in map(json.loads, open(OUT / f"manifest_shard{K}.jsonl")):
    if m["item"] in done: continue
    hyp = model.transcribe(str(OUT / f"{m['item']}.wav"), language="en", fp16=False)["text"].strip()
    k1, k2 = keys(m["tts_text"]), keys(hyp)
    rec = dict(dataset=m["dataset"], id=m["id"], item=m["item"], secs=m["secs"], text_changed=m["text_changed"],
               wer=round(wer(m["tts_text"], hyp), 3), keys_text=k1, keys_heard=k2, keys_match=k1 == k2, tts_text=m["tts_text"], transcript=hyp)
    f.write(json.dumps(rec, ensure_ascii=False) + "\n"); f.flush(); n += 1; bad += k1 != k2
print(f"ASR_FULL_DONE shard {K}: {n} new, {bad} mismatches", flush=True)
