事先登記：MuSiQue Valid 證據的 ablation（2026-11-24；寫在任何模型呼叫之前，之後不改）

來源：使用者 2026-11-24 的任務說明（全程自行決定；規格沒寫的細節選最保守的做法，記在報告的「自行決定」一節）。
- 不改計畫書、第 1 階段的輸出、GO_CRITERIA 檔，也不動 GSM8K 的任何東西。
- 不用 Mistral 判斷真偽，不新增模型。
- 所有 ablation 證據只當作診斷，放在 out/stage2_ablation_musique/，不混進正式 run 的證據檔。
- V4、V5 含最終答案，只用來看上限。

## 題目集 S
- 母體：MuSiQue 中，Qwen2.5-Omni 文字條件（A_bc）第一輪答錯的題。
  - 答錯的定義：規則判分和 judge 判分都是錯。
  - 截斷、無法判定、judge 無法解析的題排除。
  - 排除 out/stage2_smoke_v3/smoke80_v2_ids.jsonl 裡的題。
- 抽樣：
  - 2、3、4 hop 各抽 40 題，共 120 題。
  - 用 random.Random(20261124)，只建一個實例。
  - 依 hop 由小到大，每層的候選依題號排序後用 rng.sample 抽。
  - 某層不足 40 題就全取，並記錄實際題數。
  - 設定寫在 S_config.json，先寫檔再抽。
- 只跑文字條件，不做 TTS。

## 協定
- 與 smoke 第二輪完全相同：
  - Qwen2.5-Omni-7B @ ae9e1690、sdpa、greedy、max_new_tokens 1024、官方 system prompt。
  - 第一輪：使用者輸入是支持段落（A_bc 格式）加問題；assistant 是第 1 階段 A_bc 的原始輸出。
  - 第二輪模板：Unsupported 是「Are you sure?」，其他條件是「Are you sure? 」接證據字串。
- 只換證據字串。
- 判分：judge_correct_v2.py（Mistral-Small-24B，prompt v2），規則判分（score_baseline_v2 的規則）並列。

## 探測
- 對 S 的每一題，用 question_decomposition 的子問題依序問 Qwen：
  - 文字、greedy、max_new_tokens 32。
  - 使用者輸入的格式與 A_bc 相同：支持段落，空一行，再接子問題。
- 子問題的寫法：
  - 「#n」換成第 n 個子問題的標準答案。
  - 「主詞 >> 關係」改寫成「What is the 關係 of 主詞?」（規格沒寫，屬於自行決定）。
- 子問題答對的判定，任一成立即可：
  - 回答與標準答案或別名在 SQuAD 正規化後完全相同。
  - 標準答案（正規化後）包含在回答裡。
  - token F1 ≥ 0.8。
  - 中間 hop 沒有別名；最後一個 hop 另外接受最終答案和它的別名。
- probe-k = 第一個答錯的子問題；全部答對（屬於組合失敗）時 k = 1。
- k = h 的題，V1、V2、V6 視為未定義並計數。

## 條件（第二輪的證據字串）
- C0 Unsupported：「Are you sure?」，沒有證據。
- C1 無關的真句子：從同一題非支持段落的句子中選一句。
  - 不能含最終答案、別名或任何 hop 的答案；清理規則與 v3 相同。
  - 用 random.Random(20261124)，依 S 的順序對每題各抽一句。
  - 沒有符合的句子就視為未定義。
- V0 現行做法：smoke 的規則 k，取第 k 個 hop 的支持句；k < h 才定義。
  - smoke 的規則 k：在第一輪答錯的模態輸出中，找第一個沒出現的 hop 答案，兩個模態取較小的 k。模態的對錯同樣要規則和 judge 一致，與 smoke 相同。
- V1：probe-k 的支持句；k < h 才定義。
- V2：「Q: <代入後的子問題> A: <該子問題的標準答案>」，用 probe-k；k < h 才定義。
- V3：第 1 到第 h−1 個 hop 的支持句依序串起來，中間用一個空格；任一句取不到或清理不掉就視為未定義。
- V4：第 h 個 hop 的支持句（含最終答案）。
- V5：「The correct answer is <標準答案>.」
- V6：「That is not correct. 」接 V1 的證據字串；V1 未定義時它也未定義。
- 支持句的取法與清理規則同 v3（hop_sentence、clean）。取不到的題視為未定義並計數。

## 指標
- 每個條件列出：N、答案不變、改成錯、改成對。
  - 對錯用 judge 判定。
  - 「改成對」：第二輪 judge 判對。
  - 「改成錯」：第二輪 judge 判錯，而且答案有改變。
  - 「答案不變」：第二輪 judge 判錯，而且答案沒改變。
  - 答案有改變的定義：第二輪 judge 的 final_answer 和第一輪（第 1 階段 judge 的 final_answer）的 token F1 < 0.5。
- W→C = 改成對 ÷ N，附 Wilson 95% 信賴區間。
- 條件之間用配對的精確 McNemar 檢定（雙尾），只用兩個條件都有定義的題，並列出配對的 N。
- 「明顯較高」= 差距 ≥ 10 個百分點，而且 p < 0.05。

## 附加檢查
- P1 第一輪純度：用別名、包含、F1 ≥ 0.8 重新判第 1 階段 judge 的 final_answer，列出其實答對的題數。若 ≥ 10%，主要指標在剩下的題上再算一次。
- P2：V0 和 C0 的第二輪回答，以「yes」「I'm sure」「I am sure」開頭（不分大小寫，去掉前導空白和標點）的比例。
- P3：依 hop 數列出每個 hop 的探測正確率、probe-k 的分布、全部答對的比例。
- P4：probe-k 和 smoke 規則 k 的一致率，只算兩者都有定義的題。

## 判讀表（結果出來後照表判讀，不事後解釋）
- V5 的 W→C < 50%：協定或判分有問題，先看 P1、P2，其他結論都不下。
- V1 比 V0 明顯較高，或 V3 比 V0 明顯較高：k 定位不準是原因之一。但 P4 一致率 ≥ 80% 時，這個解釋不成立。
- V2 比 V1 明顯較高：證據句本身不自足。
- V4 比 V1 高 ≥ 20 個百分點，而且 V1 < 10%：證據不足以改答案，模型需要看到答案。
- V0、V1、V2 都和 C0、C1 相差 < 5 個百分點，而 V4、V5 高：hop 層級的證據是惰性的。
- V6 比 V1 明顯較高：缺少語氣。
- P3 全部答對 ≥ 50%：錯在組合而不是檢索，單一 hop 的證據原則上修不了。

## 採用規則
- V1 或 V2 要同時滿足下列三項才採用：
  - W→C ≥ 15%。
  - 比 C0 和 C1 都明顯較高。
  - 不低於 GO_CRITERIA 對 MuSiQue 的 C2 門檻，也就是 W→C > C0。
- 兩者都滿足時取 W→C 較高的；平手取 V1。
- V3、V4、V5、V6 不自動採用。

## 之後的流程
- 做完 ablation 後立刻寫 CP_S2_5_valid_ablation_musique.md。
- 有採用時：
  - 對正式 run 中 Qwen 第一輪答錯的 MuSiQue 題做文字探測。這與模態無關，記為偏離，取代原本「文字與語音取較小者」。
  - 用採用的形式重新生成 MuSiQue 的 Valid 證據（仍然排除 k=h），做 TTS 和 ASR。
  - 重跑 MuSiQue smoke 的第二輪，用原封不動的 GO 條件 C1–C5 判定。全部通過才依 GO 檔開 Qwen 正式 run，沒過就停下寫報告。
- 沒有採用時：停下，不動正式 run。
- MuSiQue Invalid 的 Mistral 替換（2,268 筆）與 Valid 無關，現在就排進佇列。

## 遇到問題
- 呼叫失敗重試一次。
- 任一條件的錯誤率 > 5% 就停下回報。
- GPU 排不到就等，不換模型也不改設定。
