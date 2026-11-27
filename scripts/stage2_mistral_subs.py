"""Stage 2 smoke v2: Mistral proposes same-type, plausible-looking substitute entities for MuSiQue Invalid evidence
(2026-11-23, user decision (a)). Mistral only PROPOSES candidates; it never judges truth. Truth is decided afterwards
by rules (stage2_evidence_v2.py) and an independent NLI model (stage2_nli.py).
Mistral-Small-24B-Instruct-2501 @ 9527884b, bf16, greedy, max_new_tokens 160, one call per request.
usage: python stage2_mistral_subs.py <mistral_requests.jsonl> <out.jsonl>"""
import sys, os, json, re, torch
from transformers import AutoTokenizer, AutoModelForCausalLM
REPO, REV = "mistralai/Mistral-Small-24B-Instruct-2501", "9527884be6e5616bdd54de542f9ae13384489724"
SYS = "You help build test materials for a reading study. Return one JSON object and nothing else."
TMPL = """Sentence: {sentence}

Entity in the sentence: "{entity}"
The entity is the answer to this sub-question ("#1", "#2" stand for earlier answers): "{sub_question}"

Propose 5 different replacement entities that are the same kind of thing as "{entity}" (a person for a person, a city for a city, a country for a country, a year for a year, an organisation for an organisation, and so on), so that the sentence still reads naturally with the replacement and would look plausible to a reader who does not know the facts. Each must be a specific real name or value, and must not be "{entity}" or a variant of it. Do not judge whether the resulting sentence is true.

Return exactly: {{"candidates": ["...", "...", "...", "...", "..."]}}"""
if os.environ.get("NO_FLASH_SDP"):   # Turing cards (TITAN RTX) cannot run the FlashAttention SDPA kernel; math/mem-efficient kernels instead
    torch.backends.cuda.enable_flash_sdp(False); torch.backends.cuda.enable_mem_efficient_sdp(False)   # math kernel only (bf16 ok)
tok = AutoTokenizer.from_pretrained(REPO, revision=REV)
lm = AutoModelForCausalLM.from_pretrained(REPO, revision=REV, torch_dtype=torch.bfloat16, device_map=os.environ.get("DEVMAP", "auto")).eval()
out = open(sys.argv[2], "w")
for r in map(json.loads, open(sys.argv[1])):
    ids = tok.apply_chat_template([{"role": "system", "content": SYS}, {"role": "user", "content": TMPL.format(**r)}],
                                  add_generation_prompt=True, return_tensors="pt").to(lm.device)
    with torch.no_grad(): o = lm.generate(ids, do_sample=False, max_new_tokens=160, pad_token_id=tok.eos_token_id)
    raw = tok.decode(o[0, ids.shape[1]:], skip_special_tokens=True)
    m = re.search(r"\{.*\}", raw, re.S); cands = []
    try: cands = [str(c) for c in json.loads(m.group(0))["candidates"]] if m else []
    except Exception: pass
    out.write(json.dumps(dict(item_id=r["item_id"], k=r["k"], entity=r["entity"], candidates=cands, raw=raw,
                              model=REPO, revision=REV), ensure_ascii=False) + "\n"); out.flush()
    print(r["item_id"], r["entity"], "->", cands, flush=True)
print("SUBS_DONE", flush=True)
