"""Stage 1 baseline for LLaMA-Omni2-7B, GLM-4-Voice-9B, Kimi-Audio-7B-Instruct (2026-11-21).
Same runs / inputs / output schema as baseline_qwen_v3.py and baseline_ultravox.py (keep the 5 models consistent):
  GSM8K   : A_q (text question), C_q (audio question)
  MuSiQue : A_a (question only), A_bc (text paragraphs + text q), C_b (text paragraphs + audio q)
Common: greedy, 1024 new TEXT tokens, no repetition penalty, user message = question only (or paragraphs + blank line + question),
official system prompt of each model (none if the official example has none). Attention: sdpa (checked in CP_B7).
Per model:
- llamaomni2 : ICTNLP/LLaMA-Omni2-7B, no system prompt (official infer has none). Audio: whisper.pad_or_trim -> 30 s max, so
               items with question audio > 30 s are NOT run (architecture limit, written to <out>_skipped.jsonl).
- glm4voice  : THUDM/glm-4-voice-9b. Official web_demo prompt format "<|system|>\n{sys}<|user|>\n{input}<|assistant|>streaming_transcription\n",
               official system prompts (speech-instruction variant for audio runs, text-instruction variant for text runs).
               The model answers interleaved (13 text : 26 audio tokens); audio tokens are dropped from the scored text.
               To give the same 1,024 TEXT tokens as the other models, max_new_tokens = 3 x 1024 = 3072 total tokens;
               truncated = hit the limit without <|user|>/eos. Audio input: Whisper-VQ tokens (glm-4-voice-tokenizer).
- kimiaudio  : moonshotai/Kimi-Audio-7B-Instruct via kimia_infer, no system prompt (official example has none),
               text_temperature 0 (greedy), output_type text. kimia_infer's generate() crashes when there is no audio
               (audio_features None is iterated); kimi_generate() below is the same code with that one line guarded.
usage: RUNS=... python baseline_others.py <model> <items.jsonl> <tts_dir> <out.jsonl>   (resumable)"""
import sys, json, time, os, re, pathlib
import torch
M, src, tts, outp = sys.argv[1], sys.argv[2], pathlib.Path(sys.argv[3]), pathlib.Path(sys.argv[4])
BASE = os.path.expanduser("~/rq4_dualcheck"); MAXN = 1024
torch.manual_seed(0)
para_text = lambda it: "\n\n".join(f"{p['title']}: {p['text']}" for p in it["paragraphs"])
SECS = {(x["dataset"], str(x["id"])): x["secs"] for x in map(json.loads, open(tts / "manifest.jsonl"))}

def attn_of(mod):
    seen = {}
    for _, m in mod.named_modules():
        c = getattr(m, "config", None); a = getattr(c, "_attn_implementation", None) if c is not None else None
        if a is not None: seen.setdefault(type(c).__name__, a)
    return seen

if M == "llamaomni2":
    import whisper
    sys.path.insert(0, BASE + "/repos/LLaMA-Omni2")
    from llama_omni2.constants import SPEECH_TOKEN_INDEX, DEFAULT_SPEECH_TOKEN as S
    from llama_omni2.model.language_model.omni2_speech_qwen2 import Omni2SpeechQwen2ForCausalLM, Omni2SpeechQwen2Config
    from transformers import AutoTokenizer
    from huggingface_hub import snapshot_download
    MID = "ICTNLP/LLaMA-Omni2-7B"; path = snapshot_download(MID); REV = pathlib.Path(path).name
    c = Omni2SpeechQwen2Config.from_pretrained(path)
    c.speech_encoder = whisper._download(whisper._MODELS["large-v3"], BASE + "/whisper_cache", False)
    tok = AutoTokenizer.from_pretrained(path, use_fast=False)
    model = Omni2SpeechQwen2ForCausalLM.from_pretrained(path, config=c, torch_dtype=torch.bfloat16).cuda().eval()
    sid = tok.convert_tokens_to_ids(S); EOS = {tok.eos_token_id, tok.pad_token_id, tok.convert_tokens_to_ids("<|im_end|>")}
    # LONG_MODE (added 11-22, supplementary runs for the 5 GSM8K items with audio > 30 s; default "skip" = main run):
    #   skip  : items > 30 s are not run (written to _skipped)
    #   trim  : official preprocessing as is (whisper.pad_or_trim keeps the first 30 s)
    #   chunk : audio split into 30 s pieces, each padded and encoded separately, inserted as consecutive speech segments
    LONG_MODE = os.environ.get("LONG_MODE", "skip")
    AUDIO_MAX = 30.0 if LONG_MODE == "skip" else None; AUDIO_TAG = S
    @torch.inference_mode()
    def run(user_text, audio_path):
        kw = {}; n_seg = 0
        if audio_path:
            wav_ = whisper.load_audio(audio_path); N = whisper.audio.N_SAMPLES
            segs = [wav_[i:i + N] for i in range(0, len(wav_), N)] if LONG_MODE == "chunk" else [wav_]
            mels = [whisper.log_mel_spectrogram(whisper.pad_or_trim(s), n_mels=128).permute(1, 0) for s in segs]
            n_seg = len(mels); user_text = user_text.replace(S, S * n_seg)
            kw = dict(speech=torch.stack(mels).to("cuda", torch.bfloat16), speech_lengths=torch.LongTensor([m.shape[0] for m in mels]).cuda())
        ids = tok.apply_chat_template([{"role": "user", "content": user_text}], add_generation_prompt=True, return_tensors="pt")[0]
        ids[ids == sid] = SPEECH_TOKEN_INDEX
        assert int((ids == SPEECH_TOKEN_INDEX).sum()) == n_seg
        t = time.time()
        o = model.generate(ids.unsqueeze(0).cuda(), do_sample=False, temperature=None, top_p=None, top_k=None, num_beams=1,
                           max_new_tokens=MAXN, use_cache=True, pad_token_id=tok.pad_token_id, **kw)
        torch.cuda.synchronize(); dt = time.time() - t
        gen = o[0]
        return dict(raw_output=tok.decode(gen, skip_special_tokens=True).strip(), infer_secs=round(dt, 2), n_new_tokens=int(len(gen)),
                    truncated=bool(len(gen) >= MAXN and int(gen[-1]) not in EOS), n_input_tokens=int(len(ids)))
    root = model

elif M == "glm4voice":
    sys.path.insert(0, BASE + "/repos/GLM-4-Voice")
    import transformers
    from transformers import AutoModel, AutoTokenizer, WhisperFeatureExtractor
    from speech_tokenizer.modeling_whisper import WhisperVQEncoder
    from speech_tokenizer.utils import extract_speech_token
    import torchaudio, functools   # sox backend segfaults on this cluster; read the same WAV via soundfile
    torchaudio.load = functools.partial(torchaudio.load, backend="soundfile")
    MID = "THUDM/glm-4-voice-9b"; TK = "THUDM/glm-4-voice-tokenizer"
    tok = AutoTokenizer.from_pretrained(MID, trust_remote_code=True)
    model = AutoModel.from_pretrained(MID, trust_remote_code=True, torch_dtype=torch.bfloat16, device_map={"": 0}).eval()
    REV = getattr(model.config, "_commit_hash", None)
    wm = WhisperVQEncoder.from_pretrained(TK).eval().to("cuda"); fe = WhisperFeatureExtractor.from_pretrained(TK)
    SYS_SPEECH = ("User will provide you with a speech instruction. Do it step by step. First, think about the instruction and "
                  "respond in a interleaved manner, with 13 text token followed by 26 audio tokens. ")
    SYS_TEXT = ("User will provide you with a text instruction. Do it step by step. First, think about the instruction and "
                "respond in a interleaved manner, with 13 text token followed by 26 audio tokens.")
    A_RE, S_RE = re.compile(r"<\|audio_\d+\|>"), re.compile(r"<\|[^|]*\|>")
    AUDIO_MAX = None; AUDIO_TAG = "<AUDIO>"
    AUD0 = tok.convert_tokens_to_ids("<|audio_0|>")
    END = [tok.convert_tokens_to_ids("<|user|>")] + ([tok.eos_token_id] if tok.eos_token_id is not None else [])
    # fix 11-22 (speed): official format is 13 text tokens then 26 audio tokens; in the v1 smoke every audio run inside
    # the text was exactly 26 tokens. A run of >= 78 audio tokens means the text stream has ended, so stop there:
    # under greedy decoding the text before that point is identical to running on to <|user|>.
    GLM_AUDIO_STOP = 78
    def _audio_run(ids):
        n = 0
        for x in reversed(ids):
            if x >= AUD0: n += 1
            else: break
        return n
    class GlmTextDone(transformers.StoppingCriteria):
        def __init__(self, n_in): self.n_in = n_in
        def __call__(self, input_ids, scores, **kw):
            return _audio_run(input_ids[0, self.n_in:].tolist()) >= GLM_AUDIO_STOP
    @torch.inference_mode()
    def run(user_text, audio_path):
        if audio_path:
            t_ = extract_speech_token(wm, fe, [audio_path])[0]
            user_text = user_text.replace(AUDIO_TAG, "<|begin_of_audio|>" + "".join(f"<|audio_{x}|>" for x in t_) + "<|end_of_audio|>")
        prompt = f"<|system|>\n{SYS_SPEECH if audio_path else SYS_TEXT}<|user|>\n{user_text}<|assistant|>streaming_transcription\n"
        inp = tok([prompt], return_tensors="pt").to("cuda"); n_in = int(inp["input_ids"].shape[1])
        t = time.time()
        o = model.generate(**inp, max_new_tokens=3 * MAXN, do_sample=False, eos_token_id=END,
                           stopping_criteria=transformers.StoppingCriteriaList([GlmTextDone(n_in)]))
        torch.cuda.synchronize(); dt = time.time() - t
        gen = o[0][n_in:].tolist()
        if any(x in END for x in gen): gen_t = gen[:min(gen.index(x) for x in END if x in gen)]
        else: gen_t = gen
        text_ids = [x for x in gen_t if x < AUD0]   # fix 11-22: decode text tokens only (v1 decoded audio too -> words split by blanks)
        done = (len(gen) < 3 * MAXN) or (gen[-1] in END) or (_audio_run(gen) >= GLM_AUDIO_STOP)
        return dict(raw_output=S_RE.sub("", tok.decode(text_ids, skip_special_tokens=False)).strip(), infer_secs=round(dt, 2),
                    n_new_tokens=len(text_ids), n_new_tokens_total=len(gen), truncated=bool(not done), n_input_tokens=n_in)
    root = model

elif M == "kimiaudio":
    sys.path.insert(0, BASE); sys.path.insert(0, BASE + "/repos/Kimi-Audio")
    from kimia_infer.api.kimia import KimiAudio
    MID = "moonshotai/Kimi-Audio-7B-Instruct"
    km = KimiAudio(model_path=MID, load_detokenizer=False); REV = getattr(km.alm.config, "_commit_hash", None)
    AUDIO_MAX = None; AUDIO_TAG = None
    @torch.inference_mode()
    def kimi_generate(chats):
        h = km.prompt_manager.get_prompt(chats, output_type="text")
        a_ids, t_ids, mask, _, _ = h.to_tensor()
        feats = h.continuous_feature
        feats = [f.to(torch.cuda.current_device()) for f in feats] if len(feats) else None   # the one guarded line
        dev = torch.cuda.current_device()
        wav_t, txt_t = km._generate_loop(audio_input_ids=a_ids.to(dev), text_input_ids=t_ids.to(dev), max_new_tokens=MAXN,
                                         audio_temperature=0.0, audio_top_k=5, audio_repetition_penalty=1.0, audio_repetition_window_size=64,
                                         text_top_k=5, text_temperature=0.0, text_repetition_penalty=1.0, text_repetition_window_size=16,
                                         is_continuous_mask=mask.to(dev), continous_feature=feats, output_type="text")
        txt_t = [x for x in txt_t if x < km.kimia_token_offset]
        return km.detokenize_text(txt_t), len(txt_t), int(a_ids.shape[1])
    def run(user_text, audio_path, para=None):
        chats = []
        if para is not None: chats.append({"role": "user", "message_type": "text", "content": para})
        chats.append({"role": "user", "message_type": "audio", "content": audio_path} if audio_path else
                     {"role": "user", "message_type": "text", "content": user_text})
        t = time.time(); txt, n, n_in = kimi_generate(chats); torch.cuda.synchronize(); dt = time.time() - t
        return dict(raw_output=str(txt).strip(), infer_secs=round(dt, 2), n_new_tokens=n, truncated=bool(n >= MAXN), n_input_tokens=n_in)
    root = km.alm
else:
    raise SystemExit(f"unknown model {M}")

print("model", M, MID, "| revision", REV, "| attention:", attn_of(root), flush=True)
RUNS = set(os.environ["RUNS"].split(",")) if os.environ.get("RUNS") else None
ONLY = set(os.environ["ONLY_IDS"].split(",")) if os.environ.get("ONLY_IDS") else None
wav = lambda it: str(tts / "question" / f"{it['dataset']}_{it['id']}.wav")
items = [json.loads(l) for l in open(src)]
done = set()
if outp.exists():
    for l in open(outp): x = json.loads(l); done.add((x["dataset"], str(x["id"]), x["run"]))
f = open(outp, "a"); skipf = open(outp.with_name(outp.stem + "_skipped.jsonl"), "a")
for it in items:
    q = it["question"]; key = (it["dataset"], str(it["id"]))
    if M == "kimiaudio":   # Kimi: paragraphs and audio question as two user messages
        runs = [("A_q", "A", "-", (q, None, None)), ("C_q", "C", "-", (None, wav(it), None))]
        if it["dataset"] == "musique":
            p = para_text(it)
            runs = [("A_a", "A", "a", (q, None, None)), ("A_bc", "A", "b/c", (p + "\n\n" + q, None, None)), ("C_b", "C", "b", (None, wav(it), p))]
    else:
        runs = [("A_q", "A", "-", (q, None)), ("C_q", "C", "-", (AUDIO_TAG, wav(it)))]
        if it["dataset"] == "musique":
            p = para_text(it) + "\n\n"
            runs = [("A_a", "A", "a", (q, None)), ("A_bc", "A", "b/c", (p + q, None)), ("C_b", "C", "b", (p + AUDIO_TAG, wav(it)))]
    for name, cond, setting, args in runs:
        if key + (name,) in done: continue
        if RUNS and name not in RUNS: continue
        if ONLY and str(it["id"]) not in ONLY: continue
        if cond == "C" and AUDIO_MAX and SECS[key] > AUDIO_MAX:
            skipf.write(json.dumps(dict(dataset=it["dataset"], id=it["id"], run=name, audio_secs=SECS[key],
                                        reason=f"question audio > {AUDIO_MAX}s; model trims audio to 30 s (architecture limit)")) + "\n")
            skipf.flush(); print(f"{key} {name}: SKIPPED audio {SECS[key]}s", flush=True); continue
        r = run(*args)
        rec = dict(dataset=it["dataset"], id=it["id"], run=name, condition=cond, musique_setting=setting, model=MID, revision=REV,
                   audio_secs=SECS[key] if cond == "C" else None, **r)
        f.write(json.dumps(rec, ensure_ascii=False) + "\n"); f.flush()
        print(f"{it['dataset']}_{it['id']} {name}: {r['n_new_tokens']} tok {r['infer_secs']}s trunc={r['truncated']}", flush=True)
print("BASELINE_DONE", M, flush=True)
