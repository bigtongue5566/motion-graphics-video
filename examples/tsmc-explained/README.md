# 台積電｜從設計到矽晶

90-second, 1080p/30fps motion film with a newly composed **Dub Techno** soundtrack:
**124 BPM · D minor**. Revision: `2026-10-10-multi-style`.

Restrained four-on-the-floor pulse; dark chord stabs with three progressively filtered dotted-eighth echoes; slowly moving cutoff; sparse rim and hats; no foreground melody.

[Watch the film](https://bigtongue5566.github.io/?demo=tsmc-explained) ·
[Play the soundtrack](https://bigtongue5566.github.io/?demo=tsmc-explained-music) ·
[Download sources](https://bigtongue5566.github.io/motion-graphics-video/media/tsmc-explained-source.zip)

## Editable production

`compose_showcase.py` implements four separate arrangements with different
drum patterns, sound synthesis, bass roles and modulation. These are bespoke showcase
implementations, separate from the Skill starter's three CLI presets. `compose_edm.py`
supplies the reusable note/stem/MIDI base; it is not this revision's composition entrypoint.

`project.json` stores explicit seventh/ninth chord voicings as absolute MIDI pitches.
Edit those pitches and bass roots together when changing key. `note-events.json`,
`music-metadata.json` and `automation.json` preserve the actual rendered note and modulation
data, including sounding echoes and kick-triggered ducking. MIDI contains the pitched
parts and percussion; GM playback does not reproduce these custom synthesizers or effects.

Film sections sit on the new musical grid. Geometry follows the mastered audio's RMS
and spectrum, with kick-driven pulses taken from the composition's actual note events.

## Reproduce locally on Windows

From this example directory, using Python 3.12 and uv:

```powershell
uv venv work/.venv --python 3.12
uv pip install --python work/.venv/Scripts/python.exe -r requirements.txt
work/.venv/Scripts/python.exe -X utf8 download_fonts.py
Copy-Item production/*.py work/
work/.venv/Scripts/python.exe -X utf8 work/compose_showcase.py --project .
work/.venv/Scripts/python.exe -X utf8 work/finish_music.py --project .
work/.venv/Scripts/python.exe -X utf8 work/render_tsmc.py preview --project .
work/.venv/Scripts/python.exe -X utf8 work/render_tsmc.py render --project .
work/.venv/Scripts/python.exe -X utf8 work/finish_video.py --project .
```

On other platforms use the corresponding venv/bin/python and copy command.
Font downloads use pinned source commits and SHA-256 checks; binaries are not bundled.
These commands create local artifacts and do not publish to any service.

Outputs: H.264/AAC MP4, exact-length 48kHz/24-bit stereo WAV master, AAC soundtrack,
MIDI, poster, storyboards and direct audio/video QC. The packaged reports describe the
published encoding: -16.0 LUFS, -1.9 dBTP,
2700 fully decoded video frames, zero decode errors.
The explicit chord audit permits the intended sevenths/ninths and rejects unintended
notes across chord boundaries. Objective checks do not certify subjective listening quality;
no listening review is claimed.

See [actual materials and licenses](RIGHTS.md), [sources](sources.json),
[audio QC](audio-qc.json), [video QC](video-qc.json) and [music notes](MUSIC.md).

This is an independent, unofficial company introduction, without company commission or endorsement. Company facts, data years and source IDs are retained in [SOURCES.md](SOURCES.md) and [claims.json](claims.json). Concept drawings do not depict actual chip dimensions or equipment.
