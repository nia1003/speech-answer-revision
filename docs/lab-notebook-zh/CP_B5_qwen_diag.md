Checkpoint: CP_B5 Qwen2.5-Omni 輸出品質診斷（10 題 GSM8K 文字版）

What ran（smoke 沒有重跑；現有環境沒有改）:
1. 用現有環境的 processor 印出 3 題實際送進模型的完整文字（GSM8K 文字 648、GSM8K 語音 885、MuSiQue 附段落文字 2hop__686395_141338）。
2. 現有環境（~/rq4_dualcheck/envs/qwen25omni，transformers 4.52.3）跑 10 題 GSM8K 文字版，設定和 smoke 相同。
3. 另建獨立環境 ~/rq4_v2/env_qwen_official，安裝官方 README 指定的 git+transformers@v4.51.3-Qwen2.5-Omni-preview
   （套件回報版本 4.52.0.dev0），torch 2.6.0+cu124，跑同樣 10 題。兩次都在 s05 的 2×3090、device_map=auto、eager attention。
另外（在你的指示之前就開始、已停止）：現有環境的「不給系統提示」變體只跑了 1 題（out/diag/nosys.jsonl）；sdpa、fp32 沒跑；
另建的 transformers 4.57.1 環境（~/rq4_v2/env_qwen_new）不是官方版本，沒有使用。

Raw data（$PROJECT_DIR/out/diag/）:
- base.jsonl（現有環境）、official_base.jsonl（官方版本），每題：id、標準答案、完整輸出、秒數、是否含 "other other"、是否含 "Human:"、相鄰重複詞數。
- 送進模型的完整文字（GSM8K 648）：
  "<|im_start|>system\nYou are Qwen, a virtual human developed by the Qwen Team, Alibaba Group, capable of perceiving auditory and visual inputs, as well as generating text and speech.<|im_end|>\n<|im_start|>user\n{題目原文}<|im_end|>\n<|im_start|>assistant\n"
  語音題（885）的 user 內容是 "<|audio_bos|><|AUDIO|><|audio_eos|>"；MuSiQue 附段落的文字題是「段落」＋「問題」兩個文字片段，模板把兩段直接接在一起，中間沒有換行。
- thinker 的 generation_config 只有 pad／bos／eos token，沒有其他預設（沒有 repetition_penalty、取樣參數）。

Computed results:
| 環境 | 含 "other other" | 含 "Human:" | 相鄰重複詞總數 | 最後數字答對 |
|---|---|---|---|---|
| 現有 4.52.3 | 7/10 | 3/10 | 8 | 4/10 |
| 官方 4.51.3-Omni-preview | 7/10 | 3/10 | 8 | 4/10 |
兩個環境 10 題的輸出逐字相同（10/10）。

Compared with plan: 照你指定的 (1)(2)(3) 順序做，沒有重跑 smoke。

Anomalies / 判讀:
- 模板與系統提示套用正確，和官方 README 範例一致。
- 換成官方指定的 transformers 版本，輸出完全不變，所以問題不是 transformers 版本造成的。
- 剩下還沒排除的可能：(i) 模型本身在這個「virtual human」系統提示下就會這樣（它被調成口語對話風格，結尾常加「If you have any other questions…」）；
  (ii) eager attention（官方建議 flash_attention_2，但官方範例預設也沒開）；(iii) bf16 數值。這三項我都沒有測。
- MuSiQue 附段落的文字題，段落和問題之間沒有分隔，是 smoke 的實作細節，會影響 (b)/(c) 的文字條件，需要你決定要不要加換行。

Not done: 沒有測 attention 實作、精度或不給系統提示（各 10 題，都不會改現有環境）；沒有重跑 smoke。

Decision needed:
1. 要不要繼續測 (i)–(iii)？建議依序：不給系統提示 → sdpa → fp32，各 10 題，用現有環境，不改任何設定檔。
2. MuSiQue 段落與問題之間要不要加分隔（例如換行），之後重跑 (b)/(c) 時採用。
