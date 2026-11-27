#!/bin/bash
#SBATCH -J judge_v2
#SBATCH -p 3d
#SBATCH --qos=spot
#SBATCH --gres=gpu:RTXPRO6000Blackwell:1
#SBATCH -c 8
#SBATCH --mem=96G
#SBATCH -t 1-00:00:00
# Stage 1 correctness judge (prompt v2) (Mistral-Small-24B bf16). env reused read-only from ~/rq4_Ajudge/env.
# usage: sbatch -o logs/judge_X.log job_judge.sh <input.jsonl> <out.jsonl> [shard n]
#        for 2x48GB: sbatch --gres=gpu:RTX6000AdaGeneration:2 --export=ALL,DEVMAP=auto ...
set -e
cd $HOME/rq4_v2
export HF_HUB_OFFLINE=1
nvidia-smi --query-gpu=name,memory.total --format=csv
$HOME/rq4_Ajudge/env/bin/python -X faulthandler -u scripts/judge_correct_v2.py "$@"
echo JOB_END
