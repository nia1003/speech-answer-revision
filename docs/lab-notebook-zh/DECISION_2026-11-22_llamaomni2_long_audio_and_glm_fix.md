決定紀錄（2026-11-22）

1. LLaMA-Omni2 音訊超過 30 秒的 5 題
- 題目：GSM8K 144、640、1077、1199、1209 的 C_q，音長 31.5–37.1 秒。
- 使用者：「都用切30秒看他會怎樣 反正要有跑的結果」。
- 做法：scripts/baseline_others.py 新增 LONG_MODE 環境變數，預設是 skip，主跑不受影響。
  - chunk：每 30 秒切一段，每段補滿 30 秒後分別編碼，依序接起來放進同一個語音位置。LLaMA-Omni2 的 arch 支援多個 speech token。
  - trim：官方前處理原樣（whisper.pad_or_trim），只取前 30 秒。
- Job 410739 輸出 out/long5_llamaomni2_{chunk,trim}_sdpa.jsonl。
- 主結果用 chunk 版，補進 LLaMA-Omni2 的 C_q，讓五個模型題目一致。trim 版當參考。
- 限制：LLaMA-Omni2 沒有用多段輸入訓練過。

2. GLM-4-Voice 修正（使用者：「能修正就修正」）
- v1 smoke 的問題：
  - 解碼時語音 token 一起解出再刪掉，留下一大段空白，把單字切開（例如 "Ta␣␣␣iping"）。
  - 文字講完後，模型繼續生成語音直到 3,072 上限，速度很慢。7 筆「截斷」其實文字都完整，是語音把預算用完。
- 修正：
  - 只解碼文字 token。
  - 連續 78 個語音 token 就停止（v1 smoke 中，文字內每段語音都剛好 26 個）。greedy 下停止前的文字不變。
  - truncated 改成「文字未完就到上限」。
- v1 程式備份：scripts/baseline_others_v1_20261121.py。
- v2 smoke：job 410738，輸出 out/smoke80_glm4voice_v2_sdpa.jsonl。
- GLM 全量 410638–410640 先 hold，等 v2 smoke 檢查完再放行。410734（Kimi shard 2）暫時 hold，讓 smoke 能拿到 GPU。
