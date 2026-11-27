"""v4 (2026-11-21, user decision "修改、然後跑全量" after CP_B12 item 205): v3 wrote "92, 100 and 86" as
"one hundred and eighty-six", heard as 186. Fix: before v3, a bare round number (>=100, multiple of 100, no $ before it)
followed by " and <number>" gets a comma: "100 and 86" -> "100, and 86" -> "one hundred, and eighty-six".
Everything else is identical to v3."""
import re, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from tts_textnorm_v3 import normalize as norm_v3

def _fix(m):
    n = int(m.group(1).replace(",", ""))
    return m.group(1) + "," + m.group(2) if n >= 100 and n % 100 == 0 else m.group(0)

def normalize(text):
    t = re.sub(r"(?<![$€\d.,])(\d{1,3}(?:,\d{3})+|\d+)(?![\d.,])(\s+and\s+)(?=[$€]?\d)", _fix, text)
    return norm_v3(t)

if __name__ == "__main__":
    for s in ["scores of 89, 71, 92, 100 and 86 on", "$100 and $86", "1,000 and 5 apples", "120 and 30", "2.00 and 5"]:
        print(s, "->", normalize(s))
