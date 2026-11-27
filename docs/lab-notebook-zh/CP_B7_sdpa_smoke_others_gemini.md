Checkpoint: CP_B7 sdpa 版 smoke 文字條件、(c) 記憶體試跑、其他 4 模型 attention、Gemini 額度、Qwen 全量文字條件開跑

What ran:
- 410508（2×3090）：Qwen2.5-Omni-7B，attn_implementation="sdpa"（語言模型與音訊編碼器都確認是 sdpa），baseline_qwen_v3.py
  （v2 的空行分隔：段落之間、段落與問題之間各一個空行）。smoke 80 的文字條件 A_q、A_a、A_bc 共 120 筆；
  接著用 Kokoro 音訊試跑先前跳過的 3 筆 C_c。
- 410509（1×3090）：其他 4 個模型各 10 題 GSM8K 文字版，記錄實際 attention 設定與輸出（diag_others.py，設定不變）。
- Gemini TTS（key 末四碼 …19YA，間隔 21 秒）：自動續跑迴圈，遇到每日上限後我手動停止。
- 410510（2×3090）：依你「smoke 檢核過就開始跑全部」的指示，開始 Qwen 全量文字條件（見最後一節）。

Raw data:
- $PROJECT_DIR/out/sdpa/baseline_smoke80_qwen25omni_sdpa_textA.jsonl（120 筆）、qwen_sdpa.log、attn_others.log
- $PROJECT_DIR/out/diag/attn_{ultravox,llamaomni2,glm4voice,kimiaudio}.jsonl
- 戰艦 ~/rq4_v2/out/tts_gemini/ledger.jsonl（19 筆：13 筆 200〔含 1 次查模型清單〕、6 筆 429）；12 個 wav 在 out/tts_gemini/question/
- (c) 試跑錯誤：torch.OutOfMemoryError，要配置 17.56 GiB，GPU 0 只剩 16.68 GiB（eager 時是 8.78 GiB）。
- Gemini 429 全文中的配額：quotaId GenerateRequestsPerMinutePerProjectPerModel-FreeTier，quotaValue 3；
  以及 GenerateRequestsPerDayPerProjectPerModel-FreeTier，quotaValue 10（model gemini-2.5-flash-tts）。

Computed results:
smoke 80 文字條件（規則判分），sdpa 對照先前的 eager：
| run | sdpa 答對 | eager 答對 | sdpa 截斷 | eager 截斷 | sdpa 有 "other other"／"Human:" | eager |
|---|---|---|---|---|---|---|
| GSM8K A_q | 34/40 | 11/40 | 0 | 5 | 0／0 | 29／5 |
| MuSiQue A_a（只給問題） | 0/40 | 0/40 | 0 | 2 | 0／0 | 11／11 |
| MuSiQue A_bc（附段落，空行分隔） | 18/40 | 18/40 | 0 | 0 | 0／0 | 19／6 |
- A_a 仍是 0/40：模型回答「不確定是哪一位」或要求補充資訊，不是管線問題。

其他 4 個模型（10 題 GSM8K 文字版）：
| 模型 | 實際 attention | 錯誤 | 重複字／"Human:"／亂碼 | 最後數字答對 | 平均秒 |
|---|---|---|---|---|---|
| Ultravox v0_4 | Llama 語言模型 eager；Whisper、整體 sdpa | 0 | 0／0／0 | 9/10 | 3.2 |
| LLaMA-Omni2-7B | sdpa | 0 | 0／0／0 | 5/10 | 1.5 |
| GLM-4-Voice-9B | sdpa | 0 | 0／0／0 | 3/10 | 9.9 |
| Kimi-Audio-7B-Instruct | sdpa | 第 1 題就失敗（TypeError: 'NoneType' object is not iterable），停止 | — | — | — |

Anomalies:
1. (c) 那 3 題在 sdpa 下反而要更多記憶體（17.56 GiB），24 GB 的卡仍跑不了。維持「記憶體限制，未跑」。
2. Gemini 免費方案是每分鐘 3 次、每天 10 次（不是先前以為的 100 次）。照每天 10 次，smoke 的 211 段要 21 天，
   全量 3,736 題要約一年。我在今天的額度用完後把續跑迴圈停了（之前每 2 分鐘重試一次，多送了 4 次 429）。
3. Ultravox 的 Llama 語言模型是 eager，但 10 題沒有出現 Qwen 那種問題；之後若要統一可再測 sdpa。
4. LLaMA-Omni2 常把數字寫成英文（例如 "fifty cupcakes"），規則判分取最後一個阿拉伯數字，會把這種答對判成錯。
   GLM 也可能有同樣情況。這是判分規則的問題，全量前要決定要不要先把英文數字轉回阿拉伯數字。
5. Kimi 的純文字輸入（只有 text 訊息、沒有 audio）在 kimia_infer 裡失敗；它的條件 A 要另外寫。

全量開跑（依你的指示）:
- 410510：Qwen2.5-Omni-7B sdpa，全量 3,736 題的文字條件：GSM8K 1,319 題 A_q；MuSiQue 2,417 題 A_a 與 A_bc（兩種都跑，因為 MuSiQue 用哪種設定還沒定）。
  共 6,153 次；輸出 ~/rq4_v2/out/full_textA_qwen25omni_sdpa.jsonl，可續跑；預估 8–12 小時。
- 沒有跑：語音條件（等音訊）、其他 4 個模型（輸入路徑與判分規則還沒定）。

Decision needed:
1. 語音條件的 TTS：Gemini 免費方案每天 10 次不可行。選項：(a) 專案開啟付費提高額度；(b) 改回 Kokoro，但分數讀法要先處理（96 題含分數）；(c) 其他 TTS。
2. 數字判分：全量判分前，要不要先把英文數字詞轉回阿拉伯數字（對 LLaMA-Omni2、GLM 影響大）。
3. Kimi 的文字條件寫法、Ultravox 要不要改 sdpa。
4. MuSiQue 正式設定：只給問題 0/40，附段落 18/40。

---
## 追加（2026-11-21）：數字詞轉換（你已同意）

- 新檔 scripts/numwords.py（英文數字詞、口語分數 → 阿拉伯數字，"three hundred and ten" → 310）與 scripts/score_baseline_v2.py；舊的 score_baseline.py 沒有改。
- 規則：GSM8K 的輸出**沒有任何阿拉伯數字**時才轉換英文數字詞，再取最後一個數字。
  原因：全部轉換時，答案後面的英文數字（例如 Qwen 第 10 題「…366 downloads over the three months」、LLaMA-Omni2 第 1121 題「…35 miles in seven days」）會被誤抓成答案。
- 重算結果（v1 → v2）：Qwen sdpa GSM8K 文字 34 → 34/40；Ultravox 9 → 9/10；LLaMA-Omni2 5 → 6/10（第 180 題整段只用英文數字，答案 twenty 現在判對）；GLM 3 → 3/10。
- 限制：同一段輸出同時有阿拉伯數字和英文數字、而答案用英文寫時，仍會抓錯。全量判分後抽查。

---
## 追加（2026-11-21）：Ultravox 統一改用 sdpa
- 決定（使用者）：五個模型的 attention 一律用 sdpa。Ultravox 載入時加 attn_implementation="sdpa"，確認 Llama 語言模型、Whisper、整體都是 sdpa。
- 410514（1×3090）同樣 10 題 GSM8K 文字版各跑一次：
  eager：答對 9/10，異常 0，平均 3.0 秒；sdpa：答對 9/10，異常 0，平均 2.5 秒；兩者逐字相同 6/10。
- 檔案：戰艦 ~/rq4_v2/out/diag/uv_eager.jsonl、uv_sdpa.jsonl。
- 判讀：改用 sdpa 不影響答對數，但有 4/10 題的輸出措辭不同，所以舊 RQ4 的 Ultravox（eager）結果不能與新結果逐字比較。
