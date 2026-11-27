"""English number words / spoken fractions -> digits (copied from asr_batch.py, 2026-11-21)."""
import re

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
    last = None
    for t in toks:
        w = t.lower()
        if w == "and" and buf is not None and last in ("hundred", "thousand"):
            continue
        if w.strip(): last = w if w.isalpha() else last
        if w != "a" and (w in ONES or w in TENS or w in ("hundred", "thousand")):
            buf = buf or [0, 0]; gap = ""
            if w in ONES: buf[1] += ONES[w]
            elif w in TENS: buf[1] += TENS[w]
            elif w == "hundred": buf[1] = max(buf[1], 1) * 100
            else: buf[0] += max(buf[1], 1) * 1000; buf[1] = 0
        elif buf is not None and re.fullmatch(r"[ -]+", t): gap = t if " " in t else ""; continue
        else: flush(); out.append(t)
    flush(); return "".join(out)
