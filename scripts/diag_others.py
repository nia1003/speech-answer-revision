"""Attention-setting check for the other four models (2026-11-21): which attention implementation each model
actually uses, and whether the same 10 GSM8K text questions show the eager/bf16 artifacts seen in Qwen
(doubled words, leaked next turn, garbled tokens). Text input only, greedy, max_new_tokens 1024, each model's
existing system prompt from rq4_dualcheck/lib.py. No setting is changed.
usage: python diag_others.py <model> <smoke80_items.jsonl> <out.jsonl>   model in kimiaudio|glm4voice|llamaomni2|ultravox"""
import sys, json, re, time, os
import torch
M, src, outp = sys.argv[1], sys.argv[2], sys.argv[3]
BASE = os.path.expanduser("~/rq4_dualcheck"); MAXN = 1024
items = [json.loads(l) for l in open(src) if json.loads(l)["dataset"] == "gsm8k"][:10]

def attn_of(mod):
    seen = {}
    for name, m in mod.named_modules():
        cfg = getattr(m, "config", None)
        a = getattr(cfg, "_attn_implementation", None) if cfg is not None else None
        if a is not None and type(cfg).__name__ not in seen: seen[type(cfg).__name__] = a
    return seen

if M == "kimiaudio":
    sys.path.insert(0, BASE); sys.path.insert(0, BASE + "/repos/Kimi-Audio")
    from kimia_infer.api.kimia import KimiAudio
    model = KimiAudio(model_path="moonshotai/Kimi-Audio-7B-Instruct", load_detokenizer=False)
    SYS = "You are a helpful assistant. Answer the user's question concisely."
    root = getattr(model, "alm", None) or model
    def gen(q):
        _, t = model.generate([{"role": "user", "message_type": "text", "content": SYS},
                               {"role": "user", "message_type": "text", "content": q}],
                              output_type="text", text_temperature=0.0, text_top_k=5, max_new_tokens=MAXN)
        return str(t).strip()
elif M == "glm4voice":
    from transformers import AutoModel, AutoTokenizer
    tok = AutoTokenizer.from_pretrained("THUDM/glm-4-voice-9b", trust_remote_code=True)
    root = AutoModel.from_pretrained("THUDM/glm-4-voice-9b", trust_remote_code=True, torch_dtype=torch.bfloat16, device_map={"": 0}).eval()
    SYS = "User will provide you with a speech instruction. Respond in text only, concisely."
    A_RE, S_RE = re.compile(r"<\|audio_\d+\|>"), re.compile(r"<\|[^|]*\|>")
    def gen(q):
        inp = tok([f"<|system|>\n{SYS}<|user|>\n{q}<|assistant|>\n"], return_tensors="pt").to("cuda")
        eos = [tok.convert_tokens_to_ids("<|user|>")] + ([tok.eos_token_id] if tok.eos_token_id is not None else [])
        o = root.generate(**inp, max_new_tokens=MAXN, do_sample=False, eos_token_id=eos)
        raw = tok.decode(o[0][inp["input_ids"].shape[1]:], skip_special_tokens=False).split("<|user|>")[0]
        return S_RE.sub("", A_RE.sub("", raw)).strip()
elif M == "llamaomni2":
    import whisper
    sys.path.insert(0, BASE + "/repos/LLaMA-Omni2")
    from llama_omni2.model.language_model.omni2_speech_qwen2 import Omni2SpeechQwen2ForCausalLM, Omni2SpeechQwen2Config
    from transformers import AutoTokenizer
    from huggingface_hub import snapshot_download
    path = snapshot_download("ICTNLP/LLaMA-Omni2-7B")
    c = Omni2SpeechQwen2Config.from_pretrained(path)
    c.speech_encoder = whisper._download(whisper._MODELS["large-v3"], BASE + "/whisper_cache", False)
    tok = AutoTokenizer.from_pretrained(path, use_fast=False)
    root = Omni2SpeechQwen2ForCausalLM.from_pretrained(path, config=c, torch_dtype=torch.bfloat16).cuda().eval()
    def gen(q):
        ids = tok.apply_chat_template([{"role": "user", "content": q}], add_generation_prompt=True, return_tensors="pt").cuda()
        o = root.generate(ids, speech=None, speech_lengths=None, do_sample=False, temperature=None, top_p=None, top_k=None,
                          num_beams=1, max_new_tokens=MAXN, use_cache=True, pad_token_id=tok.pad_token_id)
        return tok.batch_decode(o, skip_special_tokens=True)[0].strip()
elif M == "ultravox":
    import transformers
    pipe = transformers.pipeline(model="fixie-ai/ultravox-v0_4", trust_remote_code=True,
                                 model_kwargs={"torch_dtype": torch.bfloat16, "device_map": {"": 0}, **({"attn_implementation": os.environ["ATTN"]} if os.environ.get("ATTN") else {})})
    root, tok = pipe.model.eval(), pipe.tokenizer
    SYS = "You are a helpful assistant. Answer the user's question concisely."
    def gen(q):
        ids = tok.apply_chat_template([{"role": "system", "content": SYS}, {"role": "user", "content": q}],
                                      add_generation_prompt=True, return_tensors="pt").to("cuda")
        o = root.generate(input_ids=ids, attention_mask=torch.ones_like(ids), max_new_tokens=MAXN, do_sample=False, repetition_penalty=1.1)
        return tok.decode(o[0][ids.shape[1]:], skip_special_tokens=True).strip()

print("model", M, "| attention per config class:", attn_of(root) if isinstance(root, torch.nn.Module) else "n/a", flush=True)
f = open(outp, "w")
for it in items:
    t = time.time()
    try:
        with torch.no_grad(): out = gen(it["question"]); err = None
    except Exception as e:
        out, err = "", f"{type(e).__name__}: {e}"[:500]
    flags = dict(other_other=bool(re.search(r"\bother other\b", out)), human=bool(re.search(r"(Human|User):", out)),
                 doubled=len(re.findall(r"\b(\w+) \1\b", out)), garbled=bool(re.search(r"\w't\b(?<!n't)|？", out)))
    f.write(json.dumps(dict(model=M, id=it["id"], answer=it["answer"], output=out, error=err, secs=round(time.time() - t, 2), **flags), ensure_ascii=False) + "\n"); f.flush()
    print(it["id"], flags, err or "", "| tail:", out[-100:].replace("\n", " "), flush=True)
    if err and it is items[0]: break
print("OTHERS_DONE", M, flush=True)
