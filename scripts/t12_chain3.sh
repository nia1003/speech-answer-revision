#!/bin/bash
# T1/T2 driver, part 3: judges resubmitted on 3x3090 (qos normal, DEVMAP=auto, TOK_BUDGET=12000, 1 shard each; same setup as the
# CP_S2_5 / smoke judge_v2 runs) -> merge -> metrics t1, t2.
cd $PROJECT_DIR; R=$REMOTE_HOST; D=out/stage2_measurement_check
waitlog () { while true; do f=$(ssh -o ConnectTimeout=20 $R "grep -l 'Traceback\|JOB_END\|abort\|OutOfMemory\|CANCELLED\|DUE TO' ~/rq4_v2/logs/$1 2>/dev/null" 2>/dev/null); if [ -n "$f" ]; then ssh -o ConnectTimeout=20 $R "grep -c JOB_END ~/rq4_v2/logs/$1"; return; fi; sleep 60; done; }
for l in t12_jc t12_je t12_js; do r=$(waitlog $l.log); [ "$r" = "1" ] || { echo "JUDGE $l FAILED"; exit 1; }; echo "$l done $(date)"; done
for t in correct extract stance; do scp -q "$R:rq4_v2/$D/${t}_judged_s0.jsonl" $D/ || exit 1; [ -e $D/${t}_judged.jsonl ] && { echo "$t judged EXISTS locally"; exit 1; }; cp $D/${t}_judged_s0.jsonl $D/${t}_judged.jsonl; done
wc -l $D/*_input.jsonl $D/*_judged.jsonl
echo "JUDGES_DONE $(date)"
python3 scripts/t12_metrics.py t1 > /dev/null || { echo "METRICS T1 FAILED"; exit 1; }
python3 scripts/t12_metrics.py t2 > /dev/null || { echo "METRICS T2 FAILED"; exit 1; }
echo CHAIN_DONE
