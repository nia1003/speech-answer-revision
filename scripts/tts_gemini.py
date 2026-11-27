"""Gemini TTS for the stage-1 baseline, resumable, with a hard daily request cap.
- Model gemini-2.5-flash-preview-tts, one fixed voice (Kore), raw text only (no reading instruction), 24 kHz 16-bit mono WAV.
- Daily cap: at most 90 requests per Pacific-time day (project quota is 100/day). EVERY HTTP request counts, including
  failures; the ledger (<out>/ledger.jsonl) is the single source of truth. No automatic retry after an error:
  a failed item stays pending for the next run.
- Order (user decision 2026-11-21): batch q80 (smoke 80 question texts) -> para40 (40 MuSiQue paragraph strings)
  -> gsm_frac96 (GSM8K main-analysis questions containing a d/d fraction). A later batch starts only when the
  earlier one is complete.
- Key: read from the file ~/rq4_v2/.gemini_key (first line). Nothing else is used. The key is never printed or written.
- Paragraph string = "\\n\\n".join(f"{title}: {text}") — identical to the text condition (v2 separator rule).
usage: python tts_gemini.py <rq4_v2 dir> [--max N]   (N <= remaining cap for today; default = remaining)"""
import sys, json, time, base64, struct, pathlib, datetime, re, requests
from zoneinfo import ZoneInfo

MODEL, VOICE, SR, CAP = "gemini-2.5-flash-preview-tts", "Kore", 24000, 90
GAP_Q, GAP_PARA = 21.0, 21.0   # free-tier limit is 3 requests/min per model (429 detail 2026-11-21); 7 s / 15 s would exceed it
B = pathlib.Path(sys.argv[1]); OUT = B / "out/tts_gemini"; LED = OUT / "ledger.jsonl"
KEYF = pathlib.Path.home() / "rq4_v2/.gemini_key"
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"

def today_pt(): return datetime.datetime.now(ZoneInfo("America/Los_Angeles")).date().isoformat()
def used_today():
    if not LED.exists(): return 0
    return sum(1 for l in open(LED) if json.loads(l)["pt_date"] == today_pt())

def jobs():
    smoke = [json.loads(l) for l in open(B / "data/smoke80_items.jsonl")]
    q80 = [("q80", f"question/{x['dataset']}_{x['id']}", x["question"]) for x in smoke]
    para = [("para40", f"paragraphs/musique_{x['id']}", "\n\n".join(f"{p['title']}: {p['text']}" for p in x["paragraphs"]))
            for x in smoke if x["dataset"] == "musique"]
    g = [json.loads(l) for l in open(B / "data/raw/gsm8k_test.jsonl")]
    steps = {x["id"]: x for x in map(json.loads, open(B / "out/step_axis/item_steps.jsonl")) if x["dataset"] == "gsm8k"}
    frac = [("gsm_frac96", f"question/gsm8k_{i}", g[i]["question"]) for i in range(len(g))
            if not steps[i]["no_marker"] and re.search(r"\b\d+/\d+\b", g[i]["question"])]
    return q80 + para + frac

def wav(path, pcm):
    hdr = (b"RIFF" + struct.pack("<I", 36 + len(pcm)) + b"WAVEfmt " + struct.pack("<IHHIIHH", 16, 1, 1, SR, SR * 2, 2, 16)
           + b"data" + struct.pack("<I", len(pcm)))
    path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(hdr + pcm)

if __name__ == "__main__":
    if not KEYF.exists(): sys.exit(f"no key file at {KEYF}: not synthesizing")
    key = KEYF.read_text().splitlines()[0].strip()
    OUT.mkdir(parents=True, exist_ok=True)
    left = CAP - used_today()
    want = int(sys.argv[sys.argv.index("--max") + 1]) if "--max" in sys.argv else left
    budget = min(left, want)
    print(f"PT date {today_pt()}: used {CAP - left}/{CAP}, this run may send {budget}", flush=True)
    seen_batches = []; last_sent = 0.0
    for batch, rel, text in jobs():
        path = OUT / f"{rel}.wav"
        if path.exists(): continue
        if seen_batches and batch != seen_batches[-1] and any(not (OUT / f"{r}.wav").exists() for b, r, _ in jobs() if b == seen_batches[-1]):
            print(f"batch {seen_batches[-1]} not complete; not starting {batch}", flush=True); break
        if batch not in seen_batches: seen_batches.append(batch)
        if budget <= 0: print("daily cap reached for this run; stopping", flush=True); break
        body = {"contents": [{"parts": [{"text": text}]}],
                "generationConfig": {"responseModalities": ["AUDIO"],
                                     "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": VOICE}}}}}
        gap = GAP_PARA if batch == "para40" else GAP_Q          # pacing (user 2026-11-21): 7 s questions, 15 s paragraphs
        wait = gap - (time.time() - last_sent)
        if wait > 0: time.sleep(wait)
        t = time.time(); last_sent = t
        try:
            r = requests.post(URL, headers={"x-goog-api-key": key, "Content-Type": "application/json"}, json=body, timeout=300)
            status, err = r.status_code, (None if r.status_code == 200 else r.text)   # full error text (user 2026-11-21)
        except Exception as e:
            status, err, r = -1, f"{type(e).__name__}: {e}", None
        dt = time.time() - t; budget -= 1
        rec = dict(ts_utc=datetime.datetime.utcnow().isoformat(timespec="seconds"), pt_date=today_pt(), batch=batch, item=rel,
                   status=status, error=err, model=MODEL, voice=VOICE, chars=len(text), tts_secs=round(dt, 2))
        if status == 200:
            pcm = base64.b64decode(r.json()["candidates"][0]["content"]["parts"][0]["inlineData"]["data"])
            wav(path, pcm); rec["secs"] = round(len(pcm) / 2 / SR, 2)
        with open(LED, "a") as f: f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(f"{batch} {rel}: HTTP {status} {rec.get('secs', '')}s audio, {dt:.1f}s", flush=True)
        if status != 200:
            print("request failed; stopping this run (no automatic retry)", flush=True); break
    done = sum((OUT / f"{r}.wav").exists() for _, r, _ in jobs())
    print(f"TTS_GEMINI_RUN_END: {done}/{len(jobs())} clips exist; used today {used_today()}/{CAP}", flush=True)
