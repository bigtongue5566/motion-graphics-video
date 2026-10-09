# 台積電｜從設計到矽晶

90 seconds · 1080p/30fps · **124 BPM · D minor · Minimal Piano House**.
Revision: `2026-10-10-soft-piano-sync`.

Original concept animation and composition. Soft GeneralUser GS acoustic piano
plays low-register Dm/Gm triads with clear bar attacks, over sparse original
electronic drums and sub. Dense detuned high stabs and dotted echoes are removed.
The packaging motion reads the shared cue map and settles on the 60.0s piano/kick attack.
The user confirmed the 0:54–1:14 review: the tone is more comfortable and the beat clearer.
Full-film QC is technical; that listening feedback covers the excerpt.

[Watch](https://bigtongue5566.github.io/?demo=tsmc-explained) ·
[Soundtrack](https://bigtongue5566.github.io/?demo=tsmc-explained-music)

## Reproduce locally

Use Python 3.12. Install a compatible [FluidSynth](https://github.com/FluidSynth/fluidsynth/releases)
and add its executable to PATH, or set music.fluidsynth to your local executable.
FluidSynth 2.6.1 was used for this render. Fonts and the SoundFont are downloaded
separately from pinned official commits with SHA-256 verification; binaries are not bundled.

```powershell
uv venv work/.venv --python 3.12
uv pip install --python work/.venv/Scripts/python.exe -r requirements.txt
work/.venv/Scripts/python.exe -X utf8 download_fonts.py
work/.venv/Scripts/python.exe -X utf8 download_soundfont.py
Copy-Item production/*.py work/
work/.venv/Scripts/python.exe -X utf8 work/compose_showcase.py --project .
work/.venv/Scripts/python.exe -X utf8 work/finish_music.py --project .
work/.venv/Scripts/python.exe -X utf8 work/render_tsmc.py preview --project .
work/.venv/Scripts/python.exe -X utf8 work/render_tsmc.py render --project .
work/.venv/Scripts/python.exe -X utf8 work/finish_video.py --project .
```

On other platforms use the corresponding venv/bin/python and copy command.
The composer preserves original drum/bass spacing, checks triad membership and
simultaneous intervals, and exports MIDI, actual note events and mix automation.
Sampled release and effects still require audio review. GM playback alone does
not reproduce the custom percussion, sub or processing.

Outputs: exact-length 48kHz/24-bit WAV, AAC, MIDI and H.264/AAC MP4.
The film has 2700 decoded frames with zero decode errors; audio targets −16 LUFS and −2 dBTP.
See [audio QC](audio-qc.json), [video QC](video-qc.json), [music](MUSIC.md),
[tone/cue review](tone-review-qc.json), [materials/rights](RIGHTS.md),
[source ledger](sources.json) and [company references](SOURCES.md).

Independent, unofficial company introduction, without company commission or endorsement.
Concept drawings are not actual engineering diagrams. Company facts and source IDs
are retained in [claims.json](claims.json).
