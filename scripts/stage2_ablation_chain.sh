#!/bin/bash
# local driver: probe -> conditions -> round 2 -> judge -> metrics. Stops at the first failure.
cd $PROJECT_DIR; R=$REMOTE_HOST; D=out/stage2_ablation_musique
waitlog () { while true; do f=$(ssh -o ConnectTimeout=20 $R "grep -l 'Traceback\|JOB_END\|abort\|OutOfMemory' ~/rq4_v2/logs/$1 2>/dev/null" 2>/dev/null); if [ -n "$f" ]; then ssh $R "grep -c JOB_END ~/rq4_v2/logs/$1"; return; fi; sleep 60; done; }
r=$(waitlog s2a_probe.log); [ "$r" = "1" ] || { echo "PROBE FAILED"; exit 1; }
scp -q $R:rq4_v2/$D/probe.jsonl $D/ || exit 1
python3 scripts/stage2_ablation_conditions.py $D || exit 1
scp -q $D/conditions.jsonl $R:rq4_v2/$D/ && scp -q scripts/stage2_ablation_round2.py scripts/job_stage2_ablation_round2.sh $R:rq4_v2/scripts/ || exit 1
ssh $R "cd ~/rq4_v2; [ -e $D/round2.jsonl ] && echo EXISTS && exit 1; sbatch -o logs/s2a_round2.log scripts/job_stage2_ablation_round2.sh" || exit 1
r=$(waitlog s2a_round2.log); [ "$r" = "1" ] || { echo "ROUND2 FAILED"; exit 1; }
scp -q $R:rq4_v2/$D/round2.jsonl $D/ || exit 1
python3 scripts/stage2_ablation_metrics.py build $D || exit 1
scp -q $D/judge_input.jsonl $R:rq4_v2/$D/ || exit 1
ssh $R "cd ~/rq4_v2; [ -e $D/judge_v2.jsonl ] && echo EXISTS && exit 1; sbatch --qos=normal --gres=gpu:3090:3 --mem=96G --export=ALL,DEVMAP=auto,TOK_BUDGET=12000 -o logs/s2a_judge.log scripts/job_judge_v2.sh $D/judge_input.jsonl $D/judge_v2.jsonl" || exit 1
r=$(waitlog s2a_judge.log); [ "$r" = "1" ] || { echo "JUDGE FAILED"; exit 1; }
scp -q $R:rq4_v2/$D/judge_v2.jsonl $D/ || exit 1
python3 scripts/stage2_ablation_metrics.py metrics $D || exit 1
echo CHAIN_DONE
