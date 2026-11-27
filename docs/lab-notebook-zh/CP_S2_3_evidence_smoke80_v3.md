Checkpoint：CP_S2_3 第 2 階段 smoke：修正規則後重新生成證據（v3），做完步驟 3（2026-11-23）

決定（使用者）：對 CP_S2_2 回覆「Yes, fix and regenerate」，也就是照該報告的建議修正：
1. 剔除人工閱讀發現有問題的證據。
2. 排除 k=h 的 Valid。
3. 重新合成「Are you sure?」。
4. 修正生成規則後重新生成。

沒有跑任何受測模型的第二輪。

What ran（題目沿用 CP_S2_2 重抽的 80 題，k 也相同，新檔放在 out/stage2_smoke_v3/）
- scripts/stage2_evidence_v3.py：
  - GSM8K 的運算詞清單擴充：subtract*、minus、plus、add*、multipl*、sum、difference、remain*、increase*、decrease*，以及「more／less／fewer／older…（中間最多 3 個字）than」。
  - 算式後的文字如果又提到運算元，就不使用「運算選錯」。
  - Valid 的 k=h → 剔除，原因記為 k_equals_h。
  - MuSiQue 的候選替換後，句子裡如果還出現原實體的字，就剔除（original_name_remains）；Mistral 回答 NONE 也剔除。
- scripts/stage2_mistral_subs_v2.py：
  - prompt 要求候選必須符合句子裡其他所有細節（地點、性別、別名、翻譯、年代、頭銜、國籍），沒有合適的就回答 NONE。
  - 模型和解碼設定與 v2 相同。job 411332，在 s02 上只用 math SDPA 核心。
- 規則驗證 scripts/stage2_verify_v2.py；NLI 用 scripts/stage2_nli.py（roberta-large-mnli），job 411334。
- 人工閱讀：manual_exclusions.json。在跑任何模型之前寫好，剔除 6 筆，每筆附理由。
- TTS／ASR：job 411335。
  - scripts/asr_evidence_v2.py：GSM8K 改用原始證據文字的數字比對；MuSiQue 實體改用模糊比對（相似度 ≥ 0.8）；關鍵詞沒念出來就剔除該段音訊。
  - 「Are you sure?」用 scripts/tts_unsupported_variants.py 產生 5 個種子版本，選第一個被 Whisper 完整聽出來的。
- 離線檢查 scripts/stage2_offline_checks.py：結果在 offline_checks.txt。

Raw data（out/stage2_smoke_v3/）
- mistral_requests.jsonl、mistral_proposals.jsonl（每筆的原始輸出都保留）。
- smoke80_evidence.jsonl → smoke80_evidence_verified.jsonl → nli.jsonl → smoke80_evidence_final_auto.jsonl。
- manual_exclusions.json → smoke80_evidence_final.jsonl → smoke80_evidence_final_audio.jsonl。最後這個是步驟 4 要用的檔，含每段音訊的路徑和 ASR 結果。
- evidence_audio/manifest.jsonl、asr.jsonl、unsupported_variants/choice.json。音訊在戰艦 ~/rq4_v2/out/stage2_smoke_v3/evidence_audio/。

1. 每個步數格的題數與 k 的分布
- 題目與 CP_S2_2 相同：每個資料集「都對」「都錯」各 20 題。GSM8K 每個步數格 5 題，MuSiQue 每個 hop 格 7／7／6 題。

突變類型 × k（只算最後可用的 Invalid）：
| GSM8K | k=1 | k=2 | k=3 | k=4 | k=6 | 合計 |
|---|---|---|---|---|---|---|
| 讀錯題目數量 | 6 | 1 | 3 | 0 | 0 | 10 |
| 運算選錯 | 3 | 1 | 3 | 1 | 0 | 8 |
| 引用錯的前一步結果 | 0 | 0 | 2 | 4 | 2 | 8 |
- 人工剔除的 879（k=1、讀錯題目數量）已扣除，所以 k=1 的讀錯題目數量是 6。

| MuSiQue | k=1 | k=2 | k=3 | k=4 | 合計 |
|---|---|---|---|---|---|
| 實體替換 | 9 | 10 | 5 | 1 | 25 |
- 這張表扣除了人工剔除的 5 筆。

2. 證據生成：通過率與剔除原因

| 資料集 | 類型 | 應生成 | 最後可用 | 剔除（原因：筆數） |
|---|---|---|---|---|
| GSM8K | Unsupported | 40 | 40 | – |
| GSM8K | Valid | 20 | 14 | 找不到 k：4；k=h：2 |
| GSM8K | Invalid | 40 | 26 | 沒有可用的突變類型：8；所有候選都被剔除：5；人工剔除：1 |
| MuSiQue | Unsupported | 40 | 40 | – |
| MuSiQue | Valid | 20 | 16 | k=h：3；ASR 聽不到關鍵實體：1（Howard the Duck，Chatterbox 在 26 秒的長句裡漏念） |
| MuSiQue | Invalid | 40 | 25 | Mistral 的候選全部不合規則：5；NLI 判定不是矛盾：5；人工剔除：5 |

- MuSiQue 候選被規則剔除的原因：
  - 候選出現在支持段落裡（例如 Orly、Valencia、Minneapolis、Louis XIV、NASA）。
  - 原實體的名字仍留在句子裡（例如 Olivier、Senate、Portuguese、Arabia、Toronto）。
  - Mistral 這次沒有回答 NONE。
- ASR 回讀（83 段證據音訊）：
  - GSM8K 有 6 筆數字比對不一致，我逐筆讀過，全部是格式差異（15.00 vs 15、.55 vs 0.55、1/4 vs ¼），數字本身都對，沒有真的錯誤。
  - MuSiQue 只有上面那 1 筆真的錯誤。
  - WER 中位數：GSM8K 0.06–0.09，MuSiQue 0–0.04。
- 「Are you sure?」：
  - 原本的種子（20261120）在 v2、v3 都被聽成「You sure?」。
  - 5 個新種子裡有 4 個被完整聽出。採用 seed 20261221，檔案是 evidence_audio/unsupported_variants/unsupported_seed20261221.wav。
  - **還需要你親耳確認一次。**

人工閱讀（我讀的，不是計畫書要求的人工抽查）
- GSM8K Invalid：26/27 合理，剔除 879（「4/4*$400」）。
  - v2 的 4 筆自相矛盾都已經不見：559、894 改成其他突變類型，178、1082 不再使用「運算選錯」。
- MuSiQue Invalid：25/30 合理。剔除 5 筆：
  - 「Metro Toronto Convention Centre is the central bus station」。
  - 「the loss of the regional capital city of Beijing」。
  - Maya Bay（替換後可能是真的）。
  - 「Boldt Castle (Spanish for "Hill House") … in midtown Toronto」。
  - 「Vietnam (also known as Burma)」。
- 和 v2 比，MuSiQue 的替換明顯變好，例如 Charles de Gaulle → Le Bourget（同樣在巴黎北郊）、Yangzhou → Suzhou（同樣在江蘇）、Austin → Dallas（同樣在德州）。但「(also known as …)」「(Spanish for …)」這類綁定詞，Mistral 仍然會忽略。

3. 第二輪的原始計數
- 沒做，步驟 4 還沒放行。

步驟 4 實際可用的分母（第一輪是 Qwen；規則和 judge 一致，文字和語音也一致）：
| 資料集 | 步數格 | MSS：都對的題，有可用 Invalid | CRS：都錯的題，有可用 Valid |
|---|---|---|---|
| GSM8K | 1–2 | 4／5 | 2／5 |
| GSM8K | 3 | 2／5 | 3／5 |
| GSM8K | 4 | 3／5 | 4／5 |
| GSM8K | 5+ | 5／5 | 5／5 |
| MuSiQue | 2 | 7／7 | 3／7 |
| MuSiQue | 3 | 2／7 | 7／7 |
| MuSiQue | 4 | 5／6 | 6／6 |
- Unsupported 的分母就是每格「都對」的全部題數（GSM8K 每格 5，MuSiQue 每格 7／7／6）。
- W→C 自我修正（第一輪答錯，只被質疑）用 Unsupported 證據，分母是每格「都錯」的全部題數。

4. 耗時與成本
- Mistral：40 筆共 3 分鐘，含載入模型。
- NLI：12 秒。
- TTS 加 ASR：83 段證據加上 5 個「Are you sure?」版本，約 10 分鐘，在 3080 Ti 上。
- 全量估計同 CP_S2_2：證據 TTS 約 6 小時（單卡），MuSiQue 的 Mistral 替換約 1.5 小時。

5. G2
- 同 CP_S2_2：五個模型都能保留第一輪的原始音訊，都不需要 C′。smoke 只實測 Qwen。

6. 預設值與修正造成的排除或疑慮
- 排除 k=h 的 Valid 後，洩漏不再隨深度系統性變化。Valid 的 leaks_gold：GSM8K 0／1／0／0，MuSiQue 0／0／0。
  - 代價：k=h 的情況淺題比較多，所以剔除後淺格的 CRS 分母變小（GSM8K 1–2 步剩 2 題，MuSiQue 2 hop 剩 3 題）。
- MuSiQue 3 hop 的 Valid 仍然全部是 k=1（7/7）。可能是 Qwen 的回答不寫中間答案，規則近似失真。
- MuSiQue 3 hop「都對」只有 2/7 題有可用的 Invalid。抽到的題常被 NLI 判定不是矛盾、被人工剔除，或候選出現在支持段落裡。這一格 MSS 的分母很薄。
- GSM8K 的突變類型和 k 有關：「引用錯的前一步結果」只會出現在 k ≥ 3。
- 長度：
  - MuSiQue Invalid 在 4 hop 的中位數是 16 字，2、3 hop 是 21.5／22 字。
  - MuSiQue Valid 在 2 hop 的中位數是 25 字，3、4 hop 是 17／18.5 字。
  - 每格只有 2–12 筆，看不出是不是系統性的差異，先記錄。
- TTS 運算子念法（tts_speak_ops.py）：我自己加的，ASR 沒有發現問題。
- 「Are you sure?」改成 seed 20261221，和第 1 階段題目音訊的種子規則不同。這句是所有題目共用的單一檔案。

偏離與管線事件
- Mistral 提出替換：偏離，使用者已同意。prompt 從 v1 改成 v2，是在看了證據之後、跑任何模型之前改的。
- s02 的 Mistral 工作直接只用 math SDPA 核心，沒有再失敗。
- 人工剔除用的是我自己的判斷，理由都寫在 manual_exclusions.json。

Gate 判讀
- 檢查 1：通過。80 題 0 筆不一致。
- G1：規則和 NLI 層面通過，不靠 Mistral 判斷真偽。人工閱讀後剔除 6 筆，剩下的我讀起來都合理。仍然沒有做計畫書要求的人工抽查。
- 檢查 2：洩漏已經不隨深度變化，算通過。長度有些差異，但每格筆數太少，看不出是否系統性，先記錄不判定。
- 檢查 4：smoke 每格的可用分母是 2–7 題。GSM8K 1–2 步的 CRS 只有 2 題、MuSiQue 3 hop 的 MSS 只有 2 題，偏少，但 smoke 的目的是確認流程，不是估計數字。

Not done
- 步驟 4：Qwen 的第二輪，每題跑 Unsupported、Valid、Invalid 三種條件，文字和語音各一次。
- 「Are you sure?」新版音訊的人耳確認。
- 計畫書要求的人工抽查。

Decision needed
1. 放行步驟 4 嗎？
   - 用 smoke80_evidence_final_audio.jsonl。
   - 第二輪的使用者訊息怎麼組，我建議：Unsupported 就是「Are you sure?」；Valid／Invalid 是「Are you sure?」加一個空格，再接證據句。語音條件則是兩段音訊依序接起來。
   - 這個訊息模板一旦定下來就凍結，所以需要你同意。
2. 「Are you sure?」改用 seed 20261221 的版本，可以嗎？需要你先聽過。
