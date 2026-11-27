"""Formal run pass 2 (2026-11-25): same rule as s2f_build_audio_ev.py, but from evidence_final_pass2.jsonl (MuSiQue Invalid
verified: rules + NLI) and two TTS/ASR dirs: GSM8K clips in evidence_audio/ (audio/<name>.wav) and MuSiQue Invalid clips in
evidence_audio_musinv/ (path written relative to evidence_audio: ../evidence_audio_musinv/audio/<name>.wav).
usage: python3 s2f_build_audio_ev2.py <asr_gsm8k.jsonl> <asr_musinv.jsonl> -> out/stage2_full_qwen/evidence_final_audio_pass2.jsonl"""
import sys, json, os, collections
D = "out/stage2_full_qwen"; OUTF = f"{D}/evidence_final_audio_pass2.jsonl"
assert not os.path.exists(OUTF), "output exists"
asr = {}
for fp, pre in ((sys.argv[1], "audio/"), (sys.argv[2], "../evidence_audio_musinv/audio/")):
    for l in open(fp): r = json.loads(l); assert r["name"] not in asr; asr[r["name"]] = (pre, r)
c = collections.Counter(); out = open(OUTF, "w")
for r in map(json.loads, open(f"{D}/evidence_final_pass2.jsonl")):
    if r["evidence_type"] == "unsupported": r["audio"] = "unsupported_variants/unsupported_seed20261221.wav"
    elif r["verification_status"] in ("approved", "rule_passed", "nli_passed"):
        n = f"{r['dataset']}_{r['item_id']}_{r['evidence_type']}"
        if n in asr:
            pre, a = asr[n]; r["audio"] = f"{pre}{n}.wav"; r["asr"] = {k: a.get(k) for k in ("transcript", "wer", "key_ok")}
            if not a["key_ok"]: r["verification_status"] = "audio_rejected"; r["reason"] = ["asr_key_missing"]
        else: r["verification_status"] = "audio_pending"
    c[(r["dataset"], r["evidence_type"], r["verification_status"])] += 1
    out.write(json.dumps(r, ensure_ascii=False) + "\n")
for k, v in sorted(c.items()): print(k, v)
