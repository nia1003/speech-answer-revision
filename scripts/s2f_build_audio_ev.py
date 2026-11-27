"""Formal run: evidence_final_audio file from evidence_final_pass1.jsonl + TTS/ASR results (asr_evidence_v2 key_ok rule:
key_ok False -> verification_status 'audio_rejected', reason asr_key_missing). Unsupported rows -> the smoke-chosen
"Are you sure?" audio (unsupported_variants/unsupported_seed20261221.wav). Rows without audio yet keep their status.
usage: python3 s2f_build_audio_ev.py <asr.jsonl> [more asr.jsonl] -> out/stage2_full_qwen/evidence_final_audio.jsonl"""
import sys, json, collections
D = "out/stage2_full_qwen"
asr = {}
for fp in sys.argv[1:]:
    for l in open(fp): r = json.loads(l); asr[r["name"]] = r
c = collections.Counter(); out = open(f"{D}/evidence_final_audio.jsonl", "w")
for r in map(json.loads, open(f"{D}/evidence_final_pass1.jsonl")):
    if r["evidence_type"] == "unsupported": r["audio"] = "unsupported_variants/unsupported_seed20261221.wav"
    elif r["verification_status"] in ("approved", "rule_passed", "nli_passed"):
        n = f"{r['dataset']}_{r['item_id']}_{r['evidence_type']}"
        if n in asr:
            r["audio"] = f"audio/{n}.wav"; a = asr[n]; r["asr"] = {k: a.get(k) for k in ("transcript", "wer", "key_ok")}
            if not a["key_ok"]: r["verification_status"] = "audio_rejected"; r["reason"] = ["asr_key_missing"]
        else: r["verification_status"] = "audio_pending"
    c[(r["dataset"], r["evidence_type"], r["verification_status"])] += 1
    out.write(json.dumps(r, ensure_ascii=False) + "\n")
for k, v in sorted(c.items()): print(k, v)
