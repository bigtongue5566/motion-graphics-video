# project.json

init_project.py 會產生完整可讀的範例。主要欄位如下。

| 欄位 | 用途 |
| --- | --- |
| name / slug | 顯示名稱與成品檔名；slug 使用英數、底線或連字號 |
| duration / fps / width / height | 片長、幀率、畫面尺寸；duration × fps 必須為整數影格 |
| brand.name / tagline | 品牌文案，不會自動查證 |
| brand.primary / secondary / accent / ink | 十六進位品牌色與文字色 |
| brand.logo / logo_on_dark | 官方 LOGO 本機路徑，可為 SVG 或 PNG；未提供時使用品牌名稱文字，不能當作已滿足指定 LOGO 的要求 |
| fonts.cn / en | 可選字型檔路徑；未指定時使用支援的系統字型 |
| music.bpm / transpose | BPM 與相對 G 大調的半音移調量；例如 -5 為 D 大調 |
| music.soundfont / fluidsynth | 可選取樣樂器與 FluidSynth 執行檔的本機路徑 |
| music.soundfont_source / license | 對應音色庫的來源與授權路徑 |
| music.lufs / true_peak | 可調母帶目標；預設 -16 LUFS、-2 dBTP |
| scenes | 時間連續的場景陣列，涵蓋 0 至 duration |

每個場景包含 start、end、kind、scheme、chapter、headline、body、footnote、music_role。可選 metric、suffix、label、subline 與 visual_label。

kind：intro、network、modules、flow、metric、outro。
scheme：light 或 dark。
music_role：intro、groove、build、drop、break、outro。

每個場景應有足夠的閱讀時間。headline 可以換行；長句改成短行，或調整模板的文字大小。metric 必須來自本案資料；省略時顯示图形。百分比環圖還需 metric_value（0–100），不把 arbitrary 數字當成比例。

music_role 直接與場景的時間區間共用，作為聲部密度與轉場的指引。和弦依 music.bpm 的小節時間變化；任意非整拍場景不會擅自改時間。音符與收尾會裁切到精确片長。

範例內容只描述製作能力，沒有套用任何公司的年份、財務數據、優勢或商標。實際影片製作時換成本案來源可支持的敘事。
