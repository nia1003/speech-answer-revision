#!/bin/bash
#SBATCH -J s2_tts
#SBATCH -p 3d
#SBATCH --gres=gpu:3090:1
#SBATCH --exclude=s01,s07,s09
#SBATCH -c 8
#SBATCH --mem=48G
#SBATCH -t 3:00:00
# Stage 2 smoke v2: evidence TTS (env_cbx) then Whisper read-back (llamaomni2 env, as in job_tts_v4.sh).
# usage: sbatch -o logs/X.log job_stage2_tts_asr.sh <evidence_final.jsonl> <out_dir>
cd $HOME/rq4_v2
export HF_HUB_OFFLINE=1
if [ -e "$2/audio" ]; then echo "$2/audio EXISTS, abort"; exit 1; fi
env_cbx/bin/python -u scripts/tts_evidence_cbx.py $HOME/rq4_v2 "$1" "$2" || exit 1
$HOME/rq4_dualcheck/envs/llamaomni2/bin/python -u scripts/asr_evidence.py $HOME/rq4_v2 "$1" "$2" || exit 1
echo JOB_END
