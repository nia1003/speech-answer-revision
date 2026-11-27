#!/bin/bash
#SBATCH -J s2_smoke
#SBATCH -p 3d
#SBATCH --qos=normal
#SBATCH --gres=gpu:3090:3
#SBATCH -c 8
#SBATCH --mem=96G
#SBATCH -t 0-04:00:00
# Stage 2 smoke helper jobs with the judge env (read-only ~/rq4_Ajudge/env). usage: sbatch -o logs/X.log job_stage2_gpu.sh <script.py> <args...>
set -e
cd $HOME/rq4_v2
export HF_HUB_OFFLINE=1 DEVMAP=auto
nvidia-smi --query-gpu=name,memory.total --format=csv
$HOME/rq4_Ajudge/env/bin/python -u "$@"
echo JOB_END
