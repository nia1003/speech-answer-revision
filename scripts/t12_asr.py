"""T1/T2 ASR gate (PREREG_2 sec. 2): Whisper large-v3 (language=en, fp16=False) on every clip and fixed-sentence variant,
plus the reused "Are you sure?" file. norm = lowercase, strip punctuation, drop a/an/the, collapse spaces (asr_evidence_v2);
WER = asr_full_cbx.wer. Fixed: first seed (in tts_jobs order) whose normalized transcript equals the text is chosen.
usage: python t12_asr.py <rq4_v2 dir> <out_dir>"""
import sys, json, re, string, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import numwords
from numwords import words_to_digits
src = open(pathlib.Path(__file__).parent / "asr_full_cbx.py").read()
ns = {"numwords": numwords, "words_to_digits": words_to_digits, "re": re}
exec(src[src.index("EXT = {"):src.index("import whisper")], ns); exec(src[src.index("def prep(s):"):src.index("done = set()")], ns)
wer = ns["wer"]
import whisper
B = pathlib.Path(sys.argv[1]); D = B / sys.argv[2]
def norm(s):
    s = s.lower(); s = "".join(c for c in s if c not in set(string.punctuation)); s = re.sub(r"\b(a|an|the)\b", " ", s); return " ".join(s.split())
model = whisper.load_model("large-v3", device="cuda"); out = open(D / "asr.jsonl", "w"); fixed = {}
AYS = B / "out/stage2_smoke_v3/evidence_audio/unsupported_variants/unsupported_seed20261221.wav"
rows = [dict(name="fixed_ays_seed20261221", kind="fixed", fixed="fixed_ays", text="Are you sure?", path=str(AYS))]
rows += [dict(m, path=str(D / "audio" / f"{m['name']}.wav")) for m in map(json.loads, open(D / "manifest.jsonl"))]
for m in rows:
    hyp = model.transcribe(m["path"], language="en", fp16=False)["text"].strip()
    rec = dict(name=m["name"], kind=m["kind"], item_id=m.get("item_id"), fixed=m.get("fixed"), text=m["text"], path=m["path"], transcript=hyp,
               wer=round(wer(m["text"], hyp), 3), exact=norm(hyp) == norm(m["text"]))
    if m["kind"] == "fixed" and rec["exact"] and m["fixed"] not in fixed: fixed[m["fixed"]] = m["path"]
    out.write(json.dumps(rec, ensure_ascii=False) + "\n"); out.flush(); print(rec["name"], rec["wer"], rec["exact"], flush=True)
json.dump(fixed, open(D / "fixed_choice.json", "w"), indent=1)
print("T12_ASR_DONE fixed chosen:", fixed, flush=True)
