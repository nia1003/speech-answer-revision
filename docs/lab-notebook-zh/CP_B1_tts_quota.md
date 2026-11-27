Checkpoint: CP_B1 Gemini TTS 合成前的配額與設定確認

What ran（沒有合成任何音訊、沒有跑模型）:
- 用戰艦 ~/.bashrc 的 GEMINI_API_KEY 呼叫一次 models 清單（GET，只讀），確認金鑰有效、列出 TTS 模型。
- 核對 MuSiQue 的 is_supporting 欄位；計算全量與 smoke 要合成的文字量。

Raw data:
- 金鑰有效。可用的 TTS 模型（名稱、輸入／輸出 token 上限、version）：
  - gemini-2.5-flash-preview-tts 8192／16384 gemini-2.5-flash-exp-tts-2025-05-19（RQ4 C 實驗用的）
  - gemini-2.5-pro-preview-tts 8192／16384 gemini-2.5-pro-preview-tts-2025-05-19
  - gemini-3.1-flash-tts-preview 8192／16384
  - gemini-3.8-flash-tts 8192／16384（名稱沒有 preview）
  - gemini-3.8-flash-lite-tts 8192／16384
- MuSiQue dev：每題都有 paragraphs[].is_supporting；supporting 段落數 ≠ hop 數的題：0／2,417。
- 合成量：
  - 全量題目：3,736 次請求，561,748 字元
  - 全量 (c) 段落（若最後選 c）：2,417 次請求，3,451,046 字元；單題最長 4,215 字元
  - smoke：題目 80 次 14,419 字元；段落 40 次 68,545 字元
- RQ4 C 的程式在額度用完時會收到 "credits are depleted"，表示這把金鑰綁的是預付額度的帳戶。

Computed results（以約 15 字元／秒估）:
- 全量題目約 10.4 小時音訊；(c) 段落約 63.9 小時。
- 單題最長段落約 1,000 個輸入 token、約 4.7 分鐘音訊，在模型的 8,192／16,384 token 上限內。

Anomalies:
- API 沒有提供查剩餘額度或速率上限的端點；只有超過時的 429 錯誤才會寫出上限。所以「配額夠不夠」我無法自己確認。
- RQ4 C 的「逐字驗收」是 Whisper large-v3 轉寫後要求和原文逐字完全相同，不同就重合成，5 次都不同就丟掉。
  這對 "Are you sure?" 可行；長題目（數字、$、%、人名）幾乎不可能逐字相同，而且題目不能丟。驗收標準要重訂。

Not done: 沒有合成、沒有驗收、沒有跑 Qwen。

Decision needed:
1. 配額與費用：請在 AI Studio（https://aistudio.google.com）看這把金鑰所屬專案的層級、剩餘額度與 TTS 價格，
   確認夠「3,736 題題目」（若之後選 (c)，再加 2,417 段、約 64 小時音訊）。我無法從 API 讀到這些。
2. TTS 模型版本：沿用 C 實驗的 gemini-2.5-flash-preview-tts（2025-05 的預覽版，可能先下架），
   還是改用名稱不含 preview 的 gemini-3.8-flash-tts（較可能長期存在）？全量會只用一個版本。
3. 聲音：固定一個，建議沿用 C 實驗的 "Kore"。
4. 驗收標準：建議 Whisper large-v3 轉寫，正規化（小寫、去標點、數字統一成阿拉伯數字）後算 WER；
   WER > 0 就重合成，最多 3 次，仍不為 0 就保留 WER 最低的一份並標記 tts_mismatch，不丟題。
   GSM8K 另外人工抽聽數字、$、% 的唸法。
5. 合成時的文字：直接送題目原文，不加「請唸出」之類的指示（C 實驗的中性條件也是這樣）？

Proposed next step: 你確認 1–5 後，我合成 smoke 需要的 80 題題目＋40 段段落，驗收、記錄秒數；
GPU 空出來就跑 Qwen2.5-Omni-7B（GSM8K 2 條件、MuSiQue 3 種×2 條件），停在 smoke 報告。
