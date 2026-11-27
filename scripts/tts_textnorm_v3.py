"""v3 (2026-11-21, user decision after listening: Chatterbox read the second "125" in GSM8K 885 as "105"):
every number in the GSM8K TTS text is written out in English words, so the TTS never has to read digits.
Order: tts_textnorm_v2.normalize (fractions, ratios, clock times, "N$" -> "$N") first, then:
- money: "$1.20" -> "one dollar and twenty cents", "$0.30"/"$.30" -> "thirty cents", "$2.00" -> "two dollars",
  "$175,000" -> "one hundred seventy-five thousand dollars", "$1.5 million" -> "one point five million dollars",
  "$15/hour" -> "fifteen dollars per hour"; euro likewise
- percent: "10%" -> "ten percent", "2.5%" -> "two point five percent"
- fractions with an ordinal suffix left by v1 ("1/3rd", "3/4ths") -> fraction words
- ordinals: "5th" -> "fifth"
- years: a 4-digit number 1100-2099 after in/since/from/by/until/of/year/until/before/after -> "nineteen ninety-five",
  "two thousand seven", "twenty ten"
- "#5" -> "number five"; leading minus "-5" -> "negative five"
- other numbers: integers (commas allowed) -> words, decimals -> "one point five", "0.25" -> "zero point two five"
GSM8K only; the text condition is unchanged."""
import re, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from tts_textnorm_v2 import normalize as norm_v2
from tts_textnorm import frac

ONES = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
TENS = {2: "twenty", 3: "thirty", 4: "forty", 5: "fifty", 6: "sixty", 7: "seventy", 8: "eighty", 9: "ninety"}
ORD_IRR = {"one": "first", "two": "second", "three": "third", "five": "fifth", "eight": "eighth", "nine": "ninth", "twelve": "twelfth"}

def below1000(n):
    out = []
    if n >= 100: out.append(ONES[n // 100] + " hundred"); n %= 100
    if n >= 20: out.append(TENS[n // 10] + ("-" + ONES[n % 10] if n % 10 else ""))
    elif n or not out: out.append(ONES[n])
    return " ".join(out)

def int_words(n):
    if n == 0: return "zero"
    if n < 0: return "negative " + int_words(-n)
    parts = []
    for v, name in ((10**12, "trillion"), (10**9, "billion"), (10**6, "million"), (1000, "thousand")):
        if n >= v: parts.append(below1000(n // v) + " " + name); n %= v
    if n: parts.append(below1000(n))
    return " ".join(parts)

def dec_words(s):                                           # "1.5" -> "one point five", ".25" -> "zero point two five"
    s = s.replace(",", "")
    if "." not in s: return int_words(int(s))
    a, b = s.split(".", 1)
    return int_words(int(a or "0")) + " point " + " ".join(ONES[int(d)] for d in b)

def ordinal(n):
    w = int_words(n); head, sep, last = w.rpartition(" ") if " " in w else ("", "", w)
    h2, dash, unit = last.rpartition("-")
    unit = ORD_IRR.get(unit, (unit[:-1] + "ieth") if unit.endswith("y") else unit + "th")
    last = h2 + dash + unit
    return (head + sep + last).strip()

def year_words(y):
    if 2000 <= y <= 2009: return int_words(y)
    hi, lo = divmod(y, 100)
    return below1000(hi) + (" hundred" if lo == 0 else (" oh " + ONES[lo] if lo < 10 else " " + below1000(lo)))

def money(m):
    cur, num, scale, per = m.group(1), m.group(2).replace(",", ""), m.group(3), m.group(4)
    unit, cent = ("dollar", "cent") if cur == "$" else ("euro", "cent")
    if scale:
        s = f"{dec_words(num)} {scale.lower()} {unit}s"
    else:
        a, _, b = num.partition(".")
        d = int(a or "0"); c = int((b + "00")[:2]) if b else 0
        if b and len(b) > 2: s = f"{dec_words(num)} {unit}s"
        elif d and c: s = f"{int_words(d)} {unit}{'s' if d != 1 else ''} and {int_words(c)} {cent}{'s' if c != 1 else ''}"
        elif c: s = f"{int_words(c)} {cent}{'s' if c != 1 else ''}"
        else: s = f"{int_words(d)} {unit}{'s' if d != 1 else ''}"
    return s + (f" per {per}" if per else "")

NUM = r"(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?|\.\d+)"   # commas only as thousands separators
def normalize(text):
    t = norm_v2(text)
    t = re.sub(r"\b(\d+)/(\d+)(?:st|nd|rd|th)s?\b", lambda m: frac(m.group(1), m.group(2)), t)
    t = re.sub(r"([$€])" + NUM + r"(?:\s+(million|billion|thousand)\b)?(?:/(hour|day|week|month|year|hr|night|person))?",
               money, t, flags=re.I)
    t = re.sub(NUM + r"\s?%", lambda m: dec_words(m.group(1)) + " percent", t)
    t = re.sub(r"\b(\d+)(st|nd|rd|th)\b", lambda m: ordinal(int(m.group(1))), t)
    t = re.sub(r"\b(in|since|from|by|until|of|year|before|after)\s+(1[1-9]\d\d|20\d\d)\b(?!,\d)",
               lambda m: m.group(1) + " " + year_words(int(m.group(2))), t, flags=re.I)
    t = re.sub(r"#(\d+)", lambda m: "number " + int_words(int(m.group(1))), t)
    t = re.sub(r"(?<![\w.])-(\d)", r"negative \1", t)
    t = re.sub(r"(?<![\w.])" + NUM + r"(?=\D|$)", lambda m: dec_words(m.group(1)), t)
    t = re.sub(r"(?<=[a-z])(\d)", r" \1", t)                 # safety; should not trigger
    return t

if __name__ == "__main__":
    for s in ["makes 125 chimichangas on Tuesdays, 125 on Wednesdays", "raises a total of $175,000. $50,000 comes",
              "A pencil costs $1.20 and an eraser costs $0.30.", "an aquarium for $10.00 and coral at $2.00 apiece and $.50",
              "Tom found 214 seashells", "earns $15/hour and got a 10% raise, 2.5% tax", "the 5th and 21st and 3rd day",
              "In 2010 and since 1995 and in 2007", "He ate 1/3rd and 3/4ths", "$1.5 million house", "1,234,567 people",
              "0.25 of 12.48 kg", "#3 player", "it drops to -5 degrees", "from 1:00 PM to 5:00 PM 3/4 of 7:11 ratio is 7:11."]:
        print(s, "\n   ->", normalize(s))
