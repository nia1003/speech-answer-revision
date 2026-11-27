Checkpoint：CP_S2_2 第 2 階段 smoke：重抽 80 題、證據 v2、驗證、TTS／ASR、離線檢查（2026-11-23）

照使用者 2026-11-23 對 CP_S2_1 的六項決定執行，做到步驟 3 為止。沒有跑任何受測模型的第二輪。

決定（使用者）
1. MuSiQue Invalid：句子取參考文字，替換實體由 Mistral 提出；真偽由規則加獨立 NLI 判定。記為偏離。
2. GSM8K：句子有描述運算的詞時，不用「運算選錯」。
3. 依第一輪狀態重抽：資料集 ×（都對／都錯），每格 20 題，深度分散，種子先寫進檔案再抽。
4. 證據檔加 leaks_gold 欄位，洩漏的題先不剔除。
5. Valid 證據有非英文字或表格碎片時先清掉，清不掉就剔除並計數。
6. 重新生成後再人工讀一次所有通過的 Invalid，並列出突變類型 × k 的交叉表。

What ran（腳本都是新檔，第 1 階段的輸出只讀）
- 重抽：
  - out/stage2_smoke_v2/resample_config.json 先寫好（種子 20261123、配置、不足時的規則），再跑 scripts/stage2_resample.py，得到 smoke80_v2_ids.jsonl。
- 證據：
  - scripts/stage2_evidence_v2.py 產生證據。
  - scripts/stage2_mistral_subs.py 讓 Mistral 提出替換實體：Mistral-Small-24B @ 9527884b、bf16、greedy、max_new_tokens 160，40 筆請求，job 411326。
  - scripts/stage2_verify_v2.py 做規則驗證。
  - scripts/stage2_nli.py 做 NLI：FacebookAI/roberta-large-mnli @ 2a8f12d2，job 411327。
  - 最後合成 smoke80_evidence_final.jsonl。
- 音訊：
  - scripts/tts_evidence_cbx.py：Chatterbox，設定、種子、說話者都和第 1 階段相同。
  - scripts/asr_evidence.py：Whisper large-v3 回讀。
  - job 411329，s02 的 3080 Ti。
- 離線檢查：scripts/stage2_offline_checks.py，結果在 out/stage2_smoke_v2/offline_checks.txt。

Raw data（out/stage2_smoke_v2/）
- smoke80_v2_ids.jsonl：80 題。
- resample_population_counts.json：母體各格的題數。
- mistral_requests.jsonl、mistral_proposals.jsonl：40 筆請求與 Mistral 的原始輸出（每筆 5 個候選）。
- smoke80_evidence.jsonl → smoke80_evidence_verified.jsonl → smoke80_evidence_final.jsonl。
- nli.jsonl：NLI 的雙向機率。
- evidence_audio/manifest.jsonl、evidence_audio/asr.jsonl。音訊本身在戰艦 ~/rq4_v2/out/stage2_smoke_v2/evidence_audio/audio/，共 103 個檔。
- smoke80_first_round_qwen.jsonl：80 題的第一輪狀態與 Qwen 的原始輸出。

1. 每個步數格的題數；k 的分布

重抽（Qwen 第一輪；規則和 judge 一致，文字和語音一致）：
| 資料集 | 狀態 | 各步數格 | 母體題數 |
|---|---|---|---|
| GSM8K | 都對 | 1–2／3／4／5+ 各 5 題 | 337／268／190／140 |
| GSM8K | 都錯 | 各 5 題 | 20／35／37／34 |
| MuSiQue | 都對 | 2／3／4 hop 為 7／7／6 題 | 611／274／118 |
| MuSiQue | 都錯 | 7／7／6 題 | 303／195／146 |

每一格的母體都夠，不需要改用「不足時」的規則。

突變類型 × k（只算通過的 Invalid）：
| GSM8K | k=1 | k=2 | k=3 | k=4 | k=6 | 合計 |
|---|---|---|---|---|---|---|
| 讀錯題目數量 | 7 | 1 | 2 | 1 | 0 | 11 |
| 運算選錯 | 4 | 2 | 4 | 2 | 1 | 13 |
| 引用錯的前一步結果 | 0 | 0 | 3 | 2 | 1 | 6 |

| MuSiQue | k=1 | k=2 | k=3 | k=4 | 合計 |
|---|---|---|---|---|---|
| 實體替換 | 10 | 14 | 11 | 1 | 36 |

k／h 的明細（依步數格）在 offline_checks.txt。
- 引用錯的前一步結果在 k=1 不可能發生（前面沒有步驟）。
- MuSiQue 的 4/4 只有 1 筆：抽到 k=4 的題多數在 NLI 或生成時被剔除。

Valid 的 k（規則近似「模型錯在哪一步」）：
- MuSiQue 3 hop 的 7 題全部是 k=1。可能是因為 Qwen 的回答很短，沒有寫出中間 hop 的答案，規則就判成第一步沒做到。這是近似方法造成的，不一定是模型真的在第一步出錯。

2. 證據生成：通過率、剔除原因、找不到 k、ASR 回讀

| 資料集 | 類型 | 應生成 | 通過 | 剔除（原因） |
|---|---|---|---|---|
| GSM8K | Unsupported | 40 | 40 | – |
| GSM8K | Valid | 20（都錯） | 16 | 4 題找不到 k（Qwen 的輸出裡有標準解答每一步的結果） |
| GSM8K | Invalid | 40 | 30 | 8 題沒有可用的突變（沒有可讀錯的數量，或沒有可引用的前一步）；2 題所有候選都不合理 |
| MuSiQue | Unsupported | 40 | 40 | – |
| MuSiQue | Valid | 20（都錯） | 20 | 清理後沒有剔除任何一題 |
| MuSiQue | Invalid | 40 | 36 | 規則 40/40 通過；NLI 4 題不是矛盾，剔除 |

- GSM8K「運算選錯」因為句子有描述運算的詞而被跳過：記錄在每筆的 tried 欄位。
- Mistral 的候選全部通過真偽規則，每題都用第一個候選。
- NLI 沒過的 4 題（前向機率）：
  - 3hop2__326964_7855_7713：entailment 0.91。反向是 contradiction 0.92，但規則事先定為看前向。
  - 4hop2__161602_…_86452：entailment 0.51。
  - 2hop__20433_157939：entailment 0.98。
  - 4hop1__60000_…：entailment 0.98。
- NLI 模型載入時出現「部分權重未初始化」的 transformers 警告，標籤對應正常，沒有另外查。

人工閱讀（我讀的，不是計畫書要求的人工抽查）

GSM8K Invalid：26/30 讀起來合理。4 筆自相矛盾：
- 559：「Subtracting … gives 20 + 4」。
- 894：「Subtracting … gives us 80 + 54」。
- 178：「4 fewer crabs than Bo, has 40+4」。運算詞清單有「fewer than」，但這句寫的是「fewer crabs than」，沒有比對到。
- 1082：「walked 2-2+4=4 miles, he walked 2 miles to the halfway point than 2 miles home」，算式後面那半句和算式矛盾。

MuSiQue Invalid：24/36 同類型且通順。12 筆有問題，原因幾乎都是句子裡還有其他描述綁著原本的實體：
- 只換了實體，其他描述沒跟著改，所以明顯矛盾（8 筆）：
  - 「Heathrow Airport, located on the edge of the northern suburbs of Paris」
  - 「Gene Wilder (born 1957) is an English actress」
  - 「Live from Nashville, TX」
  - 「The Vancouver Bus Station is … in Toronto」
  - 「Hearst Castle (Spanish for "Hill House") … in Toronto」
  - 「Vietnam (also known as Burma)」
  - 「The State of Qatar … the largest country of Arabia」
  - 「Shanghai Yaxing … based in Shanghai, Jiangsu」
- 同一句裡還留著原本的名字或對應的說法（2 筆）：
  - 「by Richard Burton and Vivien Leigh …, where Olivier and Leigh met」
  - 「Standing Rules of The House of Representatives … adopted by the United States Senate」
- 替換後在世界知識上很突兀（1 筆）：「the loss of the regional capital city of Beijing in 1853」（太平天國）。
- 替換後可能反而是真的（1 筆）：「Maya Bay」。Maya Bay 就在 Ko Phi Phi Leh 上，這句話可能仍然成立，不能算 Invalid。

ASR 回讀（Whisper large-v3）
- 共 103 個檔。音訊長度中位數 6.0 秒，最長 26.5 秒；每個檔的 TTS 平均 4.6 秒。
| 類型 | 檔數 | 關鍵詞不一致 | 真的錯誤 | WER 中位數 |
|---|---|---|---|---|
| GSM8K Invalid | 30 | 1 | 0 | 0.05 |
| GSM8K Valid | 16 | 4 | 0 | 0.09 |
| MuSiQue Invalid | 36 | 2 | 0（專有名詞拼法：Zanuck→Zonick、Gene→Jean） | 0.00 |
| MuSiQue Valid | 20 | 3 | 1 | 0.04 |
| Unsupported | 1 | 1 | 待確認 | – |
- GSM8K 的 5 筆不一致都是比對程式的問題：「one point five」被拆成 1 和 5，ASR 其實聽成 1.5，所以沒有真的錯誤。
- MuSiQue Valid 唯一真的錯誤是 2hop__20433_157939。Chatterbox 在 26 秒的長句裡漏念了「satire (Howard the Duck)」等片段，而這題的關鍵實體就是 Howard the Duck，所以這段音訊不能用。另外兩筆只是專有名詞拼法不同（Forlani→Ferlani、Columbia→Colombia）。
- **Unsupported 那一句「Are you sure?」（0.84 秒）被 ASR 聽成「You sure?」**。所有題目都共用這一段音訊，需要人耳確認「Are」有沒有念出來。

3. 第二輪各條件的原始計數、MSS、CRS
- 沒做。步驟 4（Qwen 第二輪）要等你放行。
- 第一輪（第 1 階段，Qwen）：
  - GSM8K 都對 20、都錯 20。
  - MuSiQue 都對 20、都錯 20。

4. 耗時與全量成本（估計）
- 本機生成證據：80 題不到 1 分鐘。
- Mistral 提出替換：40 筆共 3 分鐘，其中載入模型約 1.7 分鐘，每筆約 2 秒。
- NLI：12 秒。
- TTS 加 ASR：103 個檔共 10.8 分鐘，在 3080 Ti 上跑。
- 粗估：全量 3,736 題證據（每題約 1.3 段音訊）在單卡上，TTS 約 6 小時；MuSiQue 2,417 題的 Mistral 替換約 1.5 小時。
- 第二輪的推論成本要等步驟 4 量到每題耗時才能估。

5. G2
- 五個模型都能保留第一輪的原始音訊，接第二段音訊（雙音軌檢查已通過），都不需要 C′。
- 這次 smoke 只會實測 Qwen。

6. 預設值造成的排除或疑慮
- Valid 的 k（規則近似）：GSM8K 有 4 題找不到 k，剔除。MuSiQue 3 hop 全部是 k=1，k 可能失真。
- Valid 的 k 落在最後一步時，證據就是答案（leaks_gold）。**洩漏會隨深度系統性變化**，在檢查 2 標為不通過：
  - GSM8K Valid：1–2／3／4／5+ 步為 2/4、1/3、0/4、0/5。
  - MuSiQue Valid：2／3／4 hop 為 3/7、0/7、0/6。
- Invalid 的 k（隨機）：GSM8K 抽到 k=1 時，「引用錯的前一步結果」不可能發生，所以 k=1 只有另外兩種突變類型，類型的分布和 k 有關。
- GSM8K 的運算詞清單沒有涵蓋「Subtracting」「fewer X than」這類說法，造成 3 筆自相矛盾。
- MuSiQue 只替換實體字串，同一句裡綁著原實體的其他描述（別名、地點、國家、性別）沒有跟著改。這種錯誤 NLI 和規則都抓不到，人工閱讀發現 11 筆。
- TTS 運算子念法：我自己加的規則（tts_speak_ops.py），把 * × = + − ÷ 改念成英文詞，只用在證據上（第 1 階段的題目幾乎沒有算式）。ASR 回讀沒有發現問題。
- 「Are you sure?」的音訊可能把「Are」念得很弱或漏掉。

偏離與管線事件
- Mistral 提出替換：記為偏離（使用者已同意）。
- Mistral 的工作因為 3090 全滿，改到 s02（4 張 3080 Ti 加 2 張 TITAN RTX，spot），失敗兩次才成功：
  - TITAN RTX（Turing）不支援 FlashAttention，也沒有 bf16 的 mem-efficient 核心。
  - 第三次只開 math SDPA 核心，模型、dtype、解碼都沒變，就成功了。
  - 三次的 log 都保留：logs/s2_mistral_subs_s02{,b,c}.log。
- 運算詞規則、渲染修正（結果數字等於運算元時不替換；結果寫成英文詞時剔除），都是在看到證據之後、跑任何模型之前改的。

Gate 判讀
- 檢查 1（步數標籤）：**通過**。80 題 0 筆不一致，抽到的題都不是沒有 <<>> 的題。
- G1（證據真偽）：**規則與 NLI 層面通過**。GSM8K 由程式重算確認；MuSiQue 由規則加 NLI 確認，不靠 Mistral。**人工閱讀不通過**：MuSiQue 有 12/36 明顯矛盾或可能為真，GSM8K 有 4/30 自相矛盾。
- 檢查 2（可比性）：**不通過**。Valid 的洩漏隨深度遞減。長度大致相近，但 MuSiQue Invalid 在 4 hop 的中位數是 17 字，2、3 hop 是 24 字。
- 檢查 4（格內樣本數）：smoke 是依設計配置的，每格 5–7 題，全部可用。全量（Qwen）的 GSM8K「都錯」母體每格只有 20–37 題，CRS 的分母會很薄。

Not done
- 步驟 4（Qwen 第二輪）。
- 計畫書要求的人工抽查與雙人標註。
- 「Are you sure?」音訊的人耳確認。
- 有問題的 16 筆 Invalid 和 1 筆 Valid 音訊還沒剔除，只標在這份報告裡，final 檔仍是 nli_passed 或 rule_passed。

Decision needed
1. 人工閱讀發現的 16 筆 Invalid（MuSiQue 12、GSM8K 4）要剔除嗎？2hop__20433 的 Valid 音訊（漏念關鍵實體）也要剔除嗎？
2. Valid 洩漏隨深度變化：要排除 k=h 的 Valid（改取模型沒做到的倒數第二步之前），還是保留並在分析中控制 leaks_gold？
3. 「Are you sure?」的音訊要重新合成嗎（換種子或句尾加停頓）？需要你先聽一下。
4. 改進生成規則，再重跑一次步驟 2–3？
   - GSM8K：運算詞清單補上 subtract、subtracting、fewer … than、less … than 等。
   - MuSiQue：要求 Mistral 同時列出句子裡綁著原實體的描述，有這類描述的句子就剔除；或改用只含單一關係的句子。
5. 放行步驟 4（Qwen 第二輪 smoke）嗎？

Proposed next step
- 我建議 1 剔除、2 排除 k=h、3 重新合成並人耳確認、4 做一次規則修正後重新生成。
- 這些都完成、人工確認後，再跑步驟 4。
