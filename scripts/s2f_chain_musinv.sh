#!/bin/bash
# Formal run, MuSiQue Invalid: NLI -> merge (smoke-v3 rule) -> text resume (same shard files) + TTS/ASR (separate dir)
# -> rebuild audio evidence -> wait for current speech shards -> speech resume (same shard files).
cd $PROJECT_DIR; R=$REMOTE_HOST; D=out/stage2_full_qwen; P=$D/pass2
waitlog () { while true; do f=$(ssh -o ConnectTimeout=20 $R "grep -l 'Traceback\|JOB_END\|abort\|OutOfMemory\|CANCELLED\|DUE TO' ~/rq4_v2/logs/$1 2>/dev/null" 2>/dev/null); if [ -n "$f" ]; then ssh -o ConnectTimeout=20 $R "grep -c JOB_END ~/rq4_v2/logs/$1"; return; fi; sleep 60; done; }
r=$(waitlog s2f_nli.log); [ "$r" = "1" ] || { echo "NLI FAILED"; exit 1; }
scp -q ${R}:rq4_v2/$P/nli.jsonl $P/ || exit 1
python3 scripts/s2f_merge_nli.py $P/evidence_verified.jsonl $P/nli.jsonl $D/evidence_final_pass2.jsonl || { echo "MERGE FAILED"; exit 1; }
python3 - <<'PY' || { echo "PASS2 CHECK FAILED"; exit 1; }
import json
a=[json.loads(l) for l in open("out/stage2_full_qwen/evidence_final_pass1.jsonl")]; b=[json.loads(l) for l in open("out/stage2_full_qwen/evidence_final_pass2.jsonl")]
assert len(a)==len(b); d=[x for x,y in zip(a,b) if x!=y]
assert all(x["dataset"]=="musique" and x["evidence_type"]=="invalid" for x in d), "non-MuSiQue-Invalid rows changed"
print("pass2 vs pass1: changed rows", len(d), "all MuSiQue Invalid")
PY
grep '"dataset": "musique"' $D/evidence_final_pass2.jsonl | grep '"evidence_type": "invalid"' | grep '"verification_status": "nli_passed"' > $P/evidence_musinv_tts.jsonl
wc -l $P/evidence_musinv_tts.jsonl
ssh $R "cd ~/rq4_v2; for f in $D/evidence_final_pass2.jsonl $P/evidence_musinv_tts.jsonl $D/evidence_audio_musinv; do [ -e \$f ] && exit 1; done; exit 0" || { echo "TARGET EXISTS on cluster"; exit 1; }
scp -q $D/evidence_final_pass2.jsonl ${R}:rq4_v2/$D/ && scp -q $P/evidence_musinv_tts.jsonl ${R}:rq4_v2/$P/ || exit 1
ssh $R "cd ~/rq4_v2; for i in 0 1 2; do [ -e logs/s2f_r23_text\${i}_musinv.log ] && exit 1; done; [ -e logs/s2f_tts_musinv.log ] && exit 1
for i in 0 1 2; do sbatch -o logs/s2f_r23_text\${i}_musinv.log scripts/job_stage2_full_qwen_r23.sh $D/evidence_final_pass2.jsonl \$i 3 text text; done
sbatch -o logs/s2f_tts_musinv.log scripts/job_s2f_tts_asr.sh $P/evidence_musinv_tts.jsonl $D/evidence_audio_musinv" || { echo "SUBMIT FAILED"; exit 1; }
echo "TEXT_MUSINV_AND_TTS_SUBMITTED $(date)"
r=$(waitlog s2f_tts_musinv.log); [ "$r" = "1" ] || { echo "TTS MUSINV FAILED"; exit 1; }
mkdir -p $D/evidence_audio_meta_musinv; scp -q ${R}:rq4_v2/$D/evidence_audio_musinv/{asr.jsonl,manifest.jsonl} $D/evidence_audio_meta_musinv/ || exit 1
python3 scripts/s2f_build_audio_ev2.py $D/evidence_audio_meta_gsm8k/asr.jsonl $D/evidence_audio_meta_musinv/asr.jsonl || { echo "BUILD AUDIO2 FAILED"; exit 1; }
ssh $R "cd ~/rq4_v2; [ -e $D/evidence_final_audio_pass2.jsonl ] && exit 1; exit 0" || { echo "audio_pass2 EXISTS"; exit 1; }
scp -q $D/evidence_final_audio_pass2.jsonl ${R}:rq4_v2/$D/ || exit 1
for i in 0 1 2; do r=$(waitlog s2f_r23_speech$i.log); [ "$r" = "1" ] || { echo "FIRST SPEECH $i FAILED"; exit 1; }; done
ssh $R "cd ~/rq4_v2; for i in 0 1 2; do [ -e logs/s2f_r23_speech\${i}_musinv.log ] && exit 1; sbatch -o logs/s2f_r23_speech\${i}_musinv.log scripts/job_stage2_full_qwen_r23.sh $D/evidence_final_audio_pass2.jsonl \$i 3 speech speech; done" || { echo "SPEECH RESUME SUBMIT FAILED"; exit 1; }
echo "SPEECH_MUSINV_SUBMITTED $(date)"
for i in 0 1 2; do r=$(waitlog s2f_r23_text${i}_musinv.log); [ "$r" = "1" ] || { echo "TEXT MUSINV $i FAILED"; exit 1; }; done
echo "TEXT_MUSINV_DONE $(date)"
for i in 0 1 2; do r=$(waitlog s2f_r23_speech${i}_musinv.log); [ "$r" = "1" ] || { echo "SPEECH MUSINV $i FAILED"; exit 1; }; done
echo "ALL_RUNS_DONE $(date)"
