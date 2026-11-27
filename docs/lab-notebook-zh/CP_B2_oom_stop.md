Checkpoint: CP_B2 smoke 80 基線中途停止（記憶體不足，必停條件）

What ran:
- Kokoro TTS（hexgrad/Kokoro-82M、kokoro 0.9.4、聲音 af_heart、24 kHz）：120 段全部完成（80 題題目＋40 段 MuSiQue 段落）。
- Whisper large-v3 抽查 GSM8K 40 題題目音訊：完成，結果在戰艦 ~/rq4_v2/out/asr_check_gsm8k40.jsonl。
- Qwen2.5-Omni-7B 基線：
  - 第 1 次（410349）被分到 20GB 的 RTX 4000 SFF，載入時就記憶體不足，0 筆輸出。
  - 第 2 次（410380）在 24GB 的 RTX 3090 上跑完 94 筆後記憶體不足，工作結束。

Raw data:
- 已完成的 94 筆：~/rq4_v2/out/baseline_smoke80_qwen25omni.jsonl（A_a 19、C_a 19、A_bc 19、C_b 19、C_c 18；全部是 MuSiQue，GSM8K 還沒開始）
- 失敗的那一筆：MuSiQue 3hop2__132957_51933_40768 的 C_c（段落音訊 175.03 秒＋題目音訊）。
  錯誤：torch.OutOfMemoryError，在 attention 加 mask 時要多配置 3.11 GiB，GPU 23.56 GiB 只剩 3.08 GiB。
  紀錄檔：~/rq4_v2/logs/baseline_qwen80.log；第 1 次的紀錄檔：logs/baseline_qwen80_oom_rtx4000.log
- 已完成的 94 筆中，輸出被截斷（1024 tokens 用完）的有 3 筆；目前最長的輸入是 4,097 個 token。

Computed results: 還沒算分（資料不完整）。

Anomalies:
- 模型本身約 20 GB，3090 只剩約 3.5 GB 給計算。語音條件 (c) 的段落音訊最長約 4.7 分鐘，attention 的記憶體會隨長度平方增加，24 GB 的卡跑不完 (c)。
- 已完成的 94 筆是在 3090 上跑的；如果剩下的改在另一種卡上跑，同一批 smoke 裡會混用兩種 GPU（bf16 的數值可能有微小差異）。

Not done: GSM8K 80 筆、MuSiQue 剩下 106 筆、算分、報告。沒有自動重跑。

Decision needed（二選一，都只換硬體或實作，不動已凍結的解碼設定）:
1. 全部 280 筆改在一張 48 GB 的卡（RTX6000Ada 或 RTXA6000）上從頭重跑，同一批 smoke 只用一種卡（建議）。之後全量也需要 48 GB 的卡才能跑 (c)。
2. 保留已完成的 94 筆，只把剩下的 186 筆放到 48 GB 的卡上續跑（較快，但混用兩種卡）。
（另一種做法是把 attention 改成 sdpa 來省記憶體，但這會改推論實作，我不建議在這裡改。）
