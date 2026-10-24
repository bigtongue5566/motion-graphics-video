# 本機製作管線

## 建立與依賴

使用 init_project.py 建立專案。它複製小型範本並產生 project.json，不覆寫已有檔案、不下載媒體、也不改使用者原本的影片。可以建立新專案或在現有專案中選擇新子資料夾。

```text
uv run --python 3.12 python <skill>/scripts/init_project.py --project <project-directory>
uv sync --project <project-directory>/work
```

initializer 會將 pyproject.toml 複製到 work/；使用 `uv run --project <project-directory>/work python <script-path>` 執行。下列相對路徑範例從影片專案根目錄執行。依賴為 NumPy、SciPy、Pillow、Skia、Mido、imageio-ffmpeg。FFmpeg 由 imageio_ffmpeg.get_ffmpeg_exe() 尋找，無需假設已安裝系統版本。requirements.txt 保留供既有環境相容使用。

受限環境若已有快取，可用 uv 的 offline 模式。快取目錄不能寫入時，指定專案的 work/uv-cache，避免改既有全域權限。

## 品牌素材與字型

先修改 project.json，加入官方 LOGO，使用 local path 相對於專案；可以使用透明 PNG 或官方 SVG。logo_on_dark 可指定品牌提供的反白版。SVG 若使用 renderer 不支援的 CSS，先產生保留原路徑與官方色的衍生檔。

Windows 字型會尋找 Microsoft JhengHei 與 Arial。也可在 config.fonts 設定自有中文／英文的字型檔路徑。缺字型時會報錯；修正後再渲染。

若 music.soundfont 設定了音色庫，music.fluidsynth 可指向執行檔；未指定執行檔時會嘗試 PATH。檢查 SoundFont 的 RIFF 宣告長度，避免載入未下載完成的檔案。使用自然鍵盤時保存音色庫來源與授權。

## 操作

```text
uv run --project work python work/render_video.py preview --project .
uv run --project work python work/render_video.py render --project .
```

preview 產生分鏡與封面。render 產生 work/picture.mp4，為完整動畫的影像軌。完成畫面後，按以下兩條配樂流程選一條。

## 配樂與合成

內建 Melodic House 起點：

```text
uv run --project work python work/compose_edm.py --project .
uv run --project work python work/finish_video.py --project .
```

compose 產生 work/score-mix.wav、配樂 MIDI 與音樂來源／音符檢查。finish 對這份 premix 做雙階段響度處理，輸出獨立 BGM、合成 MP4，最後直接解碼與檢查實際成品。這是內建範本的聲音方向，不是其他電子曲風的生成器。

其他方向或已有完成配樂：依 [電子配樂與畫面同步](electronic-soundtrack.md) 用 `electronic-music-production` 或本案工具完成同片長的音樂專案，再匯入母帶與來源：

```text
uv run --project work python work/finish_video.py --project . --audio ../music/outputs/score-master.wav --audio-metadata ../music/work/music-metadata.json
```

路徑替換成本案實際檔名。這條流程略過作曲及 loudnorm，保留母帶增益；只做格式轉換、最多 40ms 的邊界調整與 AAC 編碼。片長不符先停止，不能用 `-shortest` 掩蓋。配置 music.lufs 為本案採用的響度目標；工具仍驗證最終 AAC 的響度與峰值。來源原始 JSON 與音檔雜湊會附在成品來源檔，不將授權音樂標為原創。外部音訊路徑相對於執行命令的目前目錄。

只重做配樂時，可沿用 work/picture.mp4。新的音樂時間表需仍與原始章節及重要動作匹配。完成後用同一條 finish 流程重新合成與驗證；外部配樂仍需帶 --audio 與 --audio-metadata。

成品名稱、片長與音樂速度都讀 project.json；避免將初版作品名稱、新聞年份或 90 秒寫死在腳本。數據與文案從本案 config 載入；圖形的實際內容需要依本案設計。畫面範本使用 16:9 構圖；需要直式影片時重設構圖與位置，保留 LOGO 比例。

## 驗證與限制

新視覺方向可先執行原創無聲練習，沿用上述依賴及字型：

```text
uv run --python <venv-python> python <skill>/scripts/render_motion_study.py --output <empty-study-directory>
```

可加 `--preview-only` 只出關鍵影格、連續影格及任意時間重現檢查；`--samples 1|3|5` 控制僅作用在圖形層的動態取樣。使用 `--cn-font`／`--en-font` 指定字型。輸出目錄必須為空，以保存上一版。完整練習輸出十秒無聲 MP4、構圖總覽、快速動作連續影格及檢查結果，不下載素材。

此練習展示單一主體、弧線接力、遮罩、錯峰和收束，不是新的多風格 preset。依本案改寫構圖與動作；對外要求完整影片時仍須製作音樂及必要音效。

finish 檢查影片時長／幀率／尺寸、完整解碼的影格數、48kHz 雙聲道音訊、真峰值、響度、意外靜音、末端淡出與單聲道相容性，並取各章節的實際影格到 work/qc/。`music.intentional_silence` 可標記本案刻意留白；來源 metadata 的 `pulse: free` 會停用拍間空洞診斷。可在維持使用者要求的前提下調整合理檢查界限。

分鏡與這些訊號檢查不代表已觀看完整影片或聽過音樂。提供實際成品，按可用能力檢查並如實記錄。

建立來源套件時，只打包本案需要的腳本、設定、素材、來源及授權；不包含虛擬環境、快取、絕對個人路徑或不需分享的大型中間檔案。外部音色庫可保留來源與雜湊；若打包音色庫，附相應授權。
