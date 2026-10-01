# 本機製作管線

## 建立與依賴

使用 init_project.py 建立專案。它複製小型範本並產生 project.json，不覆寫已有檔案、不下載媒體、也不改使用者原本的影片。可以建立新專案或在現有專案中選擇新子資料夾。

```text
python <skill>/scripts/init_project.py --project <project-directory>
uv venv <project-directory>/work/.venv --python 3.12
uv pip install --python <project-directory>/work/.venv/Scripts/python.exe -r <project-directory>/work/requirements.txt
```

以專案虛擬環境的 Python 執行下列腳本。其他平台使用對應的 venv/bin/python。依賴為 NumPy、SciPy、Pillow、Skia、Mido、imageio-ffmpeg。FFmpeg 由 imageio_ffmpeg.get_ffmpeg_exe() 尋找，無需假設已安裝系統版本。

受限環境若已有快取，可用 uv 的 offline 模式。快取目錄不能寫入時，指定專案的 work/uv-cache，避免改既有全域權限。

## 品牌素材與字型

先修改 project.json，加入官方 LOGO，使用 local path 相對於專案；可以使用透明 PNG 或官方 SVG。logo_on_dark 可指定品牌提供的反白版。SVG 若使用 renderer 不支援的 CSS，先產生保留原路徑與官方色的衍生檔。

Windows 字型會尋找 Microsoft JhengHei 與 Arial。也可在 config.fonts 設定自有中文／英文的字型檔路徑。缺字型時會報錯；修正後再渲染。

若 music.soundfont 設定了音色庫，music.fluidsynth 可指向執行檔；未指定執行檔時會嘗試 PATH。檢查 SoundFont 的 RIFF 宣告長度，避免載入未下載完成的檔案。使用自然鍵盤時保存音色庫來源與授權。

## 操作

```text
python work/render_video.py preview --project .
python work/compose_edm.py --project .
python work/render_video.py render --project .
python work/finish_video.py --project .
```

preview 產生分鏡與封面。render 產生 work/picture.mp4，為完整動畫的影像軌。compose 產生 work/score-mix.wav、配樂 MIDI 與音樂來源／音符檢查。finish 對配樂做雙階段響度處理、輸出獨立 BGM、合成 MP4，最後直接解碼與檢查實際成品。

只重做配樂時，可沿用 work/picture.mp4。新的音樂時間表需仍與原始章節匹配。完成後用 finish 重新合成與驗證。

成品名稱、片長與音樂速度都讀 project.json；避免將初版作品名稱、新聞年份或 90 秒寫死在腳本。數據與文案從本案 config 載入；圖形的實際內容需要依本案設計。畫面範本使用 16:9 構圖；需要直式影片時重設構圖與位置，保留 LOGO 比例。

## 驗證與限制

finish 檢查影片時長／幀率／尺寸、完整解碼的影格數、48kHz 雙聲道音訊、真峰值、響度、意外靜音、末端淡出與單聲道相容性，並取各章節的實際影格到 work/qc/。可在維持使用者要求的前提下調整合理檢查界限。

分鏡與這些訊號檢查不代表已觀看完整影片或聽過音樂。提供實際成品，按可用能力檢查並如實記錄。

建立來源套件時，只打包本案需要的腳本、設定、素材、來源及授權；不包含虛擬環境、快取、絕對個人路徑或不需分享的大型中間檔案。外部音色庫可保留來源與雜湊；若打包音色庫，附相應授權。
