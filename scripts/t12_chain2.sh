#!/bin/bash
# T1/T2 driver, part 2 (after the gate fix): wait for runner jobs (main + add) -> judge inputs -> judges -> metrics.
cd $PROJECT_DIR; R=$REMOTE_HOST; D=out/stage2_measurement_check
waitlog () { while true; do f=$(ssh -o ConnectTimeout=20 $R "grep -l 'Traceback\|JOB_END\|abort\|OutOfMemory\|CANCELLED\|DUE TO' ~/rq4_v2/logs/$1 2>/dev/null" 2>/dev/null); if [ -n "$f" ]; then ssh -o ConnectTimeout=20 $R "grep -c JOB_END ~/rq4_v2/logs/$1"; return; fi; sleep 60; done; }
for l in t12_run0 t12_run1 t12_run2 t12_add0 t12_add1 t12_add2; do r=$(waitlog $l.log); [ "$r" = "1" ] || { echo "RUN $l FAILED"; exit 1; }; done
ssh $R "grep -h T12_RUN_DONE ~/rq4_v2/logs/t12_run?.log ~/rq4_v2/logs/t12_add?.log"
mkdir -p $D/runs_parts; scp -q "$R:rq4_v2/$D/runs_*shard*.jsonl" $D/runs_parts/ || exit 1
cat $D/runs_parts/*.jsonl > $D/runs.jsonl
python3 scripts/t12_judge_inputs.py $D/runs.jsonl || exit 1
ssh $R "cd ~/rq4_v2; ls $D/correct_input.jsonl 2>/dev/null" && { echo "judge input EXISTS on cluster, stop"; exit 1; }
scp -q $D/correct_input.jsonl $D/extract_input.jsonl $D/stance_input.jsonl $R:rq4_v2/$D/ || exit 1
echo "RUNS_DONE $(date)"
ssh $R "cd ~/rq4_v2; for s in 0 1; do
  sbatch -o logs/t12_jc\$s.log scripts/job_judge_v2.sh $D/correct_input.jsonl $D/correct_judged_s\$s.jsonl \$s 2
  sbatch --export=ALL,MODE=extract -o logs/t12_je\$s.log scripts/job_judge_aux.sh $D/extract_input.jsonl $D/extract_judged_s\$s.jsonl \$s 2
  sbatch --export=ALL,MODE=stance -o logs/t12_js\$s.log scripts/job_judge_aux.sh $D/stance_input.jsonl $D/stance_judged_s\$s.jsonl \$s 2
done" || exit 1
for l in t12_jc0 t12_jc1 t12_je0 t12_je1 t12_js0 t12_js1; do r=$(waitlog $l.log); [ "$r" = "1" ] || { echo "JUDGE $l FAILED"; exit 1; }; done
scp -q "$R:rq4_v2/$D/*_judged_s?.jsonl" $D/ || exit 1
for t in correct extract stance; do cat $D/${t}_judged_s0.jsonl $D/${t}_judged_s1.jsonl > $D/${t}_judged.jsonl; done
echo "JUDGES_DONE $(date)"
python3 scripts/t12_metrics.py t1 > /dev/null || { echo "METRICS T1 FAILED"; exit 1; }
python3 scripts/t12_metrics.py t2 > /dev/null || { echo "METRICS T2 FAILED"; exit 1; }
echo CHAIN_DONE
