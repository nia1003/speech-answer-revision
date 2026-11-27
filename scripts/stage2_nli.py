"""Stage 2 smoke v2: independent NLI check of MuSiQue Invalid evidence (2026-11-23). Model: FacebookAI/roberta-large-mnli
(not Mistral). premise = gold supporting sentence (cleaned), hypothesis = Invalid evidence sentence.
Pass = "CONTRADICTION" is the argmax label. Also runs the reverse direction and records both.
usage: python stage2_nli.py <evidence.jsonl> <out.jsonl>"""
import sys, json, torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
M = "FacebookAI/roberta-large-mnli"
tok = AutoTokenizer.from_pretrained(M); nli = AutoModelForSequenceClassification.from_pretrained(M).cuda().eval()
lab = nli.config.id2label; rev = nli.config._commit_hash
def run(p, h):
    x = tok(p, h, return_tensors="pt", truncation=True, max_length=512).to("cuda")
    with torch.no_grad(): pr = nli(**x).logits.softmax(-1)[0].tolist()
    return {lab[i]: round(v, 4) for i, v in enumerate(pr)}
out = open(sys.argv[2], "w")
for r in map(json.loads, open(sys.argv[1])):
    if r["dataset"] == "musique" and r["evidence_type"] == "invalid" and r.get("evidence_text") and r.get("gold_sentence"):
        f = run(r["gold_sentence"], r["evidence_text"]); b = run(r["evidence_text"], r["gold_sentence"])
        out.write(json.dumps(dict(item_id=r["item_id"], nli_model=M, nli_revision=rev, forward=f, backward=b,
                                  nli_pass=max(f, key=f.get) == "CONTRADICTION"), ensure_ascii=False) + "\n")
print("NLI_DONE", flush=True)
