#!/bin/bash
# Formal run (user 2026-11-25 "跑完直接開 judge"): wait for MuSiQue Invalid speech shards -> pull + check all outputs ->
# judge inputs -> judge_correct_v2, extract_v1, stance_v1 on 3x3090 (qos normal, DEVMAP=auto, TOK_BUDGET=12000, 1 shard each;
# same as T1/T2 412618-412620) -> pull -> parse-failure check (<= 1% each). No metrics here.
cd $PROJECT_DIR; R=$REMOTE_HOST; D=out/stage2_full_qwen; J=$D/judge; FP=$D/final_pull
waitlog () { while true; do f=$(ssh -o ConnectTimeout=20 $R "grep -l 'Traceback\|JOB_END\|abort\|OutOfMemory\|CANCELLED\|DUE TO' ~/rq4_v2/logs/$1 2>/dev/null" 2>/dev/null); if [ -n "$f" ]; then ssh -o ConnectTimeout=20 $R "grep -c JOB_END ~/rq4_v2/logs/$1"; return; fi; sleep 60; done; }
for i in 0 1 2; do r=$(waitlog s2f_r23_speech${i}_musinv.log); [ "$r" = "1" ] || { echo "SPEECH MUSINV $i FAILED"; exit 1; }; done
echo "SPEECH_DONE $(date)"
for i in 0 1 2; do [ -e $FP/round23_qwen_speech_shard$i.jsonl ] && { echo "speech pull EXISTS"; exit 1; }; scp -q ${R}:rq4_v2/$D/round23_qwen_speech_shard$i.jsonl $FP/ || exit 1; done
python3 scripts/s2f_check_runs.py text $FP/round23_qwen_text_shard{0,1,2}.jsonl || { echo "TEXT CHECK FAILED"; exit 1; }
python3 scripts/s2f_check_runs.py speech $FP/round23_qwen_speech_shard{0,1,2}.jsonl || { echo "SPEECH CHECK FAILED"; exit 1; }
python3 scripts/s2f_judge_inputs.py $J $FP/round23_qwen_text_shard{0,1,2}.jsonl $FP/round23_qwen_speech_shard{0,1,2}.jsonl || { echo "JUDGE INPUT FAILED"; exit 1; }
ssh $R "cd ~/rq4_v2; [ -e $J ] && exit 1; for l in s2f_jc s2f_je s2f_js; do [ -e logs/\$l.log ] && exit 1; done; mkdir -p $J" || { echo "JUDGE TARGET EXISTS on cluster"; exit 1; }
scp -q $J/correct_input.jsonl $J/extract_input.jsonl $J/stance_input.jsonl ${R}:rq4_v2/$J/ || exit 1
ssh $R "cd ~/rq4_v2; F='--qos=normal --gres=gpu:3090:3 --mem=96G'
sbatch \$F --export=ALL,DEVMAP=auto,TOK_BUDGET=12000 -o logs/s2f_jc.log scripts/job_judge_v2.sh $J/correct_input.jsonl $J/correct_judged_s0.jsonl 0 1
sbatch \$F --export=ALL,DEVMAP=auto,TOK_BUDGET=12000,MODE=extract -o logs/s2f_je.log scripts/job_judge_aux.sh $J/extract_input.jsonl $J/extract_judged_s0.jsonl 0 1
sbatch \$F --export=ALL,DEVMAP=auto,TOK_BUDGET=12000,MODE=stance -o logs/s2f_js.log scripts/job_judge_aux.sh $J/stance_input.jsonl $J/stance_judged_s0.jsonl 0 1" || { echo "JUDGE SUBMIT FAILED"; exit 1; }
echo "JUDGES_SUBMITTED $(date)"
for l in s2f_jc s2f_je s2f_js; do r=$(waitlog $l.log); [ "$r" = "1" ] || { echo "JUDGE $l FAILED"; exit 1; }; echo "$l done $(date)"; done
for t in correct extract stance; do scp -q "$R:rq4_v2/$J/${t}_judged_s0.jsonl" $J/ || exit 1; done
python3 - <<'PY' || { echo "JUDGE PARSE CHECK FAILED"; exit 1; }
import json, sys
J = "out/stage2_full_qwen/judge"; bad = False
for t in ("correct", "extract", "stance"):
    inp = [json.loads(l)["key"] for l in open(f"{J}/{t}_input.jsonl")]; out = [json.loads(l) for l in open(f"{J}/{t}_judged_s0.jsonl")]
    keys = {o["key"] for o in out}; miss = len(set(inp) - keys); dup = len(out) - len(keys)
    fail = sum((o.get("judge_correct") is None) if t == "correct" else (o.get("parsed") is None) for o in out)
    print(t, "input", len(inp), "judged", len(out), "missing", miss, "dups", dup, "unparseable", fail, f"({100 * fail / max(1, len(out)):.2f}%)")
    bad |= bool(miss or dup or fail > 0.01 * len(out))
sys.exit(1 if bad else 0)
PY
echo "ALL_JUDGES_DONE $(date)"
