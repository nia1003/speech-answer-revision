"""v2 (2026-11-21, user decision "改寫後跑全量"): tts_textnorm.normalize (fractions, ratios) plus
- clock times H:MM (not ratios; ratios are rewritten first): "1:00 PM" -> "one p.m.", "10:00" -> "ten o'clock",
  "16:00" -> "sixteen hundred", "2:15" -> "two fifteen", "2:05" -> "two oh five"
- amount written with the dollar sign after the number: "200$" -> "$200"
GSM8K question text only (MuSiQue questions contain neither). Only the TTS text changes; the text condition does not."""
import re, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from tts_textnorm import normalize as norm_v1
W = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
T = {2: "twenty", 3: "thirty", 4: "forty", 5: "fifty"}
def words(n): return W[n] if n < 20 else T[n // 10] + ("" if n % 10 == 0 else "-" + W[n % 10])
def clock(m):
    h, mm, ap = int(m.group(1)), int(m.group(2)), m.group(3)
    ap = f" {ap[0].lower()}.m." if ap else ""
    if mm == 0: s = words(h) + (ap if ap else (" o'clock" if h <= 12 else " hundred"))
    else: s = words(h) + " " + ("oh " + W[mm] if mm < 10 else words(mm)) + ap
    return s
def normalize(text):
    t = norm_v1(text)
    t = re.sub(r"\b(\d{1,2}):(\d{2})\b(?:\s*([AaPp])\.?[Mm]\.?)?", clock, t)
    t = re.sub(r"(?<![\$\w])(\d[\d,]*(?:\.\d+)?)\$", r"$\1", t)
    return t
if __name__ == "__main__":
    import json
    for x in map(json.loads, open(pathlib.Path(__file__).parent.parent / "data/full_items.jsonl")):
        if x["dataset"] == "gsm8k" and x["id"] in (23, 30, 128, 177, 303, 729, 862, 952, 953, 1001, 1195):
            print(x["id"], "->", normalize(x["question"])[:260]); print()
