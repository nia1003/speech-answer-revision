#!/bin/bash
# Run tts_gemini.py once per Pacific-time day until all clips exist or a non-429 error appears.
# Each run stops by itself at 90 requests/day or at the first failed request (no retry within a run).
cd $HOME/rq4_v2
while true; do
  env_tts/bin/python -u scripts/tts_gemini.py $HOME/rq4_v2 >> logs/tts_gemini_daily.log 2>&1
  last=$(tail -1 out/tts_gemini/ledger.jsonl)
  if grep -q "TTS_GEMINI_RUN_END: 216/216\|TTS_GEMINI_RUN_END: 211/216" <(tail -1 logs/tts_gemini_daily.log); then echo ALL_CLIPS_DONE >> logs/tts_gemini_daily.log; break; fi
  if echo "$last" | grep -q '"status": 429'; then sleep 120; continue; fi        # per-minute limit: wait, run again
  if echo "$last" | grep -q '"status": 200\|GET models'; then                     # daily cap reached: sleep to next PT day
    now=$(TZ=America/Los_Angeles date +%s); next=$(TZ=America/Los_Angeles date -d "tomorrow 00:10" +%s); sleep $((next-now)); continue; fi
  echo "STOPPED on non-429 error" >> logs/tts_gemini_daily.log; break
done
