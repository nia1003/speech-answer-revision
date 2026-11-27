#!/bin/bash
#SBATCH -J s2d_tts
#SBATCH -p 3d
#SBATCH -c 8
#SBATCH --mem=48G
#SBATCH -t 2:00:00
# Diagnostics a/b: evidence TTS (env_cbx) + Whisper read-back v2, for <dir>/probe and <dir>/ceiling.
cd $HOME/rq4_v2
export HF_HUB_OFFLINE=1
for d in probe ceiling; do
  D=out/stage2_diag_musique/$d
  [ -e $D/audio ] && { echo "$D/audio EXISTS, abort"; exit 1; }
  env_cbx/bin/python -u scripts/tts_evidence_cbx.py $HOME/rq4_v2 $D/evidence.jsonl $D || exit 1
  $HOME/rq4_dualcheck/envs/llamaomni2/bin/python -u scripts/asr_evidence_v2.py $HOME/rq4_v2 $D/evidence.jsonl $D || exit 1
done
echo JOB_END
