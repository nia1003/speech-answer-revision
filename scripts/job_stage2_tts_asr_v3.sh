#!/bin/bash
#SBATCH -J s2v3_tts
#SBATCH -p 3d
#SBATCH -c 8
#SBATCH --mem=48G
#SBATCH -t 3:00:00
# v3: evidence TTS (env_cbx) + Unsupported variants, then Whisper read-back v2 + variant check (llamaomni2 env).
# usage: sbatch -o logs/X.log job_stage2_tts_asr_v3.sh <evidence_final.jsonl> <out_dir>
cd $HOME/rq4_v2
export HF_HUB_OFFLINE=1
if [ -e "$2/audio" ]; then echo "$2/audio EXISTS, abort"; exit 1; fi
env_cbx/bin/python -u scripts/tts_evidence_cbx.py $HOME/rq4_v2 "$1" "$2" || exit 1
env_cbx/bin/python -u scripts/tts_unsupported_variants.py "$2" || exit 1
$HOME/rq4_dualcheck/envs/llamaomni2/bin/python -u scripts/asr_evidence_v2.py $HOME/rq4_v2 "$1" "$2" || exit 1
$HOME/rq4_dualcheck/envs/llamaomni2/bin/python -u scripts/asr_variants.py "$2" || exit 1
echo JOB_END
