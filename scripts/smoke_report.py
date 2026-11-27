"""Aggregate the smoke-80 baseline: raw per-run table (CSV) + computed numbers printed as markdown.
usage: python3 smoke_report.py <smoke_dir>   (smoke_dir has scored.jsonl, baseline_*_skipped.jsonl, asr_check_gsm8k40.jsonl, tts_smoke80/manifest.jsonl)"""
import sys, json, csv, statistics as st, pathlib
from collections import Counter, defaultdict
D = pathlib.Path(sys.argv[1])
S = [json.loads(l) for l in open(D / "scored.jsonl")]
skip = [json.loads(l) for l in open(D / "baseline_smoke80_qwen25omni_skipped.jsonl")] if (D / "baseline_smoke80_qwen25omni_skipped.jsonl").exists() else []
man = [json.loads(l) for l in open(D / "tts_smoke80/manifest.jsonl")]
asr = [json.loads(l) for l in open(D / "asr_check_gsm8k40.jsonl")]

cols = ["id", "dataset", "total_steps", "parallel_steps", "len_q", "question_chars", "paragraph_chars", "audio_secs",
        "paragraph_audio_secs", "condition", "run", "musique_setting", "extracted", "verdict", "truncated", "n_new_tokens",
        "infer_secs", "tts_secs", "raw_output"]
with open(D / "smoke80_raw_table.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore"); w.writeheader(); [w.writerow(r) for r in S]
print(f"raw table: {D/'smoke80_raw_table.csv'} ({len(S)} rows); skipped runs: {len(skip)}")
for s in skip: print("  skipped", s["id"], s["run"], s["paragraph_audio_secs"], "s")

order = ["A_q", "C_q", "A_a", "C_a", "A_bc", "C_b", "C_c"]
runs = [r for r in order if any(x["run"] == r for x in S)]
print("\n| 資料集 | run | n | 答對 | 答錯 | 無法判定 | 抽取成功率 | 截斷 |\n|---|---|---|---|---|---|---|---|")
for ds in ("gsm8k", "musique"):
    for r in runs:
        g = [x for x in S if x["dataset"] == ds and x["run"] == r]
        if not g: continue
        c = Counter(x["verdict"] for x in g)
        print(f"| {ds} | {r} | {len(g)} | {c['correct']} | {c['incorrect']} | {c['undeterminable']} | "
              f"{(len(g)-c['undeterminable'])/len(g):.3f} | {sum(x['truncated'] for x in g)} |")

def by(key, ds):
    vals = sorted({x[key] for x in S if x["dataset"] == ds})
    print(f"\n{ds}：依 {key} 的答對數／題數\n| run | " + " | ".join(str(v) for v in vals) + " |\n|---|" + "---|" * len(vals))
    for r in runs:
        g = [x for x in S if x["dataset"] == ds and x["run"] == r]
        if not g: continue
        cells = []
        for v in vals:
            h = [x for x in g if x[key] == v]; cells.append(f"{sum(x['verdict']=='correct' for x in h)}/{len(h)}")
        print(f"| {r} | " + " | ".join(cells) + " |")
for ds in ("gsm8k", "musique"):
    by("total_steps", ds); by("len_q", ds)

print("\n耗時（秒，平均／中位數）")
for r in runs:
    t = [x["infer_secs"] for x in S if x["run"] == r]
    print(f"  推論 {r}: n={len(t)} mean {st.mean(t):.2f} median {st.median(t):.2f} max {max(t):.2f}")
tq = [m["tts_secs"] for m in man if m["kind"] == "question"]; tp = [m["tts_secs"] for m in man if m["kind"] == "paragraphs"]
aq = [m["secs"] for m in man if m["kind"] == "question"]; ap = [m["secs"] for m in man if m["kind"] == "paragraphs"]
print(f"  TTS 題目: n={len(tq)} mean {st.mean(tq):.2f}s（音訊 mean {st.mean(aq):.2f}s）；TTS 段落: n={len(tp)} mean {st.mean(tp):.2f}s（音訊 mean {st.mean(ap):.2f}s）")

def mean_run(names, ds=None):
    t = [x["infer_secs"] for x in S if x["run"] in names and (ds is None or x["dataset"] == ds)]
    return st.mean(t) if t else float("nan")
g_item = mean_run(["A_q", "C_q"], "gsm8k"); m_a = mean_run(["A_a", "C_a"]); m_bc = mean_run(["A_bc", "C_b", "C_c"])
per_a = (1319 * g_item + 2417 * m_a) / 3736; per_bc = (1319 * g_item + 2417 * m_bc) / 3736
print("\n全量估算（每題推論耗時 × 3,736 × 5 模型 × 2 條件；以 Qwen2.5-Omni-7B 在 2×3090 的耗時代替所有模型）")
for lab, per in (("MuSiQue 用 (a)", per_a), ("MuSiQue 用 (b)/(c)", per_bc)):
    tot = per * 3736 * 5 * 2
    print(f"  {lab}: 每題 {per:.2f}s → {tot/3600:.1f} GPU 小時（單卡串行）")
print(f"  TTS 一次性：題目 3,736 × {st.mean(tq):.2f}s = {3736*st.mean(tq)/3600:.2f} 小時；若用 (c) 再加段落 2,417 × {st.mean(tp):.2f}s = {2417*st.mean(tp)/3600:.2f} 小時（CPU）")

print("\nGSM8K 數字／$／% 抽查（Whisper large-v3；原文與轉寫的數字符號不同的題）")
diff = [a for a in asr if a["keys_text"] != a["keys_heard"]]
print(f"  40 題中 {len(diff)} 題不同；WER 中位數 {st.median(a['wer'] for a in asr):.3f}，最大 {max(a['wer'] for a in asr):.3f}")
for a in diff: print(f"  {a['id']}: 原文 {a['keys_text']} | 聽到 {a['keys_heard']}")
