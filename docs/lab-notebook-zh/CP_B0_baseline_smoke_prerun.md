Checkpoint: CP_B0 第 1 階段步驟 1（smoke 80 題基線）跑之前的確認

What ran（沒有呼叫任何模型、沒有合成任何音訊）: 盤點戰艦上的 TTS、可用 GPU、舊 RQ4 用過的 TTS；
估算 80 題中 MuSiQue 40 題在 grounded 設定下的長度。

Raw data:
- 戰艦 HF 快取裡跟 TTS 有關的：IndexTeam/IndexTTS-2（資料夾只有 4K，權重沒有下載）、myshell-ai/MeloTTS-Chinese（中文模型）。
- 戰艦 miniconda 的 21 個 env、rq4_dualcheck 的 5 個 env、rq4_Ajudge env：都沒有裝 TTS 套件（chatterbox、kokoro、cosyvoice、f5-tts、melotts、piper、edge-tts、coqui 都查過）。系統沒有 espeak。
- 舊 RQ4 的題目與施壓音訊：Chatterbox 做聲音複製
  （Speech-Reseach/start_rq4_synthesis.sh：conda env speech-research-chatterbox；rq4_audio_many/manifest.json："CREMA-D neutral, cloned with Chatterbox"）。
  參考人聲在舊實驗室伺服器的 RQ2 voice_corpus，戰艦上只有合成出來的結果（~/rq4_dualcheck/data/question_audio/male_middle_us_voice1/）。
- GPU（11/20 下午）：3090 在 s03、s05 全部佔用；48GB、96GB 的卡全部佔用；空著的只有 3080Ti（12GB）×3、TITAN RTX（24GB，不支援 bf16）×2。
- MuSiQue smoke 40 題：題目字元中位數 108；supporting 段落字元中位數 1,762，最長 3,905；20 段全部的中位數 9,701。

Computed results:
- 以約 15 字元／秒估語速：question-only 的題目音訊約 7 秒；加上 supporting 段落約 125 秒，最長約 279 秒。
- 現有推論腳本裡，LLaMA-Omni2 會 whisper.pad_or_trim 把音訊截到 30 秒。grounded 的語音條件在這個模型上會被截斷，除非改輸入方式。

需要你決定 1：TTS（建議第一個）
| 選項 | 優點 | 缺點 |
|---|---|---|
| Kokoro-82M（Apache-2.0，固定預設聲音） | 很快、輸出固定（同一段文字每次一樣）、不需要參考人聲；全量 3,736 題只要合成一次，五個模型共用 | 要新建 env、下載權重（約 330MB）；數字、$、% 的唸法要先抽查 |
| Chatterbox（MIT，聲音複製） | 舊 RQ4 用的就是它，聲音可以延續 | 需要參考人聲（舊的 RQ2 voice_corpus 不在戰艦上）；有取樣隨機性要固定種子；比 Kokoro 慢 |
| Gemini TTS（gemini-2.5-flash-preview-tts，雲端 API） | 戰艦 ~/.bashrc 已有 GEMINI_API_KEY；RQ4 C 實驗用過（colab_rq4_C/build_nb.py：REST 呼叫、8 個預設聲音、合成後逐字驗收），程式可直接改用；不佔 GPU；品質高 | 預覽版模型可能下架或更新，重現性差；同一段文字每次合成不一定一樣；有配額與費用；題目文字會送到 Google（題目是公開資料集） |
| IndexTTS-2 | 品質高 | 權重沒下載、模型大、需要另外裝它的 repo |
| MeloTTS-Chinese、edge-tts | — | 前者是中文模型；後者要把題目送到微軟的線上服務，重現性差，不建議 |
不論選哪一套，合成後都會記錄每題音訊秒數，並抽查 GSM8K 的數字唸法。

需要你決定 2：MuSiQue 用 grounded 還是 question-only（等你回覆，我不預設）
- question-only：題目短（約 7 秒），測的是「模型自己知不知道這些事實並串起來」。
- grounded（只給 supporting 段落）：每題音訊約 2 分鐘，最長約 4.7 分鐘；LLaMA-Omni2 目前的輸入方式會截到 30 秒；
  但它比較接近「推理鏈長度」而不是「知識有沒有」。若選 grounded，還要決定語音條件裡段落是否也用語音唸。

需要你決定 3（計畫沒寫，和現有腳本有關）: 解碼設定
- 計畫「模型與推論設定」只列了要記錄的欄位，沒有給數值。現有腳本（build_nb_A.py 的 Qwen）是：
  貪婪解碼、max_new_tokens 256、Qwen 官方 system prompt、talker 關閉、使用者訊息只有題目（文字或音訊），沒有其他指示。
- 照你的要求我不會自己改。但 GSM8K 若模型逐步算，256 tokens 可能截斷，而截斷是必停條件。要沿用 256，還是改成例如 1024？
- 也沒有要求「最後一行給答案」的提示；GSM8K 用「最後一個數字」規則抽取，模型若在結尾補一句說明，可能抽錯。

Not done: 沒有裝 TTS、沒有合成、沒有跑 Qwen。

Proposed next step: 你決定 1–3 後，我建 TTS env、合成 80 題（記錄秒數），在空出的 24GB 以上的卡上跑 Qwen2.5-Omni-7B 的 C 與 A，停在步驟 1 報告。
