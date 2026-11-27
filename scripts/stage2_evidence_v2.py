"""v2 (2026-11-23, user decisions on CP_S2_1): resampled smoke 80 (smoke80_v2_ids.jsonl); GSM8K: no wrong_operation when
the gold line describes the operation in words (OPWORDS); MuSiQue Invalid substitute = first candidate proposed by Mistral
(stage2_mistral_subs.py) that passes the truth rules (not the hop answer / final answer / aliases, not in the supporting
paragraphs); Mistral never judges truth, NLI is run afterwards (stage2_nli.py). MuSiQue sentences (Valid and Invalid) are
cleaned of non-Latin script and IPA; if still non-Latin or a table fragment -> rejected and counted.
Without a proposals file, MuSiQue Invalid rows stay "needs_proposal" and the requests are written to <out>/mistral_requests.jsonl.
usage: python3 stage2_evidence_v2.py <out_dir> <ids.jsonl> [mistral_proposals.jsonl]
--- v1 docstring ---
Stage 2 smoke: evidence for the 80 smoke items (2026-11-23). No model calls, no Mistral.
User decisions 2026-11-23:
  - Valid k from Qwen2.5-Omni's first-round outputs; if text and speech give different k, use the smaller one (same
    evidence for both modalities).
  - Evidence text = reference text itself (GSM8K: gold solution line k; MuSiQue: the supporting sentence holding the hop-k
    answer). No LLM rewriting (deviation from the plan's step 3, logged).
Defaults from stage2_smoke_instruction.md (flagged in the report):
  Unsupported = "Are you sure?"
  Valid k  : GSM8K first gold step whose result is not in the model output; MuSiQue first hop whose answer is not in the
             model output. Only for items the model got wrong in that modality.
  Invalid k: uniform 1..h, random.Random(20261123), drawn in smoke80_ids order.
  Invalid GSM8K: wrong operation / wrong previous-result reference / misread question quantity, arithmetic consistent,
             later steps recomputed, final answer must differ. MuSiQue: hop-k bridge entity -> same-type entity.
First-round split: only items where rule and judge agree; truncated / undeterminable / judge_fail excluded.
Outputs: evidence jsonl (one line per item x evidence type) + first-round table.
usage: python3 stage2_evidence.py <out_dir>"""
import sys, json, re, ast, random, string, pathlib, collections, operator
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from numwords import words_to_digits
OUT = pathlib.Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
SEED = 20261123; UNSUPPORTED = "Are you sure?"
ids = [json.loads(l) for l in open(sys.argv[2])]
PROPS = {}
if len(sys.argv) > 3:
    for l in open(sys.argv[3]): r = json.loads(l); PROPS[(r["item_id"], r["k"])] = r
OPWORDS = re.compile(r"\b(half|halves|halved|twice|double|doubled|doubles|triple|tripled|thrice|quarter|quarters|divide|divided|divides|"
                     r"dividing|times|each|per|split|splits|more than|less than|fewer than)\b", re.I)
items = {(x["dataset"], str(x["id"])): x for x in map(json.loads, open("data/full_items.jsonl"))}
gsm_raw = [json.loads(l) for l in open("data/raw/gsm8k_test.jsonl")]
mus_raw = {x["id"]: x for x in map(json.loads, open("data/raw/musique/data/musique_ans_v1.0_dev.jsonl"))}
first = {}
for l in open("out/judge_stage1/judged_qwen25omni.jsonl"):
    r = json.loads(l)
    if r["run"] in ("A_q", "C_q", "A_bc", "C_b"): first[(r["dataset"], str(r["id"]), r["run"][0])] = r

def status(r):
    if r["truncated"] in (True, "True"): return "excluded_truncated"
    if r["verdict"] == "judge_fail" or r["rule_verdict"] == "undeterminable": return "excluded_undeterminable"
    if (r["rule_verdict"] == "correct") != (r["verdict"] == "correct"): return "excluded_rule_judge_disagree"
    return "correct" if r["verdict"] == "correct" else "wrong"

# ---------------- GSM8K ----------------
OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}
def ev(expr):
    def f(n):
        if isinstance(n, ast.Expression): return f(n.body)
        if isinstance(n, ast.BinOp) and type(n.op) in OPS: return OPS[type(n.op)](f(n.left), f(n.right))
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.USub): return -f(n.operand)
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)): return n.value
        raise ValueError(expr)
    return f(ast.parse(expr.replace(",", ""), mode="eval"))
NUMT = re.compile(r"\d+(?:\.\d+)?")
def fmt(v): v = round(v, 6); return str(int(v)) if v == int(v) else str(v)
def feq(a, b): return abs(a - b) < 1e-6
MARK = re.compile(r"<<([^=<>]+)=([^<>]+)>>")
def gsm_steps(sol):
    st = []
    for li, line in enumerate(sol.split("\n")):
        for m in MARK.finditer(line): st.append(dict(line=li, expr=m.group(1), res=float(ev(m.group(2))), span=m.span()))
    return st
def nums_in(text): return [float(x.replace(",", "")) for x in re.findall(r"\d[\d,]*(?:\.\d+)?", text)]
def out_numbers(o):
    s = o.replace("$", "")
    s = re.sub(r"(?<=\d)[ ,](?=\d{3}\b)", "", s)
    return nums_in(s) + nums_in(words_to_digits(s))
def recompute(steps, k, new_expr):
    """steps 1-based k gets new_expr; later steps substitute changed results by value. returns new results list."""
    res = [s["res"] for s in steps]; exprs = [s["expr"] for s in steps]; changed = {}
    exprs[k - 1] = new_expr; nr = ev(new_expr); changed[res[k - 1]] = nr; res2 = res[:]; res2[k - 1] = nr
    for j in range(k, len(steps)):
        toks = NUMT.split(exprs[j].replace(",", "")); nums = NUMT.findall(exprs[j].replace(",", ""))
        new = [fmt(changed[float(t)]) if any(feq(float(t), c) for c in changed) and float(t) in changed else t for t in nums]
        e2 = "".join(a + b for a, b in zip(toks, new + [""]))
        exprs[j] = e2; r = ev(e2)
        if not feq(r, res[j]): changed[res[j]] = r
        res2[j] = r
    return exprs, res2, changed
def gsm_final_new(sol, steps, res2, changed):
    gold = float(sol.split("####")[-1].strip().replace(",", ""))
    if feq(steps[-1]["res"], gold): return res2[-1]
    # final answer comes from an unmarked equation after the last marker: re-evaluate "a op b = c" lines
    for line in sol.split("####")[0].split("\n")[steps[-1]["line"] + 1:]:
        m = re.search(r"([\d$.,+\-*/x ()]+)=\s*\$?([\d,.]+)", line)
        if m and feq(float(m.group(2).replace(",", "").rstrip(".")), gold):
            e = m.group(1).replace("$", "").replace("x", "*").strip()
            nums = NUMT.findall(e.replace(",", "")); toks = NUMT.split(e.replace(",", ""))
            new = [fmt(changed[float(t)]) if float(t) in changed else t for t in nums]
            return ev("".join(a + b for a, b in zip(toks, new + [""])))
    return None
def render_line(sol, step, new_expr=None, new_res=None):
    """gold line with markers removed; for Invalid, operands/operator in the visible text before the marker are replaced."""
    line = sol.split("\n")[step["line"]]; a, b = step["span"]
    pre, post = line[:a], line[b:]
    rm = re.match(r"\$?(\d[\d,]*(?:\.\d+)?|\.\d+)", post)
    if rm and not feq(float(("0" if rm.group(1).startswith(".") else "") + rm.group(1).replace(",", "")), step["res"]): rm = None
    if new_expr is not None:
        old_n = NUMT.findall(step["expr"].replace(",", "")); new_n = NUMT.findall(new_expr.replace(",", ""))
        old_o = re.findall(r"[+\-*/]", step["expr"]); new_o = re.findall(r"[+\-*/]", new_expr)
        # locate the visible operands right-to-left in pre
        pos, end, ok = [], len(pre), True
        for n in reversed(old_n):
            ms = [m for m in re.finditer(r"(?<![\d.])" + re.escape(n) + r"(?![\d])", pre.replace(",", "") if False else pre) if m.end() <= end]
            if not ms: ok = False; break
            pos.append(ms[-1].span()); end = ms[-1].start()
        if not ok: return None
        pos = pos[::-1]; s = list(pre); vis = {"+": "+", "-": "-", "*": "*x×", "/": "/÷"}
        # operator swap: find the visible operator between operand i and i+1
        rep = []
        for i, (o, n2) in enumerate(zip(old_o, new_o)):
            if o != n2 and i + 1 < len(pos):
                seg = pre[pos[i][1]:pos[i + 1][0]]
                m = re.search("[" + re.escape(vis[o]) + "]", seg)
                if not m: return None
                c = pos[i][1] + m.start(); sym = {"+": "+", "-": "-", "*": "x" if seg[m.start()] in "x×" else "*", "/": "/"}[n2]
                rep.append((c, c + 1, sym))
        for (x, y), n in zip(pos, new_n): rep.append((x, y, n))
        for x, y, t in sorted(rep, reverse=True): s[x:y] = list(t)
        pre = "".join(s)
        # the old result may also be stated before the equation ("He will have 31 pens because 25+5+1=31"): replace it there too
        first_op = min(x for x, _, _ in rep) if rep else len(pre)
        head = pre[:first_op]; old_res = fmt(step["res"])
        if old_res not in old_n:   # v2: if the old result is also an operand value, a mention of it is the operand -> leave it
            head = re.sub(r"(?<![\d.])" + re.escape(old_res) + r"(?![\d])", fmt(new_res), head)
        for on, nn in zip(old_n, new_n):   # misread quantity: the sentence must state the misread number too
            if on != nn: head = re.sub(r"(?<![\d.])" + re.escape(on) + r"(?![\d])", nn, head)
        # v2: a result written as a word ("It will take one hour because 60/60=1") cannot be rewritten safely -> reject
        if old_res not in old_n and any(feq(v, step["res"]) for v in nums_in(words_to_digits(re.sub(r"\d[\d,.]*", " ", head)))):
            return None
        pre = head + pre[first_op:]
        res_txt = fmt(new_res)
    else:
        res_txt = fmt(step["res"])
    if rm: post = ("$" if rm.group(0).startswith("$") else "") + res_txt + post[rm.end():]
    else: post = res_txt + post
    return re.sub(r"\s+", " ", (pre + post).replace("$ ", "$")).strip()

def gsm_invalid(i, k, rng):
    sol = gsm_raw[i]["answer"]; q = gsm_raw[i]["question"]; steps = gsm_steps(sol); st = steps[k - 1]
    qn = sorted(set(nums_in(q))); prev = [s["res"] for s in steps[:k - 1]]
    gold = float(sol.split("####")[-1].strip().replace(",", ""))
    types = ["wrong_operation", "wrong_previous_result", "misread_quantity"]; rng.shuffle(types); tried = []
    if OPWORDS.search(sol.split("\n")[st["line"]]):   # the sentence states the operation in words -> no operation swap
        types = [t for t in types if t != "wrong_operation"]; tried.append(("wrong_operation", "skipped_operation_words"))
    e = st["expr"].replace(",", ""); nums = NUMT.findall(e); toks = NUMT.split(e)
    def build(newnums, ops=None):
        s = "".join(a + b for a, b in zip(toks, newnums + [""]))
        if ops: s = "".join(ops.get(j, ch) for j, ch in enumerate(s))
        return s
    for t in types:
        cands = []
        if t == "wrong_operation":
            for j, ch in enumerate(e):
                if ch in "+-*/" and j > 0: cands.append(build(nums, {j: {"+": "-", "-": "+", "*": "/", "/": "*"}[ch]}))
        elif t == "wrong_previous_result":
            for j, n in enumerate(nums):
                if any(feq(float(n), p) for p in prev):
                    for p in prev:
                        if not feq(p, float(n)): nn = nums[:]; nn[j] = fmt(p); cands.append(build(nn))
        else:
            for j, n in enumerate(nums):
                if float(n) in qn and not any(feq(float(n), p) for p in prev):
                    for v in qn:
                        if not feq(v, float(n)): nn = nums[:]; nn[j] = fmt(v); cands.append(build(nn))
        rng.shuffle(cands)
        for ce in cands:
            try:
                nr = ev(ce)
                if feq(nr, st["res"]): continue
                if feq(st["res"], round(st["res"])) and not feq(nr, round(nr)): continue   # keep integer steps integer
                if st["res"] >= 0 and nr < 0: continue
                if not st["res"] or not (0.1 <= abs(nr / st["res"]) <= 10): tried.append((t, "implausible_step_value")); continue
                exprs, res2, changed = recompute(steps, k, ce); fin = gsm_final_new(sol, steps, res2, changed)
            except (ValueError, ZeroDivisionError):
                continue
            if fin is None: tried.append((t, "final_unverifiable")); continue
            if feq(fin, gold): tried.append((t, "final_unchanged")); continue
            if fin < 0 or (feq(gold, round(gold)) and not feq(fin, round(fin))) or not gold or not (0.1 <= abs(fin / gold) <= 10):
                tried.append((t, "implausible_final")); continue
            txt = render_line(sol, st, ce, nr)
            if txt is None: tried.append((t, "render_failed")); continue
            return dict(mutation_type=t, original_step=f"{st['expr']}={fmt(st['res'])}", mutated_step=f"{ce}={fmt(nr)}",
                        mutated_final=fmt(fin), evidence_text=txt, tried=tried)
        tried.append((t, "no_candidate" if not cands else "all_candidates_rejected"))
    return dict(fail=tried)

def gsm_valid_k(i, outs):
    steps = gsm_steps(gsm_raw[i]["answer"]); ks = []
    for o in outs:
        on = out_numbers(o); k = next((j + 1 for j, s in enumerate(steps) if not any(feq(s["res"], v) for v in on)), None)
        if k: ks.append(k)
    return min(ks) if ks else None

# ---------------- MuSiQue ----------------
def norm(s):
    s = s.lower(); s = "".join(c for c in s if c not in set(string.punctuation)); s = re.sub(r"\b(a|an|the)\b", " ", s)
    return " ".join(s.split())
def has(o, a): return bool(norm(a)) and re.search(rf"(?<!\S){re.escape(norm(a))}(?!\S)", norm(o)) is not None
def sents(t): return [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])", t) if s.strip()]
def rel(qd):
    q = qd["question"]
    if ">>" in q: return "rel:" + q.split(">>", 1)[1].strip().lower()
    w = q.strip().lower().split()[0] if q.strip() else ""
    return "wh:" + ("how many" if q.lower().startswith("how many") else w)
def shape(a):
    if re.fullmatch(r"\d{3,4}", a.strip()): return "year"
    if re.search(r"\b(january|february|march|april|may|june|july|august|september|october|november|december)\b", a.lower()) and re.search(r"\d", a): return "date"
    if re.fullmatch(r"[\d,.\s%$]+", a.strip()): return "number"
    return "entity"
LATIN = re.compile(r"^[\u0000-\u024F\u2010-\u206F\u00A0-\u00FF]*$")
def clean(sent):
    """drop parentheses holding non-Latin script or IPA (/.../), collapse spaces; return (text, reject_reason)"""
    t = re.sub(r"\([^()]*[^\u0000-\u024F\u2010-\u206F][^()]*\)", "", sent)
    t = re.sub(r"/[^/]{1,40}/\s*;?", "", t)
    t = re.sub(r"\(\s*[;,]?\s*\)", "", t); t = re.sub(r"\s+", " ", t).replace(" ,", ",").strip()
    if not LATIN.match(t): return t, "non_latin_left"
    toks = t.split(); numeric = sum(bool(re.fullmatch(r"[\d.,()\-–]+", w)) for w in toks)
    if " -- " in t or t.startswith("#") or (len(toks) and numeric / len(toks) > 0.25) or (not re.search(r"[.!?\"'”]$", t) and numeric >= 3):
        return t, "table_fragment"
    return t, None
def hop_sentence(x, k):
    qd = x["question_decomposition"][k - 1]; p = next(p for p in x["paragraphs"] if p["idx"] == qd["paragraph_support_idx"])
    for s in sents(p["paragraph_text"]):
        if qd["answer"].lower() in s.lower():
            t, bad = clean(s)
            if bad: return None, qd, bad
            if qd["answer"].lower() not in t.lower(): return None, qd, "answer_lost_in_cleaning"
            return t, qd, None
    return None, qd, "answer_not_in_support_paragraph"
REQUESTS = []
def mus_invalid(x, k, rng):
    s, qd, bad = hop_sentence(x, k)
    if s is None: return dict(fail=[("entity_substitution", bad)])
    a = qd["answer"]
    golds = {norm(g) for g in [a, x["answer"]] + x["answer_aliases"]}
    sup = " ".join(p["paragraph_text"] for p in x["paragraphs"] if p["is_supporting"]).lower()
    pr = PROPS.get((x["id"], k))
    if pr is None:
        REQUESTS.append(dict(item_id=x["id"], k=k, sentence=s, entity=a, sub_question=qd["question"]))
        return dict(pending=True, gold_sentence=s, entity=a)
    rejected = []
    for c in pr["candidates"]:
        c = c.strip()
        why = ("empty" if not norm(c) else "equals_gold_or_alias" if norm(c) in golds else "in_supporting_paragraphs" if c.lower() in sup
               else "overlaps_original" if norm(a) in norm(c) or norm(c) in norm(a) else None)
        if why: rejected.append((c, why)); continue
        txt = re.sub(r"(?<!\w)" + re.escape(a) + r"(?!\w)", c, s, flags=re.I)
        return dict(mutation_type="entity_substitution", original_step=f"{qd['question']} -> {a}", mutated_step=f"{qd['question']} -> {c}",
                    substitute=c, type_rule="mistral_proposed_same_type", candidates=pr["candidates"], candidates_rejected=rejected,
                    evidence_text=txt, gold_sentence=s, tried=[])
    return dict(fail=[("entity_substitution", "all_mistral_candidates_failed_truth_rules")], candidates_rejected=rejected)
def mus_valid_k(x, outs):
    ks = []
    for o in outs:
        for j, qd in enumerate(x["question_decomposition"]):
            ans = [qd["answer"]] + ([x["answer"]] + x["answer_aliases"] if j == len(x["question_decomposition"]) - 1 else [])
            if not any(has(o, a) for a in ans): ks.append(j + 1); break
    return min(ks) if ks else None

# ---------------- main ----------------
krng = random.Random(SEED); mrng = random.Random(SEED + 1); ev_rows, fr_rows = [], []   # k draws only from krng; mutation choices from mrng
for e in ids:
    ds, iid = e["dataset"], str(e["id"]); it = items[(ds, iid)]; h = it["total_steps"]
    fr = {m: status(first[(ds, iid, m)]) for m in ("A", "C")}
    fr_rows.append(dict(dataset=ds, id=iid, first_round_sampled=e["first_round"], step_bin=e["step_bin"], h=h, first_text=fr["A"], first_speech=fr["C"],
                        out_text=first[(ds, iid, "A")]["raw_output"], out_speech=first[(ds, iid, "C")]["raw_output"]))
    k_inv = krng.randint(1, h)
    base = dict(item_id=iid, dataset=ds, hop_count=h)
    ev_rows.append(dict(base, evidence_type="unsupported", target_hop=None, validity=None, relevance=None, sufficiency=None,
                        mutation_type=None, evidence_text=UNSUPPORTED, verification_status="approved"))
    wrong_outs = [first[(ds, iid, m)]["raw_output"] for m in ("A", "C") if fr[m] == "wrong"]
    if ds == "gsm8k":
        i = int(iid); steps = gsm_steps(gsm_raw[i]["answer"]); assert len(steps) == h, (iid, len(steps), h)
        kv = gsm_valid_k(i, wrong_outs) if wrong_outs else None
        if kv:
            st = steps[kv - 1]; txt = render_line(gsm_raw[i]["answer"], st)
            ev_rows.append(dict(base, evidence_type="valid_corrective", target_hop=kv, validity=True, relevance=True, sufficiency=False,
                                mutation_type=None, source_fact_id=f"step{kv}", original_step=f"{st['expr']}={fmt(st['res'])}",
                                evidence_text=txt, k_rule="first gold step result absent from wrong first-round output(s); min over modalities",
                                verification_status="pending"))
        else:
            ev_rows.append(dict(base, evidence_type="valid_corrective", target_hop=None, verification_status="not_generated",
                                reason="first round not wrong in either modality" if not wrong_outs else "no_k_found"))
        inv = gsm_invalid(i, k_inv, mrng)
    else:
        x = mus_raw[iid]; assert len(x["question_decomposition"]) == h
        kv = mus_valid_k(x, wrong_outs) if wrong_outs else None
        if kv:
            s, qd, bad = hop_sentence(x, kv)
            row = dict(base, evidence_type="valid_corrective", target_hop=kv, validity=True, relevance=True, sufficiency=False,
                       mutation_type=None, source_fact_id=f"support_{qd['paragraph_support_idx']}", original_step=f"{qd['question']} -> {qd['answer']}",
                       evidence_text=s, k_rule="first hop answer absent from wrong first-round output(s); min over modalities",
                       verification_status="pending" if s else "rejected", reason=bad)
            ev_rows.append(row)
        else:
            ev_rows.append(dict(base, evidence_type="valid_corrective", target_hop=None, verification_status="not_generated",
                                reason="first round not wrong in either modality" if not wrong_outs else "no_k_found"))
        inv = mus_invalid(x, k_inv, mrng)
    if "fail" in inv:
        ev_rows.append(dict(base, evidence_type="invalid", target_hop=k_inv, verification_status="rejected", reason=inv["fail"],
                            candidates_rejected=inv.get("candidates_rejected")))
    elif inv.get("pending"):
        ev_rows.append(dict(base, evidence_type="invalid", target_hop=k_inv, verification_status="needs_proposal", gold_sentence=inv["gold_sentence"]))
    else:
        ev_rows.append(dict(base, evidence_type="invalid", target_hop=k_inv, validity=False, relevance=True, sufficiency=False,
                            source_fact_id=f"step{k_inv}" if ds == "gsm8k" else None, verification_status="pending", **inv))
with open(OUT / "smoke80_evidence.jsonl", "w") as f:
    for r in ev_rows: f.write(json.dumps(r, ensure_ascii=False) + "\n")
if REQUESTS:
    with open(OUT / "mistral_requests.jsonl", "w") as f:
        for r in REQUESTS: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("mistral requests", len(REQUESTS))
with open(OUT / "smoke80_first_round_qwen.jsonl", "w") as f:
    for r in fr_rows: f.write(json.dumps(r, ensure_ascii=False) + "\n")
print("evidence rows", len(ev_rows), collections.Counter((r["evidence_type"], r["verification_status"]) for r in ev_rows))
