"""Whisper check of out/tts_chatterbox_norm. Keys (numbers/$/%/fractions/ratios) of the ORIGINAL question vs the transcript.
Both sides: English number words and spoken fractions -> digits (numwords.py, denominators extended to 11-20 here),
"a over b" -> a/b, "a to b" -> a:b only where the original had a ratio a:b. $ and % are dropped on both sides
(Whisper writes "$2" as "2 dollars" etc.). Mixed numbers: original "1 1/2" is compared as "1 and 1/2".
usage: python asr_cbx_norm.py <rq4_v2 dir> <out.jsonl>"""
import sys, json, re, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import numwords
from numwords import words_to_digits
numwords.DEN.update({"eleventh": 11, "elevenths": 11, "twelfth": 12, "twelfths": 12, "thirteenth": 13, "thirteenths": 13,
                     "fourteenth": 14, "fourteenths": 14, "fifteenth": 15, "fifteenths": 15, "sixteenth": 16, "sixteenths": 16})
import whisper
B, outp = pathlib.Path(sys.argv[1]), sys.argv[2]; OUT = B / "out/tts_chatterbox_norm"
model = whisper.load_model("large-v3", device="cuda")
g = [json.loads(l) for l in open(B / "data/raw/gsm8k_test.jsonl")]
def keys(s, ratios=()):
    s = words_to_digits(s).replace(",", "")
    s = re.sub(r"\b(\d+) over (\d+)\b", r"\1/\2", s)
    for a, b in ratios: s = re.sub(rf"\b{a} to {b}\b", f"{a}:{b}", s)
    s = re.sub(r"\b(\d+) and (?:1 )?(\d+/\d+)", r"\1 \2", s)          # "1 and 1/2" -> "1 1/2"
    s = re.sub(r"\b(\d+) and a (half|quarter)", lambda m: f"{m.group(1)} 1/{2 if m.group(2)=='half' else 4}", s)
    return re.findall(r"\d+(?:\.\d+)?(?:[/:]\d+)?", s.replace("$", "").replace("%", ""))
f = open(outp, "w"); n = bad = 0
for m in map(json.loads, open(OUT / "manifest.jsonl")):
    i = int(m["item"].split("_")[-1]); orig = g[i]["question"]
    hyp = model.transcribe(str(OUT / f"{m['item']}.wav"), language="en", fp16=False)["text"].strip()
    rat = re.findall(r"\b(\d+):(\d+)\b", orig)
    k1, k2 = keys(orig), keys(hyp, rat)
    rec = dict(item=m["item"], secs=m["secs"], keys_text=k1, keys_heard=k2, keys_match=k1 == k2, text=orig, tts_text=m["tts_text"], transcript=hyp)
    f.write(json.dumps(rec, ensure_ascii=False) + "\n"); f.flush(); n += 1; bad += k1 != k2
    print(m["item"], "OK" if k1 == k2 else f"MISMATCH {k1} | {k2}", flush=True)
print(f"ASR_CBXN_DONE: {n} clips, {bad} mismatches", flush=True)
