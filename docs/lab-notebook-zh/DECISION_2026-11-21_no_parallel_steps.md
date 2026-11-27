Decision (使用者，2026-11-21)：不跑平行步數。

- 原本計畫把平行步數當輔助軸，主軸是總步數：GSM8K 用 <<>> 數，MuSiQue 用 hop 數。
- 之後的分析與報告都不再用平行步數：不做依平行步數的分組表，迴歸也不放這個變項。
- 既有檔案不改：out/step_axis/item_steps.jsonl 和 scored_*.jsonl 裡的 parallel_steps 欄位保留，只是不再使用。
- 不受影響：總步數軸、長度四分位、目前在跑的全量 TTS（410577–410579）。
