#!/bin/bash
#SBATCH -J h1c1_mistral
#SBATCH -p 3d
#SBATCH --qos=spot
#SBATCH --gres=gpu:RTXPRO6000Blackwell:1
#SBATCH -c 8
#SBATCH --mem=96G
#SBATCH -t 0-04:00:00
# usage: sbatch -o logs/run1.log job_mistral.sh run1      (env reused read-only from ~/rq4_Ajudge/env)
set -e
cd $HOME/rq4_v2
export HF_HUB_OFFLINE=1
$HOME/rq4_Ajudge/env/bin/python -u scripts/mistral_depth.py data/gsm8k_depth_smoke_40.jsonl out/h1_check1/mistral_$1.jsonl
