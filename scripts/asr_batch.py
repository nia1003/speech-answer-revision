"""Whisper check for one Gemini TTS batch. English number words (and spoken fractions such as "one quarter",
"three-fourths", "a half") are converted back to digits before comparing the number/$/%/fraction tokens of the
original text and of the transcript. Also a normalized WER. New output file only.
usage: python asr_batch.py <rq4_v2 dir> <batch: q80|para40|gsm_frac96> <out.jsonl> [whisper_model] [device]"""
import sys, json, re, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import tts_gemini as T

ONES = {w: i for i, w in enumerate("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen "
                                    "fifteen sixteen seventeen eighteen nineteen".split())}
ONES["a"] = 1
TENS = {w: 10 * i for i, w in enumerate("_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()) if w != "_"}
DEN = {"half": 2, "halves": 2, "third": 3, "thirds": 3, "quarter": 4, "quarters": 4, "fourth": 4, "fourths": 4, "fifth": 5,
       "fifths": 5, "sixth": 6, "sixths": 6, "seventh": 7, "sevenths": 7, "eighth": 8, "eighths": 8, "ninth": 9, "ninths": 9,
       "tenth": 10, "tenths": 10}
def words_to_digits(s):
    s = re.sub(r"\b(" + "|".join(k for k in ONES if k != "a") + r"|a)[\s-]+(" + "|".join(DEN) + r")\b",
               lambda m: f"{ONES[m.group(1).lower()]}/{DEN[m.group(2).lower()]}", s, flags=re.I)
    toks = re.findall(r"[A-Za-z]+|[^A-Za-z]+", s); out, buf, gap = [], None, ""
    def flush():
        nonlocal buf, gap
        if buf is not None: out.append(str(buf[0] + buf[1]) + gap); buf = None; gap = ""
    for t in toks:
        w = t.lower()
        if w != "a" and (w in ONES or w in TENS or w in ("hundred", "thousand")):
            buf = buf or [0, 0]; gap = ""
            if w in ONES: buf[1] += ONES[w]
            elif w in TENS: buf[1] += TENS[w]
            elif w == "hundred": buf[1] = max(buf[1], 1) * 100
            else: buf[0] += max(buf[1], 1) * 1000; buf[1] = 0
        elif buf is not None and re.fullmatch(r"[ -]+", t): gap = t if " " in t else ""; continue
        else: flush(); out.append(t)
    flush(); return "".join(out)
keys = lambda s: re.findall(r"\$?\d+(?:\.\d+)?(?:/\d+)?%?|\$|%", s.replace(",", ""))
tok = lambda s: re.sub(r"[^\w\s$%./]", " ", words_to_digits(s).lower().replace(",", "")).split()
def wer(r, h):
    r, h = tok(r), tok(h); d = list(range(len(h) + 1))
    for i in range(1, len(r) + 1):
        p, d[0] = d[0], i
        for j in range(1, len(h) + 1): p, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, p + (r[i - 1] != h[j - 1]))
    return d[-1] / max(1, len(r))

if __name__ == "__main__":
    import whisper
    B, batch, outp = pathlib.Path(sys.argv[1]), sys.argv[2], sys.argv[3]
    model = whisper.load_model(sys.argv[4] if len(sys.argv) > 4 else "large-v3", device=sys.argv[5] if len(sys.argv) > 5 else "cuda")
    T.B, T.OUT = B, B / "out/tts_gemini"
    f = open(outp, "w"); n = bad = 0
    for b, rel, text in T.jobs():
        p = T.OUT / f"{rel}.wav"
        if b != batch or not p.exists(): continue
        hyp = model.transcribe(str(p), language="en", fp16=False)["text"].strip()
        k1, k2 = keys(words_to_digits(text)), keys(words_to_digits(hyp))
        rec = dict(batch=b, item=rel, wer=round(wer(text, hyp), 3), keys_text=k1, keys_heard=k2, keys_match=k1 == k2,
                   has_fraction=bool(re.search(r"\d+/\d+", text)), text=text, transcript=hyp)
        f.write(json.dumps(rec, ensure_ascii=False) + "\n"); f.flush(); n += 1; bad += not rec["keys_match"]
        print(rel, rec["wer"], "OK" if rec["keys_match"] else f"MISMATCH {k1} | {k2}", flush=True)
    print(f"ASR_BATCH_DONE {batch}: {n} clips, {bad} number/fraction mismatches", flush=True)
