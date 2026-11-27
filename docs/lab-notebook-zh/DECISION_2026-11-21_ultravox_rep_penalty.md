決定紀錄：Ultravox repetition_penalty 維持 1.0（2026-11-21）

- 決定（使用者）：「維持 1.0」。
- 背景：
  - Ultravox 官方 pipeline 預設 repetition_penalty 為 1.1。
  - baseline_ultravox.py 為了與 Qwen 一致（純 greedy），用 1.0。
  - smoke 80（200 筆）有 6 筆因重複迴圈被截斷：
    - A_a 4 筆、A_bc 1 筆、A_q 1 筆。
    - 主分析會用到的 4 種 run（A_q、C_q、A_bc、C_b）合計 2/160。
- 影響：
  - 五個模型的解碼都是 greedy，不加 repetition penalty。
  - 截斷的題數照實報告，判為答錯。
  - 與官方預設不同，這點寫進模型盤點與限制。
- 全量 410624–410626 已用 1.0 執行，不需要重跑。
