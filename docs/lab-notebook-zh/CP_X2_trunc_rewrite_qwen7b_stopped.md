Checkpoint: CP_X2 截短題改寫（Qwen2.5-7B-Instruct）品質不合格，已停止（2026-11-21）

What ran:
- 410588（1×3090，s03）：scripts/rewrite_trunc.py。
- 設定：Qwen2.5-7B-Instruct，greedy；few-shot 用 3 題 MuSiQue 2hop（拆解 → 群眾寫的問句）。
- 自動檢查兩件事：問句裡有沒有出現任何一步的答案、是不是單一問句。
- 第一次送出（410587）失敗，因為戰艦上沒有 MuSiQue dev 檔。補上傳後重送。
- 跑到第 41 筆時，我看了輸出後手動停止（scancel）。

Raw data:
- $PROJECT_DIR/out/trunc/trunc_rewritten_qwen7b_aborted.jsonl（41 筆，保留所有嘗試）。
- 自動檢查通過 29/41。但通過的題目裡，很多其實**漏掉了中間步驟**。
- 例子 1（3hop1__145290_443779_52195）：
  - 原本的鏈：
    1. Satyo Husodo 出生地 → Indonesia
    2. 和 #1 一起成立 Timor Leste Commission of Truth and Friendship 的國家 → East Timor
    3. #2 的總統 → Francisco Guterres
  - k=2 改寫成「In which country was Satyo Husodo born?」，答案會是 Indonesia，不是 East Timor。第 2 步被丟掉了。
  - k=3 改寫成「Who is the president of the country where Satyo Husodo was born?」，同樣少了第 2 步。
- 例子 2（Kemplang）：同一種錯法。
- 另外也有把答案寫進題目的（「Who is the president of East Timor?」，自動檢查有抓到），以及一句問兩個問題的。

Computed results:
- 前 16 筆中，我人工判讀有正確串起全部步驟的不到一半。
- 自動檢查抓不到「漏步驟」這種錯誤。

判讀:
- 7B 模型無法可靠地把知識庫寫法的小題（例如「#1 –Timor Leste Commission of Truth and Friendship >> country」）串成正確的問句。
- 照這個品質跑完 1,874 題，抽查一定不合格（門檻是不合格率 10%）。

沒有做:
- 沒有跑完。
- 沒有改原本的題目。
- 沒有合成任何語音。

Decision needed（改寫方式）:
(a) 換更大的模型，例如 Qwen2.5-32B-Instruct 或 72B（AWQ，48GB 卡）。few-shot 改用 3 到 4 步的例子；為了不和 S1 的題目重疊，取非直線鏈的群眾問句當例子。並且加一道自動驗證：把改寫後的問句和 k 段段落交給另一個模型作答，答案必須等於目標答案，否則重寫。
(b) 由 Claude 改寫 1,874 題，同樣加上 (a) 的作答驗證，再人工抽查 10%。
(c) 縮小範圍：只做 4hop1 的 246 條鏈（共 738 題），用 (a) 或 (b)。
