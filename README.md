# Synthosize Visual Studio · 0.1

A working local proof of concept for reusable, beat-synchronized visual worlds.

**This includes a runnable local editor and a password-protected Railway edition, not a signed Mac/Windows installer or an FL Studio plugin.** The local editor and export engine are tested on Linux. The Electron shell still needs native Mac and Windows validation.

## Railway edition

Deploy the included Dockerfile with a persistent `/data` volume. See `docs/RAILWAY.md` for required secrets and single-owner hosting behavior. Media is stored on Railway when using this edition.

## Start here

You need **Python 3.10+**, **FFmpeg and ffprobe on PATH**, and the two Python packages in `requirements.txt`. No API keys or paid services are used.

From this folder, in a terminal:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m engine.server --open
```

On Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m engine.server --open
```

The last command opens the editor in your browser, served only on `127.0.0.1`. Keep the terminal running. Ctrl+C stops it. If a browser doesn't open, use the printed local URL. Project data is saved in `~/SynthosizeStudio`. Use `--data /your/folder` to change this.

### Desktop shell (development)

With the same Python environment active, install Node.js and run:

```sh
npm install
npm start
```

The Electron process starts the same local engine and closes it when the window closes. If necessary, set `SYNTHOSIZE_PYTHON` to your Python executable's absolute path. Electron stores scenes in its user-data directory, separate from the browser launch's default data directory. Portable backups move scenes between them. Packaging Python and FFmpeg into standalone installers is not done yet.

## First loop

1. Click **Open example world** to load the original procedural “Night shift” scene and a synthetic 120 BPM test beat. The included artwork is only a test fixture; it does not establish a required Synthosize style.
2. Or click **Import beat**, then **Import** in the media panel. Supported audio: WAV, MP3, FLAC, M4A, OGG. Visuals: PNG, JPEG, WebP, GIF, MP4, MOV, WebM, subject to the installed FFmpeg decoder.
3. Check the BPM estimate by listening. Use **½ / 2×**, manual BPM, and **First beat** to align it. Scrub to a downbeat and click **Align to playhead**.
4. Select a layer. Choose its cycle length in beats and forward, reverse, ping-pong, or frozen playback. Trim values refer to source seconds, before tempo stretching. A trim-out of zero means the end. The full selected clip fits exactly into the cycle.
5. Add gentle rhythmic float or optional **Loudness → lift**. Both can remain zero. Add transform keyframes by moving the playhead, adjusting X/Y/rotation/opacity, and capturing the transform. Match the last keyframe to the first to close the cycle. If keyframes exist, they override that property's static value.
6. Save the scene. Import a different beat to reuse its visuals and motion. Scene assets are copied into a managed, content-addressed asset store; moving the original downloads does not break the scene.
7. Click **Export video**. Choose dimensions, 24/30/60 fps, start time and duration. Render and download the MP4. Export doesn't record your screen.
8. **Back up scene** produces a portable `.synth.zip` with original media and caches. **Restore backup** imports it under a new scene ID.

The editor previews the full audio track, or loops the selected number of bars when no audio is loaded. Individual layers always cycle at their own musical duration. “One visual loop” in export uses the scene's bar count; ensure each layer's cycle divides that length if you need a shared seamless boundary. Forward-loop source clips must themselves have matching endpoints. Ping-pong helps with mismatched ends but deliberately reverses motion. Audio is not automatically crossfaded at the export boundary.

## What works in this slice

- Local file imports, managed assets, duplicate detection, portable backups.
- BPM estimate with heuristic confidence, manual tempo, half/double time, first-beat offset.
- Audio waveform and beat grid, scrubbing, audio-led playback.
- Layer position, scale, rotation, opacity, visibility and ordering.
- Tempo-stretched clips, trim, reverse, ping-pong and freeze.
- Beat-based transform keyframes, periodic float, normalized loudness-driven lift.
- Named, tagged, searchable scenes with thumbnails and recovery of unsaved edits.
- Deterministic CPU rendering and background H.264/AAC MP4 export.
- Original example scene and a rendered 1080 × 1920, 30 FPS, four-second demo.

## Deliberate limits

- Animated imports are limited to **20 seconds**, decoded at **24 FPS** and up to **960 px** per side. Still images retain up to 1920 px. Higher-resolution export doesn't restore lost source detail. A 60 FPS export samples motion at 60 FPS, but the clip cache remains 24 FPS; there is no optical-flow interpolation.
- At most 12 layers; audio up to 15 minutes; upload size 300 MB. Decoded PNG caches can be much larger than the original media. Imported audio is downmixed for analysis/preview; export uses the original audio.
- Draft preview is CPU-rendered, at a target up to 24 FPS with one request in flight. Complex scenes may preview slowly. It is not yet a GPU editor, and low-latency preview/audio sync is not guaranteed under load. Offline export uses exact frame times.
- This first renderer has no masks, crop tool, color grading, independent camera, drag handles, crossfade loop mode, advanced easing, frequency-band mappings, attack/release controls, puppet rigging, particles or 3D.
- Loudness lift uses a normalized 10 ms RMS envelope. It does not claim to isolate kick, snare, 808 or melody. BPM confidence is a heuristic, not a calibrated probability. Sparse, syncopated and variable-tempo music needs manual correction.
- SVG is intentionally rejected until a safe rasterization path is implemented.
- No VST/AU, live FL Studio transport link, AI generation, cloud sync or account system.
- Source install only: no bundled dependency installer, app signing, auto-update or native platform certification.

## Development

```sh
python -m pip install -r requirements-hosted.txt
python -m unittest discover -s tests -v
python -m examples.make_demo
```

`docs/ARCHITECTURE.md` explains time coordinates, the project format, export and next milestones. `docs/VALIDATION.md` records the checks actually performed in this environment.
