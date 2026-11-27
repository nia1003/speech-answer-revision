#!/bin/bash
#SBATCH -J s2f_tts
#SBATCH -p 3d
#SBATCH --gres=gpu:3090:1
#SBATCH --exclude=s01,s07,s09
#SBATCH -c 8
#SBATCH --mem=48G
#SBATCH -t 1-00:00:00
# Resume of job_s2f_tts_asr.sh after preemption (413046, 2026-11-25): same TTS/ASR scripts and settings. tts_evidence_cbx.py
# skips clips whose .wav already exists (written via tmp+rename, so existing files are complete) and appends to manifest.jsonl.
# Aborts if asr.jsonl already exists. usage: sbatch -o logs/X.log job_s2f_tts_asr_resume.sh <evidence.jsonl> <out_dir>
cd $HOME/rq4_v2
export HF_HUB_OFFLINE=1
if [ ! -d "$2/audio" ] || [ -e "$2/asr.jsonl" ]; then echo "resume precondition failed, abort"; exit 1; fi
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
env_cbx/bin/python -u scripts/tts_evidence_cbx.py $HOME/rq4_v2 "$1" "$2" || exit 1
$HOME/rq4_dualcheck/envs/llamaomni2/bin/python -u scripts/asr_evidence_v2.py $HOME/rq4_v2 "$1" "$2" || exit 1
echo JOB_END
