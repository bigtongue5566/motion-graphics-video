# 台積電｜從設計到矽晶

A 90-second independent, unofficial TSMC introduction, with original conceptual
animation and a newly composed 120 BPM E minor electronic soundtrack.

[觀看影片與逐段來源](https://bigtongue5566.github.io/?demo=tsmc-explained) ·
[獨立配樂](https://bigtongue5566.github.io/?demo=tsmc-explained-music) ·
[資料來源](SOURCES.md) · [素材與授權](RIGHTS.md)

The film identifies official sources on screen and separates 2025 reported data
from conceptual graphics. It does not reproduce company logos, official graphics,
photographs, website screenshots, corporate footage or third-party recordings.
It is not sponsored or endorsed by TSMC. Attribution is not a clearance guarantee.

## Reproduce on Windows

From this example directory, using Python 3.12 and uv:

```powershell
uv venv work/.venv --python 3.12
uv pip install --python work/.venv/Scripts/python.exe -r requirements.txt
work/.venv/Scripts/python.exe -X utf8 download_fonts.py
Copy-Item production/*.py work/
work/.venv/Scripts/python.exe -X utf8 work/compose_tsmc.py --project .
work/.venv/Scripts/python.exe -X utf8 work/finish_music.py --project .
work/.venv/Scripts/python.exe -X utf8 work/render_tsmc.py preview --project .
work/.venv/Scripts/python.exe -X utf8 work/render_tsmc.py render --project .
work/.venv/Scripts/python.exe -X utf8 work/finish_tsmc.py --project .
```

Use the equivalent Python path and copy command on other platforms. The font
downloader verifies pinned upstream versions. Rendering is local; the reproduction
scripts do not publish files or silently download company media.

Outputs include 1080p/30fps H.264/AAC MP4, 48kHz/24-bit WAV master, AAC, MIDI,
poster, storyboard, and direct audio/video QC. The finished recording uses original
synthesis; suggested MIDI program numbers do not duplicate its exact timbres.
Objective checks do not establish subjective listening quality.

The source extends the author's MIT production utilities. `original_renderer.py`
provides font loading, audio analysis, transitions and encoding; `render_tsmc.py`
implements this film's independent diagrams, typography and source captions.
Original parts use MIT; third-party fonts use their retained OFL notices.
