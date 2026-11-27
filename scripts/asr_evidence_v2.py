"""v2 (2026-11-23, after CP_S2_2): GSM8K keys come from the ORIGINAL evidence text (digits) vs the transcript (Whisper
writes digits), so spoken decimals no longer split into two keys; MuSiQue key entity matched fuzzily (difflib ratio >= 0.8
against any same-length word window of the normalized transcript) so sound-alike spellings (Zanuck/Zonick) pass while
missing entities fail. key_ok False -> audio rejected.
--- v1 ---
Stage 2 smoke v2: Whisper large-v3 read-back of the evidence audio. Same number-key rules as asr_full_cbx.py
(prep/keys/wer imported by text, not by executing that file). GSM8K: number keys of the TTS text vs the transcript.
MuSiQue: the key entity (Valid: hop answer; Invalid: substitute) must appear in the normalized transcript; plus WER.
usage: python asr_evidence.py <rq4_v2 dir> <evidence_final.jsonl> <audio_dir>"""
import sys, json, re, string, pathlib, difflib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import numwords
from numwords import words_to_digits
src = open(pathlib.Path(__file__).parent / "asr_full_cbx.py").read()
ns = {"numwords": numwords, "words_to_digits": words_to_digits, "re": re}
exec(src[src.index("EXT = {"):src.index("import whisper")], ns)
exec(src[src.index("def prep(s):"):src.index("done = set()")], ns)
keys, wer = ns["keys"], ns["wer"]
import whisper
B = pathlib.Path(sys.argv[1]); EV = {}; AD = B / sys.argv[3]
for r in map(json.loads, open(B / sys.argv[2])): EV[f"{r['dataset']}_{r['item_id']}_{r['evidence_type']}"] = r
def norm(s):
    s = s.lower(); s = "".join(c for c in s if c not in set(string.punctuation)); s = re.sub(r"\b(a|an|the)\b", " ", s)
    return " ".join(s.split())
model = whisper.load_model("large-v3", device="cuda"); out = open(AD / "asr.jsonl", "w"); n = bad = 0
for m in map(json.loads, open(AD / "manifest.jsonl")):
    hyp = model.transcribe(str(AD / "audio" / f"{m['name']}.wav"), language="en", fp16=False)["text"].strip()
    rec = dict(name=m["name"], secs=m["secs"], tts_text=m["tts_text"], transcript=hyp, wer=round(wer(m["tts_text"], hyp), 3))
    r = EV.get(m["name"])
    if r and r["dataset"] == "gsm8k":
        k1, k2 = keys(r["evidence_text"]), keys(hyp); rec.update(keys_text=k1, keys_heard=k2, key_ok=k1 == k2)
    elif r:
        ent = r["substitute"] if r["evidence_type"] == "invalid" else r["original_step"].rsplit(" -> ", 1)[1]
        e, hw = norm(ent).split(), norm(hyp).split()
        best = max((difflib.SequenceMatcher(None, " ".join(e), " ".join(hw[i:i + len(e)])).ratio() for i in range(max(1, len(hw) - len(e) + 1))), default=0)
        rec.update(key_entity=ent, key_match=round(best, 3), key_ok=best >= 0.8)
    else:
        rec.update(key_ok=norm(hyp) == norm(m["tts_text"]))
    out.write(json.dumps(rec, ensure_ascii=False) + "\n"); out.flush(); n += 1; bad += not rec["key_ok"]
print(f"ASR_EVIDENCE_DONE {n} files, {bad} key mismatches", flush=True)
