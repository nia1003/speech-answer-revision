#!/bin/bash
#SBATCH -J tts_cbxn
#SBATCH -p 3d
#SBATCH --gres=gpu:3090:1
#SBATCH --exclude=s01,s07,s09
#SBATCH -c 8
#SBATCH --mem=48G
#SBATCH -t 12:00:00
cd $HOME/rq4_v2
export HF_HUB_OFFLINE=1
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
env_cbx/bin/python -u scripts/tts_chatterbox_norm.py $HOME/rq4_v2 && $HOME/rq4_dualcheck/envs/llamaomni2/bin/python -u scripts/asr_cbx_norm.py $HOME/rq4_v2 out/asr_cbx_norm.jsonl
echo CBXN_JOB_END
