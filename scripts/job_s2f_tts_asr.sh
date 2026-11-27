#!/bin/bash
#SBATCH -J s2f_tts
#SBATCH -p 3d
#SBATCH --gres=gpu:3090:1
#SBATCH --exclude=s01,s07,s09
#SBATCH -c 8
#SBATCH --mem=48G
#SBATCH -t 1-00:00:00
# Formal run evidence TTS (env_cbx, tts_evidence_cbx.py = smoke v3 settings) + Whisper read-back v2 (asr_evidence_v2.py, key_ok rule).
# "Are you sure?" variants are NOT re-synthesized: the smoke-chosen seed-20261221 file is reused (GO_CRITERIA v1).
# usage: sbatch -o logs/X.log job_s2f_tts_asr.sh <evidence_final.jsonl> <out_dir>
cd $HOME/rq4_v2
export HF_HUB_OFFLINE=1
if [ -e "$2/audio" ]; then echo "$2/audio EXISTS, abort"; exit 1; fi
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
env_cbx/bin/python -u scripts/tts_evidence_cbx.py $HOME/rq4_v2 "$1" "$2" || exit 1
$HOME/rq4_dualcheck/envs/llamaomni2/bin/python -u scripts/asr_evidence_v2.py $HOME/rq4_v2 "$1" "$2" || exit 1
echo JOB_END
