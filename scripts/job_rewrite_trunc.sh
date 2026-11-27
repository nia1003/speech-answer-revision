#!/bin/bash
#SBATCH -J rw_trunc
#SBATCH -p 3d
#SBATCH --gres=gpu:3090:1
#SBATCH --exclude=s01,s07,s09
#SBATCH -c 8
#SBATCH --mem=48G
#SBATCH -t 12:00:00
cd $HOME/rq4_v2
export HF_HUB_OFFLINE=1
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
env_qwen_official/bin/python -u scripts/rewrite_trunc.py $HOME/rq4_v2
echo RW_JOB_END
