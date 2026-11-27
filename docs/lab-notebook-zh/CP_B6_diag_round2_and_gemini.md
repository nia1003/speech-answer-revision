Checkpoint: CP_B6 Qwen 診斷第二輪（一次改一項）＋ Gemini TTS 第一批開頭

What ran:
- 410504，s05 的 2×3090，transformers 4.52.3（現有環境，沒有改），同樣 10 題 GSM8K 文字版，greedy、max_new_tokens 1024：
  nosys（不給系統提示）／ sdpa（attention 改 sdpa，語言模型和音訊編碼器都確認是 sdpa）／
  thinker_bf16（只載入 thinker，bf16、eager）／ fp32（只載入 thinker，float32、eager）／
  instruct（Qwen/Qwen2.5-7B-Instruct，bf16，sdpa，它自己的預設 chat template 與系統提示）。
- 手動讀 base 的 10 題輸出，核對規則判分。
- Gemini TTS：key 檔 ~/rq4_v2/.gemini_key（權限 600，末四碼 …19YA）有效；第一批 q80 送出 5 次，4 次成功、第 5 次 HTTP 429。

Raw data（$PROJECT_DIR/out/diag/）:
- base.jsonl、official_base.jsonl、r2_nosys.jsonl、r2_sdpa.jsonl、r2_thinker_bf16.jsonl、r2_fp32.jsonl、r2_instruct.jsonl、diag2.log
- 每題：id、標準答案、完整輸出、秒數、是否含 "other other"、是否含 "Human:"、相鄰重複詞數。
- Gemini：~/rq4_v2/out/tts_gemini/ledger.jsonl（6 筆：1 次查模型清單、4 次 200、1 次 429）；4 個 wav 在 out/tts_gemini/question/。
  429 訊息開頭："You exceeded your current quota, please check your plan and billing details…"（只存了前 300 字，看不到是哪一種配額）。

Computed results（10 題，答對＝最後一個數字等於標準答案）:
| 變體 | 只改了什麼 | "other other" | "Human:" | 相鄰重複詞 | 答對 | 與 base 逐字相同 |
|---|---|---|---|---|---|---|
| base（現有） | — | 7 | 3 | 8 | 4 | 10 |
| official | transformers 官方版本 | 7 | 3 | 8 | 4 | 10 |
| nosys | 不給系統提示 | 0 | 4 | 20 | 2 | 0 |
| sdpa | attention 改 sdpa | 0 | 0 | 0 | 9 | 0 |
| thinker_bf16 | 只載入 thinker（對照） | 8 | 10 | 43 | 2 | 0 |
| fp32 | 只載入 thinker＋float32 | 0 | 10 | 0 | 6 | 0 |
| Qwen2.5-7B-Instruct | 純文字模型 | 0 | 0 | 0 | 8 | 0 |
- 手動核對 base 的 10 題：規則判分 10 題全對（4 題答對、6 題答錯都屬實），沒有誤判。

判讀:
- 換成 sdpa 之後，重複字、"Human:" 全部消失，答對 9/10（純文字的 Qwen2.5-7B-Instruct 是 8/10）。例：549 題 base 算出「400 - 2 = 338」，sdpa 算出 398（正確）。
- 只載入 thinker 的 bf16 對照，前半段和 base 一樣錯（同樣的 338、"other other"），但它不會在回合結束時停下，10 題都繼續生成到 "Human:"，
  所以它不是乾淨的對照；fp32 也有同樣的停止問題，但重複字消失。
- 合起來看：問題出在 eager attention 在 bf16 下的數值，換 sdpa 就正常。transformers 版本、系統提示都不是原因。
- 這代表 smoke 80 的 Qwen 結果、以及舊 RQ4 用同一套 eager 設定跑的 Qwen 結果，都可能受影響。
- Gemini 的 429 發生在 12 秒內第 5 次請求，比較像每分鐘的限制，不是每天 100 次的限制。

Not done: 沒有重跑 smoke；沒有改既有環境或既有結果；Gemini 第一批只完成 4/80；沒有跑 Whisper 抽查。

Decision needed:
1. 之後的 Qwen 推論改用 attn_implementation="sdpa"（語言模型與音訊編碼器都是），並重跑 smoke 80？
   sdpa 也可能讓長音訊的記憶體需求變小，(c) 那 3 題可能就跑得動。
2. Gemini：改成每兩次請求間隔至少 21 秒（每分鐘 ≤ 3 次）、存完整錯誤訊息，再試一次；再 429 就停下回報。
3. 終端機分頁裡的「放 key」指令還在等你輸入。如果不換 key，可以按 Ctrl-C 取消，現在的 key 檔不會被動到；
   如果要換，貼上新 key 按 Enter。
