Checkpoint: 軌道 C 模型盤點（草稿，對應 G2）

What ran: 只讀現有推論程式 ~/Lee/colab_rq4_A/build_nb_A.py（A 雙音軌重跑用的 a_runner.py）、
戰艦 ~/rq4_dualcheck 的雙音軌檢查結果，以及戰艦 HF 快取的 revision。沒有跑任何模型。

| 欄位 | Qwen | Kimi | GLM | LLaMA | Ultravox |
|---|---|---|---|---|---|
| checkpoint | Qwen/Qwen2.5-Omni-7B | moonshotai/Kimi-Audio-7B-Instruct | THUDM/glm-4-voice-9b（+ glm-4-voice-tokenizer） | ICTNLP/LLaMA-Omni2-7B | fixie-ai/ultravox-v0_4 |
| revision（戰艦快取） | ae9e1690… | 9a82a84c… | 352e5a64…（tokenizer a5f2404e…） | 50291b44… | 335521c4… |
| 音訊進入方式 | Qwen2.5OmniProcessor，16 kHz，process_mm_info | kimia_infer 的 message_type=audio | Whisper-VQ 轉成 <\|audio_N\|> 離散 token，夾在 begin/end_of_audio | whisper.pad_or_trim（截到 30 秒）→ 128-mel，<speech> 佔位 | soundfile 讀檔、重取樣到 16 kHz，<\|audio\|> 佔位 |
| 第二輪歷史 | 第一輪題目音訊保留為音訊；r0 以文字放 assistant；質疑為第二段音訊 | 同左 | 同左 | 同左（2 段 mel） | 同左（2 個佔位、2 段音訊） |
| 被評分的答案 | 文字輸出（talker 關閉） | 文字輸出（output_type=text） | 文字（去掉音訊 token） | 文字輸出 | 只有文字 |
| 解碼 | 貪婪，max_new_tokens 256 | text_temperature 0、top_k 5，256 | 貪婪，256 | 貪婪，256 | 貪婪，256，repetition_penalty 1.1 |
| 系統提示 | Qwen 官方 SYS | "Answer concisely" | "Respond in text only, concisely" | 無 | "Answer concisely" |
| 文字端 logprob | HF generate，可取（未實測） | kimia_infer 包裝，未確認 | HF generate，可取，但要濾掉音訊 token（未實測） | HF generate，可取（未實測） | HF generate，可取（未實測） |
| 環境 | py3.11, transformers 4.52.3 | py3.11, transformers 4.51.3 | py3.11, transformers 4.44.2 | py3.10, transformers 4.43.4 | py3.11, transformers 4.46.3 |
| 即時插話 | 不支援（我們的用法） | 不支援 | 不支援 | 不支援 | 不支援 |

可以直接回答「待決定事項」的幾項：
- 「雙音軌」在 pipeline 裡的意思：第二輪輸入同時有「第一輪題目的音訊」與「質疑的音訊」兩段音訊，
  中間夾模型第一輪的文字答案。五個模型都已在戰艦檢查過（結構 2 段、複述題目 3/3、換掉題目音訊後不會跟著 r0 走），
  結果在 ~/Lee/colab_rq4_A/dualcheck_results/。這就是新計畫的條件 C（Audio→Audio），不是「語音加背景」。
- LLaMA 家族：LLaMA-Omni2-7B（Qwen2.5 骨幹），不是 LLaMA-Omni。
- Ultravox：v0_4（Llama-3.1-8B 骨幹）。計畫猜測「Ultravox 一次只傳一段 audio」不成立：我們的程式傳兩段，檢查也通過。
- 答案來源：全部是文字輸出，沒有對語音輸出做 ASR。

Anomalies / 缺口:
- revision 是戰艦快取的版本；A 實驗的 Colab 推論當時下載的是當天的 main，沒有記錄 commit，無法保證一致。
- max_new_tokens 256 是給「短答＋Are you sure」設計的；GSM8K／MuSiQue 若要逐步推理，256 可能截斷，新實驗要另定。
- 文字輸入條件（條件 A）目前五個模型都沒有寫好；Kimi 與 GLM 的文字輸入路徑要另外確認。
- 文字端 logprob 五個都還沒實際取過（H3 才需要）。

Not done: 沒有新跑任何模型；文字條件、logprob、音訊長度上限都還沒實測。

Decision needed: 確認這張表可以當 G2 的起點，或指出要換的 checkpoint。
