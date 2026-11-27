Checkpoint: CP_B13 第 1 階段全量：Qwen2.5-Omni-7B 語音條件 C（2026-11-21）

決定（使用者）：「修改、然後跑全量」（修 205 的改寫規則後跑全量）；「smoke 跑完就自己跑全量」。

What ran:
- 205 的改寫規則（scripts/tts_textnorm_v4.py）：
  - v3 會把「92, 100 and 86」寫成 "one hundred and eighty-six"，聽起來像 186。
  - v4 在「整百以上的數字 + and + 數字」之間加逗號，變成 "one hundred, and eighty-six"。其餘規則與 v3 完全相同。
  - 1,319 題中只有 205 的文字改變。
- 410613：scripts/job_tts_v4.sh。重新合成 205（設定、種子與 v3 相同），再做 Whisper 檢查，比對結果一致（100、86）。接著建立 out/tts_speech_final_view：
  - GSM8K：v3 音訊，205 換成 v4。
  - MuSiQue：CP_B11 的音訊。
  - 共 3,736 個 wav，manifest 3,736 筆，每筆記錄來源。
- 410614–410616（各 1×3090，s04／s05）：scripts/job_full_speech_qwen.sh。
  - 全部 3,736 題依題目順序分 3 份（data/speech_full_shards/）。
  - 腳本：baseline_qwen_v3.py，RUNS=C_q,C_b。
  - 模型設定：sdpa、greedy、max_new_tokens 1024、官方 system prompt，和 CP_B9 文字條件相同。
  - GSM8K 跑 C_q（問題用語音）；MuSiQue 跑 C_b（段落用文字，問題用語音）。
- 判分：scripts/score_baseline_v2.py，和 CP_B9 相同。

Raw data:
- 本機 out/full_speechC/：
  - full_speechC_qwen25omni_sdpa_shard{0,1,2}.jsonl（1,246／1,245／1,245 筆），合併成 full_speechC_qwen25omni_sdpa.jsonl（3,736 筆）。
  - scored_full_speechC_qwen25omni_sdpa_v2.jsonl：3,736 筆，有判定、步數、長度四分位。
  - manifest.jsonl、三份 log。log 沒有錯誤；_skipped 檔都是 0 筆。
- 被截斷 2 筆：gsm8k 415（C_q）、2hop__13592_49388（C_b），兩筆都判為答對。
- 答案抽取：GSM8K 1,319 筆全部抽到數字。MuSiQue 沒有抽取步驟，答案或別名整詞出現就算對。

Computed results（每題和 CP_B9 同題、同模型的文字條件配對）:
| | 語音 C | 文字 A | 文字對、語音錯 | 文字錯、語音對 | McNemar 精確 p |
|---|---|---|---|---|---|
| GSM8K（C_q vs A_q，1,319 題） | 1,016（77.0%） | 1,042（79.0%） | 92 | 66 | 0.046 |
| MuSiQue（C_b vs A_bc，2,417 題） | 1,354（56.0%） | 1,319（54.6%） | 158 | 193 | 0.069 |

- GSM8K 主分析的 1,301 題（排除沒有 <<>> 的 18 題）：語音 1,004、文字 1,029。
- 平均推論時間：C_q 4.6 秒、C_b 2.1 秒。平均問題音長：GSM8K 12.5 秒、MuSiQue 4.8 秒。
- 依步數（語音答對／文字答對／題數）：
  - GSM8K：
    - 1 步 57/57/65
    - 2 步 295/308/357
    - 3 步 283/288/364
    - 4 步 210/216/290
    - 5 步 106/103/138
    - 6 步 35/37/57
    - 7 步 11/14/21
    - 8 步 7/6/9
    - 沒有 <<>> 12/13/18
  - MuSiQue：
    - 2 hop 768/752/1,252
    - 3 hop 413/398/760
    - 4 hop 173/169/405
- 依長度四分位（語音／文字／題數）：
  - GSM8K：
    - Q1 264/275/327
    - Q2 270/271/328
    - Q3 251/253/323
    - Q4 219/230/323
  - MuSiQue：
    - Q1 372/367/614
    - Q2 366/357/603
    - Q3 323/310/603
    - Q4 293/285/597

Compared with plan:
- 符合第 1 階段的設計：同一 checkpoint、文字和語音、全部 3,736 題、greedy、max_new_tokens 1024，並報告截斷題數。
- 計畫書寫的 TTS 是 Gemini TTS，實際用的是 Chatterbox（CP_B8 的決定）。GSM8K 還經過 v3／v4 改寫（數字全部寫成英文詞）。計畫書的 TTS 段落需要更新。
- 判分用規則，沒有用 Mistral judge（計畫書列為待決定）。

Anomalies／判讀:
- GSM8K 語音比文字低 2.0 個百分點（p＝0.046）。MuSiQue 語音反而高 1.4 個百分點（p＝0.069）。兩個 p 都在邊緣，這裡沒有做多重比較校正，也還沒做 bootstrap 信賴區間。
- MuSiQue 語音比較高，可能的解釋（都還沒驗證）：
  - 段落是文字，只有很短的問題（約 4.8 秒）是語音。
  - 輸入形式改變，造成輸出風格不同，而判分規則是「答案整詞出現在輸出裡就算對」，會受輸出風格影響。
- GSM8K 語音和文字的差距，看不出隨步數系統性變大，但每格題數少，這只是描述。
- 語音條件也包含「數字改寫成英文詞」，所以差距不能只歸因於「聽」。限制裡要寫明。

沒有做:
- 沒有 bootstrap 信賴區間，也沒有迴歸（步數＋長度）。
- 沒有人工看「文字對、語音錯」的 92 題，分辨是聽錯數字還是推理不同。
- 沒有用 Mistral judge 複核 MuSiQue。
- 沒有跑其他 4 個模型。
- 計畫書的 TTS 段落沒有改，那是使用者的文件。

Decision needed（計畫書規定每完成一個模型要停下報告）:
1. 下一個模型：Ultravox（已改 sdpa）、Kimi-Audio（文字路徑待確認）、GLM-4-Voice、LLaMA-Omni2，順序由你決定。
2. 要不要先抽看 GSM8K「文字對、語音錯」的 92 題，分類成聽錯數字或推理不同？
3. MuSiQue 判分要不要另外用 Mistral judge 複核？
