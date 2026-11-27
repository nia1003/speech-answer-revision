"""Read-only follow-ups requested 2026-11-21 (no data or results are modified; new files only).
(1) A_bc and C_b on the same 37 MuSiQue items that C_c has, next to C_c.
(2) Paired text-vs-audio counts: both correct / text only / audio only / both wrong.
(3) GSM8K main 1,301: items containing both '$' and '/'; ASR spot-check recomputed after converting English number words to digits.
usage: python3 readonly_extra.py <rq4_v2 dir>"""
import sys, json, re, pathlib, statistics as st
B = pathlib.Path(sys.argv[1]); D = B / "out/smoke80"
S = [json.loads(l) for l in open(D / "scored.jsonl")]
v = {(str(x["id"]), x["run"]): x["verdict"] == "correct" for x in S}
cc_ids = sorted({str(x["id"]) for x in S if x["run"] == "C_c"})
print(f"(1) 同一批 {len(cc_ids)} 題 MuSiQue")
for r in ("A_bc", "C_b", "C_c"):
    print(f"   {r}: {sum(v[(i, r)] for i in cc_ids)}/{len(cc_ids)}")

def pair(a, b, ids, lab):
    c = {"都對": 0, "只有文字對": 0, "只有語音對": 0, "都錯": 0}
    for i in ids:
        x, y = v[(i, a)], v[(i, b)]
        c["都對" if x and y else "只有文字對" if x else "只有語音對" if y else "都錯"] += 1
    print(f"   {lab}（{a} vs {b}，n={len(ids)}）: " + "、".join(f"{k} {n}" for k, n in c.items()))
g_ids = sorted({str(x["id"]) for x in S if x["dataset"] == "gsm8k"}); m_ids = sorted({str(x["id"]) for x in S if x["dataset"] == "musique"})
print("(2) 文字對語音的成對計數")
pair("A_q", "C_q", g_ids, "GSM8K")
pair("A_a", "C_a", m_ids, "MuSiQue (a)")
pair("A_bc", "C_b", m_ids, "MuSiQue (b)")
pair("A_bc", "C_c", cc_ids, "MuSiQue (c)")

g = [json.loads(l) for l in open(B / "data/raw/gsm8k_test.jsonl")]
steps = {x["id"]: x for x in map(json.loads, open(B / "out/step_axis/item_steps.jsonl")) if x["dataset"] == "gsm8k"}
main = [i for i in range(len(g)) if not steps[i]["no_marker"]]
both = [i for i in main if "$" in g[i]["question"] and "/" in g[i]["question"]]
frac_after_dollar = [i for i in both if re.search(r"\$\s*\d[\d,.]*[^.?!]*?\b\d+/\d+\b", g[i]["question"])]
FRAC = re.compile(r"\d+/\d+")
n_frac = sum(bool(FRAC.search(g[i]["question"])) for i in both)
print(f"(3a) GSM8K 主分析 {len(main)} 題中，題目同時含 $ 和 / 的：{len(both)} 題；其中 / 是分數（數字/數字）的：{n_frac} 題")
print("     題號：", both)

ONES = {w: i for i, w in enumerate("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split())}
TENS = {w: 10 * i for i, w in enumerate("_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()) if w != "_"}
def words_to_digits(s):
    toks = re.findall(r"[A-Za-z]+|[^A-Za-z]+", s); out, buf = [], None
    def flush():
        nonlocal buf
        if buf is not None: out.append(str(buf[0] + buf[1])); buf = None
    for t in toks:
        w = t.lower()
        if w in ONES or w in TENS or w in ("hundred", "thousand"):
            if buf is None: buf = [0, 0]
            if w in ONES: buf[1] += ONES[w]
            elif w in TENS: buf[1] += TENS[w]
            elif w == "hundred": buf[1] = max(buf[1], 1) * 100
            else: buf[0] += max(buf[1], 1) * 1000; buf[1] = 0
        elif buf is not None and re.fullmatch(r"[ -]+", t) : continue
        else: flush(); out.append(t)
    flush(); return "".join(out)
keys = lambda s: re.findall(r"\$?\d+(?:\.\d+)?%?|\$|%", s.replace(",", ""))
A = [json.loads(l) for l in open(D / "asr_check_gsm8k40.jsonl")]
res = []
for a in A:
    k1, k2 = keys(words_to_digits(a["question"])), keys(words_to_digits(a["transcript"]))
    res.append(dict(id=a["id"], keys_text=k1, keys_heard=k2, match=k1 == k2, transcript_digits=words_to_digits(a["transcript"])))
with open(D / "asr_check_gsm8k40_wordnum.jsonl", "w") as f:
    for r in res: f.write(json.dumps(r, ensure_ascii=False) + "\n")
bad = [r for r in res if not r["match"]]
print(f"(3b) 英文數字詞轉回數字後，40 題中 {len(bad)} 題的數字／$／% 列表仍不同（新檔 asr_check_gsm8k40_wordnum.jsonl，原檔未改）")
for r in bad: print(f"     {r['id']}: 原文 {r['keys_text']} | 聽到 {r['keys_heard']}")
