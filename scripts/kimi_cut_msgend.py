"""Kimi-Audio post-processing (DECISION_2026-11-21_kimi_msg_end_cut): cut raw_output at the first <|im_msg_end|>;
truncated = no <|im_msg_end|> and n_new_tokens >= 1024. Writes a new file; input untouched.
usage: python kimi_cut_msgend.py <in.jsonl> <out.jsonl>"""
import sys, json
T = "<|im_msg_end|>"
with open(sys.argv[2], "w") as g:
    for l in open(sys.argv[1]):
        x = json.loads(l); r = x["raw_output"]; cut = T in r
        x["raw_output_uncut"] = r; x["msg_end_cut"] = cut
        if cut: x["raw_output"] = r.split(T)[0].strip()
        x["truncated"] = bool((not cut) and x["n_new_tokens"] >= 1024)
        g.write(json.dumps(x, ensure_ascii=False) + "\n")
