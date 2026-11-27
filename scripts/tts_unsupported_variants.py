"""Re-synthesize the shared Unsupported line "Are you sure?" (2026-11-23, after CP_S2_2: the stage-2 v2 audio was heard
as "You sure?"). Same Chatterbox settings; seeds SEED+100+j, j=0..4 (5 variants, all kept); Whisper large-v3 transcript
of each is written by asr step; the first variant whose normalized transcript is exactly "are you sure" is chosen.
usage: python tts_unsupported_variants.py <out_dir>"""
import sys, json, pathlib, numpy as np, soundfile as sf, torch
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from tts_chatterbox import SEED
from chatterbox.tts import ChatterboxTTS
OUT = pathlib.Path(sys.argv[1]) / "unsupported_variants"; OUT.mkdir(parents=True, exist_ok=True)
model = ChatterboxTTS.from_pretrained(device="cuda"); SR = model.sr
for j in range(5):
    torch.manual_seed(SEED + 100 + j)
    with torch.inference_mode(): w = model.generate("Are you sure?", exaggeration=0.5, cfg_weight=0.5, temperature=0.8)
    a = w.squeeze(0).float().cpu().numpy(); sf.write(OUT / f"unsupported_seed{SEED + 100 + j}.wav", a, SR)
    print(j, round(len(a) / SR, 2), flush=True)
print("VARIANTS_DONE", flush=True)
