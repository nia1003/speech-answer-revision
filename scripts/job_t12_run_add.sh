#!/bin/bash
#SBATCH -J t12_add
#SBATCH -p 3d
#SBATCH --gres=gpu:3090:1
#SBATCH --exclude=s01,s07,s09
#SBATCH -c 8
#SBATCH --mem=48G
#SBATCH -t 1-00:00:00
# T1/T2 Qwen rounds 2-3 (t12_runner.py). usage: sbatch -o logs/X.log job_t12_run.sh <shard> <n>
cd $HOME/rq4_v2
export HF_HUB_OFFLINE=1 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
D=out/stage2_measurement_check
$HOME/rq4_dualcheck/envs/qwen25omni/bin/python -u scripts/t12_runner.py $D/requests_add.jsonl $D/runs_add_shard$1.jsonl $1 $2 || exit 1
echo JOB_END
