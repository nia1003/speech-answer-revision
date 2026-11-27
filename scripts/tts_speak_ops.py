"""Stage 2 evidence only (2026-11-23): speak arithmetic operators before tts_textnorm_v4 (stage-1 questions had almost
no equations, evidence lines are equations). Between numbers (optional $ and spaces): * or x/X/× -> times, = -> equals,
+ -> plus, - or – -> minus, / -> divided by, except a compact a/b with a < b <= 20 and no spaces (a fraction like 1/4,
left to textnorm). % left to textnorm."""
import re
N = r"\$?\d[\d,]*(?:\.\d+)?|\.\d+"
def speak_ops(t):
    t = re.sub(rf"(?<=[\d)])\s*[*×]\s*(?=[\d$(.])", " times ", t)
    t = re.sub(rf"(?<=\d)\s+[xX]\s+(?=[\d$(])", " times ", t)
    t = re.sub(rf"(?<=[\d)%])\s*=\s*", " equals ", t)
    t = re.sub(rf"(?<=[\d)%])\s*\+\s*(?=[\d$(.])", " plus ", t)
    t = re.sub(rf"(?<=[\d)%])\s*[-–]\s*(?=[\d$(.])", " minus ", t)
    def div(m):
        a, sp1, sp2, b = m.group(1), m.group(2), m.group(3), m.group(4)
        try:
            if not sp1 and not sp2 and "$" not in a + b and float(a) < float(b) <= 20 and float(a) == int(float(a)): return m.group(0)
        except ValueError: pass
        return f"{a} divided by {b}"
    t = re.sub(rf"({N})(\s*)/(\s*)({N})", div, t)
    return re.sub(r"\s+", " ", t).strip()

def speak_ops_after(t):
    """second pass after tts_textnorm_v4 (numbers already words): leftover symbols between words."""
    t = re.sub(r"\s*=\s*", " equals ", t)
    t = re.sub(r"\s*[*×]\s*", " times ", t)
    t = re.sub(r"(?<=\s)[xX](?=\s)", "times", t)
    t = re.sub(r"\s+\+\s+|(?<=[a-z])\+(?=[a-z\s])", " plus ", t)
    t = re.sub(r"(?<=\s)[-–](?=\s)", "minus", t)
    t = re.sub(r"(?<=[a-z])/(?=[a-z])", " per ", t)
    t = t.replace(":", ": ")
    return re.sub(r"\s+", " ", t).strip()
def speak(t, normalize):
    return speak_ops_after(normalize(speak_ops(t)))
