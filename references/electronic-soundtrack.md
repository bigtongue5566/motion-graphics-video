# 電子配樂與畫面同步

影片的配樂方向由敘事、情緒、空間、節奏和使用者參考決定。Electronic Music 包含舞曲、非舞曲與混合形式；不把每支影片預設為 House，也不把「緊張」等同加快四拍鼓。

## 選擇聲音語法

先確定音樂在片中的作用，再選曲風與配器。下列是可用方向，不是固定配對或曲風全集。

| 影片需要 | 可探索的方向 | 畫面可對應的聲音事件 |
| --- | --- | --- |
| 穩定律動、逐步展開 | House、Techno、Dub Techno | 主拍、切分、濾波開展、層次進出 |
| 快速資訊、動能或追逐 | Breakbeat、UK Garage、D&B、Jungle | 實際 kick/snare、碎拍空隙、樂句轉折 |
| 宏大旋律、期待與釋放 | Trance、Melodic Bass、Future Bass | 動機回歸、和聲轉折、展開與撤除 |
| 低頻重量、強烈對比 | Dubstep、Trap、Bass Music | 半拍主擊、低音包絡、留白與回應 |
| 緩慢敘事、親近或沉思 | Downtempo、Trip-hop、Chillout | 律動重心、呼吸、段落疏密 |
| 空間、懸疑、抽象或聲景 | Ambient、Drone、Electroacoustic、實驗／混合 | 質地、頻譜、空間或張力變化；可以沒有拍點 |

環境有 `electronic-music-production` 時，使用其曲風路由、音色與編曲流程；詳細曲風資料由該技能維護。本影片技能附帶的 `compose_edm.py` 是可獨立運行的 Melodic House 範本，名稱保留以相容既有專案。它不會因更改標籤或 BPM 就生成其他曲風。其他方向可用伴隨技能、現有 DAW、合成器或本案專用作曲器完成，再匯入影片。

## 共用時間表

1. 保留本片指定的精確片長，把場景、音樂段落和重要聲音／動作落點記在同一時間軸。
2. 有拍配樂記錄實際 onset、樂句與重拍。半拍、切分和 swing 不用每拍等距縮放取代；有變速時以實際 tempo map 和輸出音訊核對。
3. 自由時間配樂使用秒數：質地變化、聲音出現／消退、張力高點或空間轉換。MIDI 參考 BPM 不代表存在週期性鼓點。
4. 畫面加速、鼓細分增加、段落密度增加與 BPM 上升是不同操作。依敘事選擇；不可只把同段循環越播越快。變速後重算拍點，避免 cue 漂移。
5. 最後一個聲音事件對應最後一個主要動作，讓動作落定後有閱讀時間；保留自然釋音／空間尾音，或依本案設計乾淨的終止，再驗證最後一幀與音訊邊界。

可將本案 cue 記為 `time_seconds / sound_event / visual_event / tolerance_frames`，由本案 renderer 和 composer 讀取，或明確轉成兩者的設定。現有範本僅共用場景 start/end，**不會自動讀任意 cue JSON，也不會從外部音訊偵測鼓點**。完成後以實際影格與波形核對，不以表格當作已同步的證據。

## 匯入完成的配樂

先按本片片長完成獨立音樂專案，匯出母帶 WAV 和 `work/music-metadata.json`；伴隨技能的成品 provenance JSON 亦可使用。使用授權歌曲時提供等價來源 JSON，保留作者、來源、授權及所作剪輯。至少需有 `original_composition` 布林值，或 `composition` 來源／權利說明；這項檢查不會替你判斷授權是否合法。

建議保留的欄位：`style`、`pulse`（自由時間填 `free`）、`bpm`、`tempo_note`、`key`（如適用）、`instrument_source`、`sections`、素材來源與授權。可以省略不適用的 BPM／調性，不能憑空補寫。`sections` 若提供，使用 start/end 秒數及 role；工具會保留完整原始 JSON。

```text
uv run --project <film>/work python <film>/work/finish_video.py --project <film> --audio <music>/outputs/score-master.wav --audio-metadata <music>/work/music-metadata.json
```

`--audio` 與 `--audio-metadata` 必須同時使用。這條路徑不呼叫影片作曲器，也不重新做 loudnorm、EQ 或限幅；只轉成 48kHz stereo 24-bit PCM，再編碼為獨立 AAC 並與原畫面串流合成。來源母帶保留原檔；音量不會自動追到影片設定。

工具先解碼、檢查有效樣本及片長。只容許最多 40ms 的編碼／重採樣邊界差，補零或裁尾到精確樣本數並記錄；差距更大就停止，回音樂專案修改編曲，不自動循環或裁掉長段。影片的 `music.lufs` 應設為本案實際採用的目標；已完成配樂超出檢查範圍時回原專案調整，而不是無聲地再母帶一次。較安靜的 Ambient 也可設定自己的目標。

來源音檔 SHA-256、來源 JSON SHA-256、原始完整資料、邊界調整樣本數及處理方式會保存在 `work/soundtrack-import.json` 和成品 `<slug>-soundtrack-source.json`。僅音樂專案實際提供 MIDI 時交付它；匯入音訊不會反推 MIDI。

重新合成外部配樂時仍傳同一組參數；不帶 `--audio` 的原流程仍會對 `work/score-mix.wav` 做雙階段母帶。兩條流程擇一，不把外部完成母帶再送入舊 premix 路徑。

## 留白與檢查

有意的靜音段在影片 `project.json` 的 `music.intentional_silence` 記錄，例如 `[[12, 14]]`。這只是 QC 的意圖標記，不會製造靜音；實際聲音仍由編曲決定。標記必須覆蓋整個低音量分析窗，其他意外靜音仍會失敗。自由時間配樂仍檢查音訊有效性、響度、真峰值、單聲道與片尾，但不套用有拍段落的拍間空洞診斷。

參考以下文件處理具體問題：

- [旋律型／House 編曲](edm-production.md)：和聲、主題發展與既有作曲範本。
- [音訊連續性](audio-continuity.md)：release、共同音、拍間空洞、刺耳聲部及 cue 檢查。
- [本機管線](local-pipeline.md)：uv 環境、圖像渲染、合成與交付。

實際試聽能判斷音色、情緒與音畫關係；訊號與符號檢查只排除部分製作錯誤。沒有試聽能力時交付可播放檔並如實列出已完成的客觀檢查。
