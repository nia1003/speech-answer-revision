#!/bin/bash
#SBATCH -J tts_full
#SBATCH -p 3d
#SBATCH --gres=gpu:3090:1
#SBATCH --exclude=s01,s07,s09
#SBATCH -c 8
#SBATCH --mem=48G
#SBATCH -t 1-00:00:00
# usage: sbatch job_tts_full.sh <k> <N>
cd $HOME/rq4_v2
export HF_HUB_OFFLINE=1
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
env_cbx/bin/python -u scripts/tts_full_cbx.py $HOME/rq4_v2 $1 $2 && $HOME/rq4_dualcheck/envs/llamaomni2/bin/python -u scripts/asr_full_cbx.py $HOME/rq4_v2 $1
echo TTSFULL_JOB_END $1
