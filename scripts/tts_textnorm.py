"""Text normalization applied before TTS for the speech conditions (user decision 2026-11-21: "改寫成分數詞").
Applied to GSM8K question text only. MuSiQue slashes are names/dates ("Directive 10/2", "9/11"), so MuSiQue is left as is.
Rules (the text condition is NOT changed; only the string sent to TTS):
- mixed number "1 1/2" -> "one and a half"            (not after ':' -- "16:00 2/3" is a time followed by a fraction)
- fraction "3/4" -> "three quarters", "1/2" -> "one half", "7/13" -> "seven thirteenths"; denominators > 20 -> "a over b"
- ratio "7:11" -> "7 to 11", only in a sentence containing "ratio" and not followed by AM/PM (times are left as is)
usage: from tts_textnorm import normalize"""
import re

W = ("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen "
     "eighteen nineteen twenty").split()
ORD = {2: "half", 3: "third", 4: "quarter", 5: "fifth", 6: "sixth", 7: "seventh", 8: "eighth", 9: "ninth", 10: "tenth",
       11: "eleventh", 12: "twelfth", 13: "thirteenth", 14: "fourteenth", 15: "fifteenth", 16: "sixteenth",
       17: "seventeenth", 18: "eighteenth", 19: "nineteenth", 20: "twentieth"}
num = lambda n: W[n] if n < len(W) else str(n)

def frac(a, b):
    a, b = int(a), int(b)
    if b not in ORD or a > 20: return f"{a} over {b}"
    d = ORD[b] if a == 1 else ("halves" if b == 2 else ORD[b] + "s")
    return f"{num(a)} {d}"

def normalize(text):
    def mixed(m):
        w, a, b = m.groups()
        f = "a half" if (a, b) == ("1", "2") else ("a " + ORD[int(b)] if a == "1" and int(b) in ORD else frac(a, b))
        return f"{num(int(w))} and {f}"
    t = re.sub(r"(?<![:\d])\b(\d+) (\d+)/(\d+)\b(?!/)", mixed, text)
    t = re.sub(r"(?<![/\d])\b(\d+)/(\d+)\b(?!/)", lambda m: frac(*m.groups()), t)
    def ratio_sent(s):
        if "ratio" not in s.lower(): return s
        return re.sub(r"\b(\d+):(\d+)\b(?!\s*(?:[AaPp]\.?[Mm]))", r"\1 to \2", s)
    return "".join(ratio_sent(s) for s in re.split(r"(?<=[.!?])(\s+)", t))

if __name__ == "__main__":
    for s in ["Anis rowed 1/5 times more miles", "small cubes that use 1/2 an ounce", "spends 1/4 and 3/4", "ate 2/5 and 7/13",
              "By midday 2/5 of the people had voted and by 16:00 2/3 of the remaining", "he gave him 1 1/2 times",
              "The ratio of popsicles is 5:6. From 1:00 PM to 5:00 PM.", "is 1:3. At 8:00, 5000 people", "a 3/16 inch bolt"]:
        print(s, "->", normalize(s))
