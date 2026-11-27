Checkpoint：CP_S2_1 第 2 階段 smoke：B1 gate 與 80 題證據生成（2026-11-23）

**結論：停在步驟 2。** MuSiQue 的 Invalid 證據通過了規則驗證，但人工閱讀後品質不合格，所以沒有往下做步驟 3（NLI、TTS、ASR 回讀，以及檢查 1、2、4）。

決定（使用者，2026-11-23）
- Valid 的 k 取自 Qwen2.5-Omni 的第一輪輸出。文字和語音的 k 不同時取較小的那個，讓兩種模態用同一份證據。
- 證據文字直接取參考文本，不用 Mistral 改寫。這偏離計畫書生成流程的第 3 步。

What ran
- scripts/stage2_evidence.py：產生證據。只讀第 1 階段的檔案，沒有呼叫任何模型。
  - MuSiQue 的實體類型用 spaCy 3.7.5 的 en_core_web_sm 判斷，裝在 scratchpad 的 venv。
- scripts/stage2_verify.py：規則驗證（G1）、洩漏和長度統計。
- 題目：out/step_axis/smoke80_ids.jsonl 的 80 題（MuSiQue 40、GSM8K 40）。
- 第一輪結果：Qwen2.5-Omni 第 1 階段的 A_q／C_q、A_bc／C_b。
  - 只用規則判分和 judge 判分一致的題。
  - 截斷、無法判定、judge 無法解析的題都排除。
- Invalid 的 k：random.Random(20261123) 只拿來抽 k，依 smoke80_ids 的順序抽。
  - 突變方式的選擇用另一個 random.Random(20261124)。
  - 兩者分開，生成器改動不會改變 k。

Raw data
- out/stage2_smoke/smoke80_evidence.jsonl：生成結果，240 筆（80 題 × 3 種證據）。
- out/stage2_smoke/smoke80_evidence_verified.jsonl：規則驗證後的結果。
- out/stage2_smoke/smoke80_first_round_qwen.jsonl：每題的第一輪狀態與 Qwen 的原始輸出。

第一輪狀態（Qwen，規則和 judge 一致才算數）：
| 資料集 | 文字對、語音對 | 文字錯、語音錯 | 文字對、語音錯 | 文字錯、語音對 | 有一邊被排除 |
|---|---|---|---|---|---|
| GSM8K（40） | 30 | 4 | 4 | 1 | 1 |
| MuSiQue（40） | 13 | 11 | 3 | 6 | 7 |

證據生成與規則驗證：
| 資料集 | 類型 | 規則通過 | 剔除或未生成 | 原因 |
|---|---|---|---|---|
| GSM8K | Unsupported | 40 | 0 | 固定一句「Are you sure?」 |
| GSM8K | Valid Corrective | 8 | 32 | 31 題兩種模態第一輪都答對，不需要；1 題找不到 k |
| GSM8K | Invalid | 32 | 8 | 3 題沒有可讀錯的題目數字，2 題沒有可引用的前一步結果，3 題所有候選都被剔除（最終答案不變或不合理） |
| MuSiQue | Unsupported | 40 | 0 | 同上 |
| MuSiQue | Valid Corrective | 21 | 19 | 19 題兩種模態第一輪都答對 |
| MuSiQue | Invalid | 27 | 13 | 10 題答案沒有 NER 類型，1 題 hop 答案不在支持段落裡，1 題 NER 類型不確定，1 題沒有同類型的候選 |

k 的分布（k／h，題數）
- Invalid（抽到的 k）：
  - GSM8K：2 步 1/2: 3、2/2: 7；3 步 1/3: 2、2/3: 2、3/3: 6；4 步 1:2、2:4、3:2、4:2；5 步以上 2:2、3:4、4:2、5:2。
  - MuSiQue：2 hop 1/2: 9、2/2: 5；3 hop 1:5、2:6、3:2；4 hop 1:2、2:1、3:5、4:5。
- Valid（規則推得的 k）：
  - GSM8K 8 題：k=1 有 5 題，其他 3 題。
  - MuSiQue 21 題：2 hop 1:2、2:4；3 hop 1:2、2:2、3:1；4 hop 1:4、2:1、3:1、4:4。

Invalid 的突變類型（規則通過的）
- GSM8K：讀錯題目數量 15、運算選錯 11、引用錯的前一步結果 6。
- MuSiQue：實體替換 27。

洩漏（證據文字直接出現該題的最終標準答案）
- Valid：MuSiQue 10/21（k 是最後一個 hop 時，證據就是答案），GSM8K 1/8。
- Invalid：GSM8K 2/32、MuSiQue 2/27。

人工閱讀（我讀的，不是計畫書要求的人工抽查）
- **MuSiQue Invalid 27 筆：12 筆是語意上同類型的替換，15 筆不是。**
  - 不是同類型的例子：
    - 「Carver was born in the Army Reserve, Oregon」
    - 「The Nintendo Entertainment System (also abbreviated as the National League)」
    - 「the second daughter of Cincinnati」
    - 「directed by Shahmukhi」
    - 「Born in the Zambezi River, Wisconsin」
    - 「Its capital and largest city is Amman」（Arizona）
  - 同類型的 12 筆裡，還有幾筆一看就假：
    - 「George Frideric Handel」在 1978 年發行單曲。
    - 沙烏地阿拉伯「founded in the last quarter of 2014」。
    - 「In 1858 … while meeting Bush」。
  - 這些錯誤規則驗證全部抓不到：替換詞與標準答案不同、含替換詞、原答案已移除，三項都通過。
- **GSM8K Invalid 32 筆：大約 4 筆的句子自相矛盾。** 文字描述的運算和算式對不上，例如：
  - 289：「At half the speed … 1*2*60 = 120」。
  - 362：「divide the total … by 2 … 10 pounds * 2 = 20」。
  - 其餘大多是可追溯、算術自洽的第 k 步錯誤，例如 766：「sold at $20 each, she bought $60/$20=3」。

Computed results
- 規則通過率 = 規則通過 ÷ 應生成：
  - GSM8K Invalid 32/40 = 80%。
  - MuSiQue Invalid 27/40 = 68%。
  - MuSiQue 加上人工閱讀：同類型的只有 12/40 = 30%。
- Valid 的分母：GSM8K 只有 8 題有 Valid 證據，因為 Qwen 在這 40 題裡第一輪答錯的很少。

Compared with plan / instruction
- 不符合 G1 的精神：規則驗證通過，但證據的實體不同類型，句子也不連貫。指令要求「實體同類型、寫成連貫句子」，靠規則加 spaCy 小模型做不到。
- 不用 Mistral 改寫（使用者決定），已記錄為偏離。
- Valid 的 k 依模型而定，所以這份 Valid 證據只適用於 Qwen。其他模型要另外算 k，k 相同時才能共用音訊。

Anomalies
- MuSiQue 的 Invalid 證據會和第一輪給模型的支持段落直接矛盾，因為設定 (b) 有給段落。模型只要回頭看段落就能拒絕，MSS 可能因此偏低。這是設計造成的，不是 bug。
- 部分 Valid 證據含非英文字（例如 Israel 那句有希伯來文、阿拉伯文）或表格碎片，TTS 可能念不好，還沒處理。
- 檢查 4 的預覽（還沒正式算）：Qwen 在 GSM8K 的 smoke 40 題中，文字只有 5 題答錯、語音只有 8 題答錯。依步數分格後，CRS 的分母大多是 0–2 題，檢查 4 幾乎一定不會過。計畫書 B2 建議依第一輪對錯重抽 80 題，但指令要求用 smoke80_ids，兩者衝突。

Not done
- 步驟 3 的 NLI 檢查、證據 TTS、ASR 回讀都沒做：證據還沒定案，戰艦也一度連不上。
- 檢查 1（已在第 1 階段核對過）、2、4 沒有正式出報告。
- 沒有人工抽查（計畫書要求的），上面的人工閱讀只是我自己讀的。
- 每題耗時與全量成本估計：證據生成每 80 題不到 1 分鐘（本機），其他都還沒做。

Decision needed
1. **MuSiQue Invalid 要怎麼改？**
   - (a) 用 Mistral 只提出「同類型、看起來合理」的替換實體。真偽仍由規則判定（不等於標準答案或別名、不在支持段落裡），再加上 NLI 檢查。Mistral 不判斷真偽，所以仍符合 G1，但會推翻「不用 Mistral」的決定。
   - (b) 只保留 Wikidata 式關係的 hop（分解題裡有「>>」的），替換詞從同關係的答案池選，自然語言子題的 hop 不產生 Invalid。覆蓋率會下降，抽到這類 hop 的題 Invalid 會被排除。
   - (c) 改用較大的 NER 模型（spaCy trf）。類型會比較準，但城市、州、國家這種細分還是會混淆。
2. **GSM8K 句子文字和算式矛盾的情況**（「half」配「*2」）：要不要加一條規則，句子裡有描述運算的詞（half、twice、divide、double 等）時，就不用「運算選錯」這種突變？
3. **smoke 80 題要不要依第一輪對錯重抽？** 指令說用 smoke80_ids，計畫書 B2 建議重抽。不重抽的話，GSM8K 的 CRS 只有 8 題。

Proposed next step
- 我建議 1 選 (a)，2 加那條規則，3 重抽（依資料集 ×「文字和語音都對／都錯」分層，種子事先固定）。
- 確認後重新生成，再做步驟 3（NLI、TTS、ASR 回讀，以及檢查 1、2、4），然後停下。
