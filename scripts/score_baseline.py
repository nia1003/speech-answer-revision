"""Rule-based scoring for the stage-1 baseline (plan default, no LLM judge).
GSM8K  : last number in the output (commas and $ removed) == reference final answer (numeric equality).
         No number in the output -> undeterminable.
MuSiQue: SQuAD-style normalization (lowercase, drop punctuation and a/an/the, collapse spaces);
         correct if the normalized answer or any normalized alias occurs in the normalized output as a whole-word span.
         Empty output -> undeterminable.
Truncated outputs are scored like any other output and also counted separately.
usage: python3 score_baseline.py <smoke80_items.jsonl> <baseline.jsonl> <tts_manifest.jsonl> <scored.jsonl>"""
import sys, json, re, string

NUM = re.compile(r"-?\d[\d,]*(?:\.\d+)?")
def last_number(s):
    xs = NUM.findall(s.replace("$", ""))
    return xs[-1].replace(",", "").rstrip(".") if xs else None
def num_eq(a, b):
    try: return abs(float(a) - float(b)) < 1e-6
    except Exception: return False
def norm(s):
    s = s.lower(); s = "".join(c for c in s if c not in set(string.punctuation))
    s = re.sub(r"\b(a|an|the)\b", " ", s); return " ".join(s.split())

items = {(x["dataset"], str(x["id"])): x for x in map(json.loads, open(sys.argv[1]))}
man = {}
for x in map(json.loads, open(sys.argv[3])): man[(x["dataset"], str(x["id"]), x["kind"])] = x
out = open(sys.argv[4], "w")
for r in map(json.loads, open(sys.argv[2])):
    it = items[(r["dataset"], str(r["id"]))]; o = r["raw_output"]
    if r["dataset"] == "gsm8k":
        ext = last_number(o); verdict = "undeterminable" if ext is None else ("correct" if num_eq(ext, it["answer"]) else "incorrect")
    else:
        golds = [it["answer"]] + list(it.get("answer_aliases") or [])
        no = norm(o); hit = next((g for g in golds if norm(g) and re.search(rf"(?<!\S){re.escape(norm(g))}(?!\S)", no)), None)
        ext = hit; verdict = "undeterminable" if not o.strip() else ("correct" if hit else "incorrect")
    qa = man.get((r["dataset"], str(r["id"]), "question"), {}); pa = man.get((r["dataset"], str(r["id"]), "paragraphs"), {})
    audio_secs = qa.get("secs") if r["condition"] == "C" else None
    rec = dict(id=r["id"], dataset=r["dataset"], total_steps=it["total_steps"], parallel_steps=it["parallel_steps"],
               len_q=it["len_q"], question_chars=it["question_chars"], paragraph_chars=it.get("paragraph_chars"),
               audio_secs=audio_secs, paragraph_audio_secs=pa.get("secs") if r["run"] == "C_c" else None,
               condition=r["condition"], run=r["run"], musique_setting=r["musique_setting"], model=r["model"],
               raw_output=o, extracted=ext, verdict=verdict, truncated=r["truncated"], n_new_tokens=r["n_new_tokens"],
               infer_secs=r["infer_secs"], tts_secs=qa.get("tts_secs") if r["condition"] == "C" else None,
               n_audio_tokens=r.get("n_audio_tokens"), audio_input_secs=r.get("audio_input_secs"))
    out.write(json.dumps(rec, ensure_ascii=False) + "\n")
print("scored")
