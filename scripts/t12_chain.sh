#!/bin/bash
# T1/T2 local driver (PREREG_2/PREREG_3): wait for VPN -> upload -> TTS + ASR gate -> plan (gate, requests) -> Qwen rounds 2-3
# (3 shards) -> judge inputs -> judges (correct v2, extract, stance; 2 shards each) -> metrics t1, t2. Stops at the first failure.
cd $PROJECT_DIR; R=$REMOTE_HOST; D=out/stage2_measurement_check; D2=out/stage2_wrapper_contrast
waitssh () { until ssh -o ConnectTimeout=15 $R true 2>/dev/null; do sleep 60; done; }
waitlog () { while true; do f=$(ssh -o ConnectTimeout=20 $R "grep -l 'Traceback\|JOB_END\|abort\|OutOfMemory\|CANCELLED\|DUE TO' ~/rq4_v2/logs/$1 2>/dev/null" 2>/dev/null); if [ -n "$f" ]; then ssh -o ConnectTimeout=20 $R "grep -c JOB_END ~/rq4_v2/logs/$1"; return; fi; sleep 60; done; }
waitssh; echo "VPN up $(date)"
ssh $R "squeue -u <user> -h -j 411485 2>/dev/null; scancel 411485 2>/dev/null; sleep 2; sacct -j 411485 -n -o State | head -1"
ssh $R "cd ~/rq4_v2; for f in $D $D2 logs/t12_tts.log; do [ -e \$f ] && echo \"EXISTS \$f\" && exit 1; done; mkdir -p $D $D2" || { echo "TARGET EXISTS, stop"; exit 1; }
scp -q $D/{PREREG_2.md,sets.json,b_conditions.jsonl,tts_jobs.jsonl,clip_map.jsonl} $R:rq4_v2/$D/ && scp -q $D2/PREREG_3.md $R:rq4_v2/$D2/ \
  && scp -q scripts/{t12_tts.py,t12_asr.py,t12_runner.py,judge_aux_v1.py,job_t12_tts_asr.sh,job_t12_run.sh,job_judge_aux.sh} $R:rq4_v2/scripts/ || exit 1
ssh $R "cd ~/rq4_v2; sbatch --gres=gpu:3090:1 --exclude=s01,s07,s09 -o logs/t12_tts.log scripts/job_t12_tts_asr.sh" || exit 1
r=$(waitlog t12_tts.log); [ "$r" = "1" ] || { echo "TTS/ASR FAILED"; exit 1; }
mkdir -p $D/audio_meta; scp -q $R:rq4_v2/$D/{manifest.jsonl,asr.jsonl,fixed_choice.json} $D/ || exit 1
python3 scripts/t12_plan.py || { echo "PLAN/GATE FAILED"; exit 1; }
scp -q $D/{gate.json,requests.jsonl} $R:rq4_v2/$D/ || exit 1
echo "GATE_DONE $(date)"
ssh $R "cd ~/rq4_v2; for i in 0 1 2; do [ -e logs/t12_run\$i.log ] && exit 1; sbatch -o logs/t12_run\$i.log scripts/job_t12_run.sh \$i 3; done" || { echo "RUN SUBMIT FAILED"; exit 1; }
for i in 0 1 2; do r=$(waitlog t12_run$i.log); [ "$r" = "1" ] || { echo "RUN $i FAILED"; exit 1; }; done
scp -q "$R:rq4_v2/$D/runs_shard*.jsonl" $D/ || exit 1
ssh $R "grep -h T12_RUN_DONE ~/rq4_v2/logs/t12_run?.log"
cat $D/runs_shard*.jsonl > $D/runs.jsonl; mv $D/runs_shard0.jsonl $D/runs_shard0.part; mv $D/runs_shard1.jsonl $D/runs_shard1.part; mv $D/runs_shard2.jsonl $D/runs_shard2.part
python3 scripts/t12_judge_inputs.py $D/runs.jsonl || exit 1
scp -q $D/{correct_input.jsonl,extract_input.jsonl,stance_input.jsonl} $R:rq4_v2/$D/ || exit 1
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
