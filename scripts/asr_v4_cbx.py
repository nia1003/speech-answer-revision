"""v4 copy (2026-11-21): checks out/tts_full_v4.
v3 copy (2026-11-21): checks out/tts_full_v3. Reference = tts_textnorm_v2 text of the ORIGINAL question (digits kept,
fractions/ratios/times as in v2), so number words in the v3 TTS text are compared as values. Extra rules: "N dollars and M cents"
-> N.MM, "M cents" -> 0.MM, "N point d d" -> N.dd, million/billion; values compared as numbers (4.00 == 4), zeros dropped.
Original docstring:
Whisper large-v3 check of out/tts_full (one shard). Keys = numbers (and a/b, a:b) of the TTS text vs the transcript.
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
B, K = pathlib.Path(sys.argv[1]), int(sys.argv[2]); OUT = B / "out/tts_full_v4"
from tts_textnorm_v2 import normalize as norm_v2
G = {x["id"]: x["question"] for x in map(json.loads, open(B / "data/full_items.jsonl")) if x["dataset"] == "gsm8k"}
model = whisper.load_model("large-v3", device="cuda")
def prep(s):
    s = words_to_digits(s).replace(",", "")
    s = re.sub(r"\b(\d+) dollars? and (\d+) cents?\b", lambda m: f"{m.group(1)}.{int(m.group(2)):02d}", s)
    s = re.sub(r"\b(\d+) (?:euros?) and (\d+) cents?\b", lambda m: f"{m.group(1)}.{int(m.group(2)):02d}", s)
    s = re.sub(r"\b(\d+) cents?\b", lambda m: f"0.{int(m.group(1)):02d}", s)
    s = re.sub(r"\b(\d+) point ((?:\d ?)+)", lambda m: m.group(1) + "." + m.group(2).replace(" ", ""), s)
    s = re.sub(r"(\d+(?:\.\d+)?) (million|billion)\b", lambda m: "%d" % round(float(m.group(1)) * (1e6 if m.group(2) == "million" else 1e9)), s)
    s = re.sub(rf"\b(\d+)(?:st|nd|rd|th)?[ -]({DENRE})\b", lambda m: f"{m.group(1)}/{numwords.DEN[m.group(2).lower()]}", s, flags=re.I)
    s = re.sub(r"\b(\d+) (1[1-9]|20)ths?\b", r"\1/\2", s)                  # "1 16th" -> 1/16
    s = re.sub(r"\b(\d+) over (\d+)\b", r"\1/\2", s)
    s = re.sub(r"\b(\d+) to (\d+)\b", r"\1:\2", s)
    s = re.sub(r"\b(\d+) (?:o'clock|hundred hours|hundred)\b", r"\1", s)
    s = re.sub(r"\b(\d{1,2}):00\b", r"\1", s)
    s = re.sub(r"\b(\d+) and (?:1 )?(\d+/\d+)", r"\1 \2", s)
    s = re.sub(r"\b(\d+) and a (half|quarter)\b", lambda m: f"{m.group(1)} 1/{2 if m.group(2) == 'half' else 4}", s)
    return s.replace("$", " ").replace("%", " ")
def keys(s):
    out = []
    for k in re.findall(r"(?:\d+(?:\.\d+)?|\.\d+)(?:[/:]\d+)?", prep(s)):
        for p in re.split(r"[/:]", k):
            v = float(p)
            if v: out.append("%g" % v)
    return out
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
    ref = norm_v2(G[m["id"]]); k1, k2 = keys(ref), keys(hyp)
    rec = dict(dataset=m["dataset"], id=m["id"], item=m["item"], secs=m["secs"], text_changed=m["text_changed"],
               wer=round(wer(ref, hyp), 3), ref_text=ref, keys_text=k1, keys_heard=k2, keys_match=k1 == k2, tts_text=m["tts_text"], transcript=hyp)
    f.write(json.dumps(rec, ensure_ascii=False) + "\n"); f.flush(); n += 1; bad += k1 != k2
print(f"ASR_FULL_DONE shard {K}: {n} new, {bad} mismatches", flush=True)
