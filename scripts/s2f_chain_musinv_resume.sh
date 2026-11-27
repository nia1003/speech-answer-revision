#!/bin/bash
# Tail of s2f_chain_musinv.sh after TTS preemption: waits for resume job 413208 instead of 413046.
# -> rebuild audio evidence -> wait for current speech shards -> speech resume (same shard files).
cd $PROJECT_DIR; R=$REMOTE_HOST; D=out/stage2_full_qwen; P=$D/pass2
waitlog () { while true; do f=$(ssh -o ConnectTimeout=20 $R "grep -l 'Traceback\|JOB_END\|abort\|OutOfMemory\|CANCELLED\|DUE TO' ~/rq4_v2/logs/$1 2>/dev/null" 2>/dev/null); if [ -n "$f" ]; then ssh -o ConnectTimeout=20 $R "grep -c JOB_END ~/rq4_v2/logs/$1"; return; fi; sleep 60; done; }
r=$(waitlog s2f_tts_musinv_resume.log); [ "$r" = "1" ] || { echo "TTS MUSINV FAILED"; exit 1; }
mkdir -p $D/evidence_audio_meta_musinv; scp -q ${R}:rq4_v2/$D/evidence_audio_musinv/{asr.jsonl,manifest.jsonl} $D/evidence_audio_meta_musinv/ || exit 1
python3 scripts/s2f_build_audio_ev2.py $D/evidence_audio_meta_gsm8k/asr.jsonl $D/evidence_audio_meta_musinv/asr.jsonl || { echo "BUILD AUDIO2 FAILED"; exit 1; }
ssh $R "cd ~/rq4_v2; [ -e $D/evidence_final_audio_pass2.jsonl ] && exit 1; exit 0" || { echo "audio_pass2 EXISTS"; exit 1; }
scp -q $D/evidence_final_audio_pass2.jsonl ${R}:rq4_v2/$D/ || exit 1
ssh $R "cd ~/rq4_v2; for i in 0 1 2; do [ -e logs/s2f_r23_speech\${i}_musinv.log ] && exit 1; sbatch -o logs/s2f_r23_speech\${i}_musinv.log scripts/job_stage2_full_qwen_r23.sh $D/evidence_final_audio_pass2.jsonl \$i 3 speech speech; done" || { echo "SPEECH RESUME SUBMIT FAILED"; exit 1; }
echo "SPEECH_MUSINV_SUBMITTED $(date)"
for i in 0 1 2; do r=$(waitlog s2f_r23_speech${i}_musinv.log); [ "$r" = "1" ] || { echo "SPEECH MUSINV $i FAILED"; exit 1; }; done
echo "ALL_RUNS_DONE $(date)"
