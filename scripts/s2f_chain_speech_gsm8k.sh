#!/bin/bash
# Formal run speech part that needs no Mistral: GSM8K evidence TTS/ASR -> evidence_final_audio -> speech smoke (0/400) -> full speech 0-2/3.
cd $PROJECT_DIR; R=$REMOTE_HOST; D=out/stage2_full_qwen
waitlog () { while true; do f=$(ssh -o ConnectTimeout=20 $R "grep -l 'Traceback\|JOB_END\|abort\|OutOfMemory\|CANCELLED\|DUE TO' ~/rq4_v2/logs/$1 2>/dev/null" 2>/dev/null); if [ -n "$f" ]; then ssh -o ConnectTimeout=20 $R "grep -c JOB_END ~/rq4_v2/logs/$1"; return; fi; sleep 60; done; }
r=$(waitlog s2f_tts_gsm8k.log); [ "$r" = "1" ] || { echo "TTS FAILED"; exit 1; }
mkdir -p $D/evidence_audio_meta_gsm8k; scp -q ${R}:rq4_v2/$D/evidence_audio/{asr.jsonl,manifest.jsonl} $D/evidence_audio_meta_gsm8k/ || exit 1
python3 scripts/s2f_build_audio_ev.py $D/evidence_audio_meta_gsm8k/asr.jsonl || exit 1
ssh $R "cd ~/rq4_v2; [ -e $D/evidence_final_audio.jsonl ] && exit 1; exit 0" || { echo "final_audio EXISTS on cluster"; exit 1; }
scp -q $D/evidence_final_audio.jsonl ${R}:rq4_v2/$D/ || exit 1
ssh $R "cd ~/rq4_v2; [ -e logs/s2f_r23_speech_smoke.log ] && exit 1; sbatch -o logs/s2f_r23_speech_smoke.log scripts/job_stage2_full_qwen_r23.sh $D/evidence_final_audio.jsonl 0 400 speech speechsmoke" || exit 1
r=$(waitlog s2f_r23_speech_smoke.log); [ "$r" = "1" ] || { echo "SPEECH SMOKE FAILED"; exit 1; }
scp -q ${R}:rq4_v2/$D/round23_qwen_speechsmoke_shard0.jsonl $D/ || exit 1
python3 - <<'PY' || { echo "SPEECH SMOKE CHECK FAILED"; exit 1; }
import json, sys, collections
R=[json.loads(l) for l in open("out/stage2_full_qwen/round23_qwen_speechsmoke_shard0.jsonl")]
n=len(R); bad=[r for r in R if r.get("r3_error") or not r.get("r3") or r["r3"].get("raw_output") is None]; tr=sum(r["truncated"] for r in R)
print("rows", n, collections.Counter((r["dataset"], r["evidence_type"]) for r in R), "r3 bad", len(bad), "r2 trunc", tr)
for r in R[:6]: print(r["dataset"], r["evidence_type"], r["user2_audio"], r["audio_input_secs"], "|| r2:", r["raw_output"][:50], "|| r3:", r["r3"]["raw_output"][:50])
sys.exit(1 if n < 10 or bad or tr > 0.05 * n else 0)
PY
ssh $R "cd ~/rq4_v2; for i in 0 1 2; do [ -e logs/s2f_r23_speech\$i.log ] && exit 1; sbatch -o logs/s2f_r23_speech\$i.log scripts/job_stage2_full_qwen_r23.sh $D/evidence_final_audio.jsonl \$i 3 speech speech; done" || { echo "FULL SPEECH SUBMIT FAILED"; exit 1; }
echo "FULL_SPEECH_SUBMITTED $(date)"
for i in 0 1 2; do r=$(waitlog s2f_r23_speech$i.log); [ "$r" = "1" ] || { echo "FULL SPEECH $i FAILED"; exit 1; }; done
ssh $R "cd ~/rq4_v2; wc -l $D/round23_qwen_speech_shard?.jsonl; grep -c 'ERROR' logs/s2f_r23_speech?.log"
echo "FULL_SPEECH_GSM8K_DONE $(date)"
