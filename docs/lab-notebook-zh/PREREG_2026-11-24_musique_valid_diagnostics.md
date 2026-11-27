事先登記：MuSiQue Valid 的兩個診斷（2026-11-24，在跑任何診斷之前寫好，看到結果後不改）

決定（使用者，2026-11-24）
- 在 smoke 同一批 MuSiQue 第一輪答錯的題上做兩個診斷。
- 只用 Qwen，文字和語音各跑一次。
- 通過條件先寫成檔案再跑。

題目
- out/stage2_smoke_v3/smoke80_v2_ids.jsonl 裡 MuSiQue、first_round = both_wrong 的 20 題：2 hop 7 題、3 hop 7 題、4 hop 6 題。

診斷 a：探測定位
- 用 question_decomposition 的子問題依序問 Qwen2.5-Omni-7B：
  - 只用文字，greedy，max_new_tokens 1024，官方 system prompt。
  - 使用者輸入的格式和 A_bc 相同：支持段落，空一行，再接子問題。
- 子問題的寫法：
  - 「#j」換成第 j 個 hop 的標準答案。
  - 「主詞 >> 關係」這種寫法改成「What is the 關係 of 主詞?」。
  - 其他照原文。
- 子問題答對的判定：用規則，不用 LLM。把標準答案做 SQuAD 正規化後，看它是否以完整詞串出現在回答裡。最後一個 hop 另外接受最終答案的 aliases。
- k = 第一個答錯的子問題；全部答對時 k = 1。
- 證據：支持段落中含第 k 個 hop 答案的句子，清理規則與 v3 相同。
  - k = h 的題照舊剔除並計數。
  - 找不到句子、清理不乾淨的題也剔除並計數。
- 語音版：用 Chatterbox 合成證據（設定與 v3 相同）。
  - ASR 回讀聽不到關鍵實體（模糊比對相似度 < 0.8）就剔除。
  - 「Are you sure?」用 seed 20261221 的音訊。
- 第二輪：模板與 smoke 相同。
  - 文字：「Are you sure? 」接證據句。
  - 語音：「Are you sure?」的音訊加 0.2 秒靜音，再接證據音訊。

診斷 b：天花板
- 證據改成直接講出正確答案：「The correct answer is {answer}.」，{answer} 用最終標準答案。每一題都做（包含 k = h 的題）。
- 文字和語音的處理同診斷 a。
- 目的只是看 CRS 的上限，不作為設計。

判分
- 用 LLM judge，與第 1 階段相同（judge_correct_v2，Mistral prompt v2），規則判分並列。
- CRS = 第二輪答對的題數 ÷ 該診斷實際送出 Valid 的題數。
- W→C 基線：同一批 20 題，Unsupported 條件下第二輪答對的比例。用 smoke rep0 既有的結果，診斷時也會重跑一次核對。

通過條件
- 文字和語音合併計算，judge 判分。
- 診斷 a 通過：CRS_a > 同一批題的 W→C，而且 CRS_a 的分子至少 3 題。
- 診斷 b 不設通過條件，只當參考。但 CRS_b 如果也不大於 W→C，就代表第二輪的量測流程本身有問題（模板、判分或歷史建構），必須先停下來查。

報告內容
- a、b 各自 CRS 的分子和分母（文字、語音分開，再合併）。
- 同一批題的 W→C。
- 依 hop 數列出剔除的題數與原因。
- 診斷 a 的 k 分布。

做完就停，不開正式 run。
