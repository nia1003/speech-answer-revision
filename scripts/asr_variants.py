"""Whisper large-v3 transcripts of the Unsupported variants; picks the first exact "are you sure". usage: python asr_variants.py <out_dir>"""
import sys, json, re, pathlib, whisper
D = pathlib.Path(sys.argv[1]) / "unsupported_variants"; model = whisper.load_model("large-v3", device="cuda"); res = []
for p in sorted(D.glob("*.wav")):
    t = model.transcribe(str(p), language="en", fp16=False)["text"].strip(); res.append(dict(file=p.name, transcript=t, exact=re.sub(r"[^a-z ]", "", t.lower()).strip() == "are you sure"))
    print(res[-1], flush=True)
ch = next((r["file"] for r in res if r["exact"]), None)
json.dump(dict(variants=res, chosen=ch), open(D / "choice.json", "w"), indent=1); print("CHOSEN", ch, flush=True)
