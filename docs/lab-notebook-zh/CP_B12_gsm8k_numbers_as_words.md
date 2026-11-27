Checkpoint: CP_B12 GSM8K 題目音訊 v3（所有數字改寫成英文詞）重新合成＋Whisper 檢查＋語音 smoke（2026-11-21）

決定（使用者，試聽後）：「885 唸成 105，改寫數字後重新合成」。

What ran:
- scripts/tts_textnorm_v3.py：先套 v2（分數、比例、時間、N$），再把所有數字改成英文詞：
  - 金額：「$1.20」改成 one dollar and twenty cents。
  - 百分比、序數、年份、「#N」、負數。
  - 小數：「1.5」改成 one point five。
  - 1,319 題送給 TTS 的文字都沒有阿拉伯數字了，其中 1,296 題有改動。
- 410593–410595（各 1×3090）：scripts/tts_full_v3_cbx.py → scripts/asr_v3_cbx.py，分 3 份同時跑。
  - Chatterbox 設定、種子、切段都和 CP_B11 相同。
  - 只重做 GSM8K 的 1,319 題。MuSiQue 沿用 CP_B11 的音訊。
  - Whisper 比對的參考是**原題**的數字（經 v2 正規化）。
- 410612：scripts/job_smoke_speech_cbx_v3.sh，Qwen2.5-Omni-7B sdpa，只跑 GSM8K 的 C_q（smoke 40 題）。
  - 新建 out/tts_cbx_v3_view：question/ 只放 v3 的 GSM8K wav 的 symlink。
  - 用 score_baseline_v2.py 判分。
- 舊的 out/tts_full、out/smoke_speech_cbx 都沒有動。

Raw data:
- 戰艦 ~/rq4_v2/out/tts_full_v3/question/：1,319 個 wav。
- 本機 out/tts_full_v3_pull/：manifest_shard{0,1,2}.jsonl、asr_shard{0,1,2}.jsonl、三份 log，都沒有錯誤。
- 本機 out/smoke_speech_cbx_v3/：smoke80_speech_cbx_v3_qwen25omni_sdpa.jsonl、scored_C.jsonl、manifest.jsonl、smoke_v3.log。

Computed results — Whisper 檢查:
| | 題數 | 比對不一致 | 平均 WER | 平均音長（秒） | 最長（秒） |
|---|---|---|---|---|---|
| CP_B11（v2） | 1,319 | 111（8.4%，寬鬆比對） | 0.023 | 12.3 | 37.1 |
| v3 | 1,319 | 26（2.0%，嚴格比對） | 0.021 | 12.5 | 37.1 |

這 26 題逐筆看過，分成三類：
1. **真的讀錯或聽錯，3 題：**
   - 205：原題「92, 100 and 86」。v3 文字變成「one hundred and eighty-six」，聽成 186。**這是 v3 改寫規則的問題**（「100 and 86」寫成英文後有歧義），不是 TTS 讀錯。
   - 806：「The four hundred fifth graders」聽成「four fifth graders」，hundred 不見了。
   - 384：「three fifths」聽成「brief-fifths」。
2. **無法確定，2 題：**
   - 891：121 聽成「100 to 21」。
   - 445：「six five dollar bills」聽成「$6.50 bills」。原題本身就有歧義。
3. **其實讀對了，是比對程式的問題，21 題：**
   - 序數（3rd → third）、「1-hour」→ one-hour、名字裡的數字（Sally Thirtytwo）、時間格式（2.15）、mph 被轉成「MP8」、Whisper 結尾截斷等。

- 先前的典型錯誤這次都讀對了：885 的兩個 125、819 的 175000、1278 的 214、195 的 $1.20、615 的 $2.00。

Computed results — 語音 smoke（GSM8K C_q，40 題）:
| 音訊 | 答對 |
|---|---|
| 文字 A_q（CP_B9 smoke） | 34/40 |
| CP_B11 音訊（v2） | 33/40 |
| v3 音訊 | 31/40 |

- 判定改變的有 4 題，另有 1 題仍錯但答案變了：
  - 對變錯 3 題：648、570、383。
  - 錯變對 1 題：1062。
  - 885 仍錯，答案從 440 變成 750。
- 這 3 題加上 885 逐題看過：Whisper 都聽對，模型的推理也都用了正確數字，錯在推理本身。
  - 648：漏算 Howie 自己（26×2=52）。
  - 570：每天花費算錯。
  - 383：利潤除以 4，得到 $4.50。
  - 885：這次聽到的是 125（先前是 105），但把「twice as many」理解成兩天的總和，答 750（正確 500）。
- 40 題的 smoke 中，差 2 題在 greedy 下屬於題目層級的變動，不能解讀成 v3 音訊比較差。
- 用全部 1,319 題比較 v2 和 v3 音訊對正確率的影響，要等全量跑完。

判讀與限制:
- 數字唸錯的比例從約 8.4% 降到約 0.2–0.4%（3–5/1,319）。
- 205 是改寫規則造成的，要修規則（例如列舉裡的「100 and 86」，「and」前面的 hundred 不加 and），只影響少數題。
- v3 改變了題目的呈現方式（數字都用英文詞），語音條件和文字條件的差異因此包含「數字的寫法」。這屬於語音呈現本身，限制裡要寫明。
- 沒有人工試聽 v3 音訊。

沒有做:
- 沒有修 205 的改寫規則，也沒有重新合成任何題目。
- 沒有跑全量語音條件。
- 沒有重跑 MuSiQue 的 C_b（音訊沒變，維持 22/40）。

Decision needed:
1. 205 的改寫規則要不要修（只重合成受影響的題目，並在 manifest 註明），還是保留並在分析中標記 3–5 題？
2. 主實驗的 GSM8K 語音條件改用 v3 音訊（建議），v2 保留作為附錄？
3. 要不要開始跑 Qwen 語音條件全量（GSM8K C_q 用 v3、MuSiQue C_b 用 CP_B11 音訊）？
