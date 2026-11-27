#!/bin/bash
#SBATCH -J t12_tts
#SBATCH -p 3d
#SBATCH -c 8
#SBATCH --mem=48G
#SBATCH -t 6:00:00
# T1/T2 TTS (env_cbx) + Whisper gate (llamaomni2 env). Output dir must not contain audio already.
cd $HOME/rq4_v2
export HF_HUB_OFFLINE=1
D=out/stage2_measurement_check
env_cbx/bin/python -u scripts/t12_tts.py $HOME/rq4_v2 $D/tts_jobs.jsonl $D || exit 1
$HOME/rq4_dualcheck/envs/llamaomni2/bin/python -u scripts/t12_asr.py $HOME/rq4_v2 $D || exit 1
echo JOB_END
