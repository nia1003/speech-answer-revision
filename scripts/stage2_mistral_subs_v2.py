"""Prompt v2 (2026-11-23, after CP_S2_2): candidates must stay consistent with every other detail of the sentence
(locations, gender, aliases/other names, translations, dates, titles, nationality); "NONE" allowed. Mistral still only
proposes; truth is decided by rules + NLI. Original docstring:
Stage 2 smoke v2: Mistral proposes same-type, plausible-looking substitute entities for MuSiQue Invalid evidence
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

Propose up to 5 replacement entities for "{entity}". Each replacement must:
- be the same kind of thing as "{entity}" (a person for a person, a city for a city, a county for a county, a year for a year, an organisation for an organisation, and so on);
- fit every other detail in the sentence, so that the only thing that changes is which entity is named. Check locations (city, county, state, country), gender words (actor/actress, his/her), aliases or other names given for the entity ("also known as ...", translations, abbreviations), dates and eras, titles, and nationality. If the sentence ties "{entity}" to such a detail, the replacement must also fit that detail;
- look plausible to a reader who does not know the facts;
- be a specific real name or value, and not "{entity}" or a variant of it.
If no replacement can fit every detail of the sentence, return {{"candidates": ["NONE"]}}. Do not judge whether the resulting sentence is true.

Return exactly: {{"candidates": ["...", "..."]}}"""
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
