# Motion Graphics Video

A Codex skill for producing branded motion-graphics films with researched facts,
official logos and colors, synchronized animation, and original or licensed electronic soundtracks.

動態圖形影片製作 Skill：整合品牌研究、分鏡、動畫、多風格電子配樂、影音同步與成品檢查。
Skill instructions and production references are written in Traditional Chinese.

## Sourced company explainer — TSMC

[![台積電｜從設計到矽晶](https://bigtongue5566.github.io/assets/tsmc-explained.jpg)](https://bigtongue5566.github.io/?demo=tsmc-explained)

**[Watch the 90-second film with sound →](https://bigtongue5566.github.io/?demo=tsmc-explained)** ·
[逐段資料來源](https://bigtongue5566.github.io/?demo=tsmc-explained#references) ·
[Original soundtrack](https://bigtongue5566.github.io/?demo=tsmc-explained-music) ·
[Reproducible source](examples/tsmc-explained)

An independent, unofficial introduction to TSMC, with original conceptual wafer,
transistor and packaging animation and a new 124 BPM D minor Minimal Piano House score.
Reported 2025 facts and N2 production timing are linked to official primary sources
in the film, the player page, [SOURCES.md](examples/tsmc-explained/SOURCES.md),
and the machine-readable [claim ledger](examples/tsmc-explained/claims.json).

No company logo, corporate photo, official chart, website screenshot, company
footage or third-party recording is included. The company name identifies the
subject in ordinary type. This work is not sponsored or endorsed by TSMC.
Attribution does not grant rights or guarantee against legal claims; see the
[actual materials and rights record](examples/tsmc-explained/RIGHTS.md).

## Original demo

[![Form & Frequency — original motion study](https://bigtongue5566.github.io/assets/form-and-frequency.jpg)](https://bigtongue5566.github.io/?demo=form-and-frequency)

**[Watch the 90-second film with sound →](https://bigtongue5566.github.io/?demo=form-and-frequency)** ·
[Explore this Skill on Skill Showcase](https://bigtongue5566.github.io/?skill=motion-graphics-video)

An original 1080p motion study with procedural geometry and a synchronized
Future Bass soundtrack. The shared [production example](https://github.com/bigtongue5566/electronic-music-production/tree/main/examples/form-and-frequency)
includes its render source, MIDI, media checks, and [sources and licenses](https://github.com/bigtongue5566/electronic-music-production/blob/main/examples/form-and-frequency/RIGHTS.md).


## More original Demos

| Work | Music | Film | Standalone soundtrack | Reproducible source |
| --- | --- | --- | --- | --- |
| Digital Pulse / 數位脈動 | 60 sec · 172 BPM · Drum & Bass | [Watch](https://bigtongue5566.github.io/?demo=digital-pulse) | [Listen](https://bigtongue5566.github.io/?demo=digital-pulse-music) | [Project](https://github.com/bigtongue5566/electronic-music-production/tree/main/examples/digital-pulse) |
| Neon Drift / 霓虹漫遊 | 60 sec · 132 BPM · UK Garage | [Watch](https://bigtongue5566.github.io/?demo=neon-drift) | [Listen](https://bigtongue5566.github.io/?demo=neon-drift-music) | [Project](https://github.com/bigtongue5566/electronic-music-production/tree/main/examples/neon-drift) |

Each work has a new musical arrangement and original procedural visuals,
documented sources, MIDI, editable code, and checks of the finished media.

## Refreshed multi-style showcase

The four current films and soundtracks were recomposed and re-rendered on 2026-10-10:
Future Bass (148 BPM), Drum & Bass (172 BPM), UK Garage (132 BPM), and Minimal Piano House (124 BPM).
Their source packages retain explicit chord voicings, notes, actual synthesis/automation,
MIDI and finished-media QC. These custom example implementations are separate from the
companion music skill's selectable starter arrangements. The films follow the new audio and actual kick events.

## Electronic soundtracks beyond EDM

Choose music from the film's narrative and sound references: dance styles, Ambient,
Downtempo, experimental or hybrid scores can use different rhythms, textures and
forms. The companion [electronic-music-production](https://github.com/bigtongue5566/electronic-music-production)
skill handles music development. Import its finished master and provenance with
`finish_video.py --audio ... --audio-metadata ...`; the video pipeline preserves gain
and copies the picture stream without running a second loudness master.

For free-time scores, synchronize by seconds, texture and tension changes rather
than a fabricated beat grid. Intentional rests can be declared for audio QC.
The included `compose_edm.py` remains a standalone Melodic House starter for existing
projects; other styles require their own arrangement, not just a new preset label.
See [electronic soundtrack integration](references/electronic-soundtrack.md).

## Starter preview

The [art direction and motion guide](references/art-direction-and-motion.md) adds
representative-shot development, object-driven transitions, purposeful timing,
visual review and explicit ending design. [Style recipes](references/style-recipes.md)
help choose a visual language and tools without treating every technology film as a HUD.

An original, silent [10-second motion study](scripts/render_motion_study.py) exercises
a focal object, path hand-off, stagger, masked transitions and a settled end frame.
Using the starter dependencies, run it with:

```text
uv run --python <venv-python> python scripts/render_motion_study.py --output <empty-study-directory>
```

It exports an MP4, key frames, a motion filmstrip and deterministic-seek/media checks.
This is a visual study, not a scored client film or a collection of style presets.
The source is original; the guidance cites the independently published
[mg-styles-15](https://github.com/Vincentwei1021/mg-styles-15) as a study reference.

![Starter storyboard](docs/starter-storyboard.jpg)

The storyboard shows the starter's vector scenes. Its example text illustrates the
workflow; replace it with researched content for each actual brand.

## What it includes

- A workflow for checking company facts, news, official logos, palettes, and source provenance.
- Animated vector scenes: brand opening, connected networks, modular assembly, flowing paths,
  metrics, and a brand closing.
- A configurable melodic-house score with chord-following melodies, bass, drums,
  builds, breaks, chapter accents, and kick-triggered volume ducking.
- An import path for finished electronic scores, with source hashes and original metadata,
  no second loudness master, and free-time/intentional-rest handling in QC.
- Independent AAC background music and a final H.264/AAC MP4; the internal composer
  also produces editable MIDI and a mastered WAV.
- Direct checks of the encoded movie: duration, frame count, resolution, frame rate,
  audio format, loudness, true peak, mono compatibility, and fading.

The starter defaults to 90 seconds, 1080p, 30 fps, and 120 BPM. These are adjustable
starting values. Adapt the layout, narration, visuals, and music to the actual brief.

## Install as a Codex skill

Clone this repository into your Codex skills directory. For the standard Windows
location used by this project:

```powershell
git clone https://github.com/bigtongue5566/motion-graphics-video.git "$env:USERPROFILE\.codex\skills\motion-graphics-video"
```

If you use a custom `CODEX_HOME`, place the repository in its `skills/motion-graphics-video`
directory. Use an empty destination to preserve an existing installation.

Invoke it with a prompt such as:

```text
用 $motion-graphics-video 製作一支 90 秒的公司介紹影片，
採用官方 LOGO 與品牌配色，搭配適合敘事的電子配樂，並查證公司資訊。
```

## Run the starter directly

Python 3.12 and `uv` are used in the tested Windows setup. The dependencies include
NumPy, SciPy, Pillow, Skia, Mido, and imageio-ffmpeg. FFmpeg is supplied by
imageio-ffmpeg; a separate system installation is unnecessary.

From the repository root:

```powershell
uv run --python 3.12 python -X utf8 scripts/init_project.py --project ../my-brand-film
uv sync --project ../my-brand-film/work
```

Edit `../my-brand-film/project.json` to set the brand, official logo paths, colors,
copy, scenes, timing, and music. Add the relevant source records to
`../my-brand-film/work/sources.json`.

```powershell
uv run --project ../my-brand-film/work python -X utf8 ../my-brand-film/work/render_video.py preview --project ../my-brand-film
uv run --project ../my-brand-film/work python -X utf8 ../my-brand-film/work/render_video.py render --project ../my-brand-film
```

Choose one audio route. For the included House arrangement:

```powershell
uv run --project ../my-brand-film/work python -X utf8 ../my-brand-film/work/compose_edm.py --project ../my-brand-film
uv run --project ../my-brand-film/work python -X utf8 ../my-brand-film/work/finish_video.py --project ../my-brand-film
```

For a finished score from a separate music project, replace the paths with its actual outputs:

```powershell
uv run --project ../my-brand-film/work python -X utf8 ../my-brand-film/work/finish_video.py --project ../my-brand-film --audio ../music/outputs/score-master.wav --audio-metadata ../music/work/music-metadata.json
```

The imported track must match the requested film duration; only up to 40 ms of
codec/resampling boundary trim or padding is allowed and recorded. Set `music.lufs`
to the intended delivery target. Import does not normalize gain, and the encoded
AAC must still pass final loudness, peak, mono and ending checks. Supply provenance
with `original_composition` (boolean) or a `composition` description, including
the actual source/license details. See the integration guide for free-time metadata.

Supply suitable fonts in `project.json`. Windows defaults use Microsoft JhengHei and Arial.
The included visual layout is 16:9; redesign the composition for a portrait film.

The initializer also accepts `--duration`, `--bpm`, `--size`, `--fps`, and `--name`.
It refuses to overwrite existing project files.

## Outputs and configuration

Finished files are written to the generated project's `outputs/` directory:

| File | Purpose |
| --- | --- |
| `<slug>.mp4` | Full motion-graphics film with music and chapter metadata |
| `<slug>-bgm.m4a` | Independent soundtrack |
| `<slug>-music.mid` | Editable note and instrument tracks from the internal composer |
| `<slug>-soundtrack-source.json` | Imported audio provenance, hashes and conversion details, when using --audio |
| `<slug>-storyboard.jpg` | Scene composition overview |
| `<slug>-poster.jpg` | Film poster |
| `<slug>-qc.json` | Measurements from the encoded final film |
| `<slug>-production.md` | Production notes and supplied source references |

`work/` contains the silent picture track, floating-point mix, 24-bit audio master,
logs, and actual encoded frame samples. Keep `work/picture.mp4` when revising only
the soundtrack.

- [Skill instructions](SKILL.md)
- [Project configuration](references/project-schema.md)
- [Visual research and design](references/visual-production.md)
- [Electronic soundtracks and synchronization](references/electronic-soundtrack.md)
- [Melodic House composition and mixing](references/edm-production.md)
- [Local production pipeline](references/local-pipeline.md)

## Instrument sources and validation

The default keyboard and electronic instruments are synthesized by the included
code. For a sampled piano, configure a local SoundFont and a compatible FluidSynth
executable in `music.soundfont` and `music.fluidsynth`. Record the source and license.
External sound libraries are separate downloads and are not bundled here.

The workflow has been exercised on Windows with an 8-second, 15 fps synthesized
version and a 7.3-second, 30 fps version at 124 BPM in D major with a sampled piano.
Both completed the animation, score, mastering, muxing, and encoded-media checks.

Signal measurements and chord-note checks help find production errors. Listening
and visual review remain necessary to assess musical and design quality.

The [audio continuity guide](references/audio-continuity.md) covers MIDI gates versus
release tails, shared-note ties, legato articulation and 10ms gap diagnostics.
The standalone video starter now includes the repaired renderer and helpers.
Pad ties and room are opt-in. The built-in House composer defaults to consonant triads
with cross-part interval checks; intentional tension follows the brief. Other styles
and free-time scores use appropriate harmony and texture rules. The guide also covers harsh timbres,
primary/echo beat placement and verifying picture cues in the final MP4.

The soundtrack regression suite exercises real AAC/MP4 muxing, unchanged picture
packets and master gain, provenance retention, duration rejection and declared rests:

```text
uv run --project <generated-film>/work python -m unittest discover -s tests -v
```

## License

The code, original vector primitives, synthesis code, and skill documentation in
this repository are available under the [MIT License](LICENSE).
External dependencies, fonts, SoundFonts, company logos, and trademarks retain
their respective licenses and ownership. No company logos or sampled instrument
banks are included in this repository.
