# Architecture and implementation sequence

## Choice

Use Electron for the desktop window and a loopback-only Python worker for media ownership, analysis, persistence and render jobs. The UI is plain HTML/CSS/JavaScript: a small proof of concept does not need a component framework. NumPy supplies numeric audio analysis, Pillow supplies compositing, and FFmpeg supplies codecs and MP4 encoding. No cloud dependency exists in the runtime.

Electron has Node integration disabled, context isolation enabled and the renderer sandbox enabled. Navigation is restricted to the local app origin; new windows and permission requests are blocked. The local server binds 127.0.0.1, validates Host/Origin, and requires an unpredictable session token for mutations. File routes only serve managed media, exports and UI assets. Imports invoke FFmpeg with argument lists, not shell strings. SVG is not accepted.

Official references consulted during design:
- https://www.electronjs.org/docs/latest/tutorial/security/
- https://www.electronjs.org/docs/latest/tutorial/context-isolation
- https://ffmpeg.org/ffmpeg-filters.html
- https://ffmpeg.org/ffmpeg.html

## Time coordinates

Audio file time is the master time in seconds. For a constant tempo:

`beat(t) = (t - firstBeatOffsetSeconds) * BPM / 60`

For a layer cycle of L beats:

`phase(t) = fractionalPart(beat(t) / L)`

The implementation snaps only floating-point values within 1e-10 of an exact cycle boundary, preventing decimal-tempo rounding from displaying the previous cycle's last frame. Negative pre-roll wraps correctly.

A forward clip samples `floor(phase * trimmedFrameCount)`. Reverse flips phase, ping-pong uses `1 - abs(2*phase - 1)`, and freeze samples the first trimmed frame. Clips stretch to their layer's beat count. Imported presentation timing is normalized by FFmpeg to a constant 24 FPS cache before sampling.

Keyframes store local beat positions in that cycle; supported properties interpolate linearly. Values before the first/after the last key are held. Matching first and final keys closes a loop. Periodic float is `(1-cos(phase*2π))/2`, not an accumulation of frame deltas. RMS lift is sampled from the current audio time and added independently, and is disabled by zero intensity.

Preview takes the HTML audio element's `currentTime`; silent preview uses a monotonic clock. Only one preview request is in flight. This favors accurate state and bounded work over dropping a backlog of stale frames. Network/CPU latency can make visible preview lag sound; export has no such real-time dependency.

Export frame N evaluates the same renderer at `rangeStart + N / outputFPS`. FFmpeg receives raw RGB frames at that fixed rate. Audio is decoded from the same range start in the original source, padded with silence if necessary and encoded as AAC. Frame count is `ceil(duration * FPS)`, so duration is rounded up by less than one output frame. No real-time screen capture occurs. An atomic rename exposes only a completed MP4.

## Scene format v1

Scene JSON contains:

| Field | Meaning |
|---|---|
| version / id | Schema version and stable 32-hex scene identifier |
| name / tags / created / modified | Library metadata |
| bpm / offset / beatsPerBar / bars | Constant musical grid and shared export-loop length |
| width / height / fps / background | Output canvas and background |
| audio | SHA-256 reference to managed original audio, or null |
| layers | Ordered back-to-front layer list |

Each layer contains `id`, `asset`, `name`, normalized center `x/y`, relative contain-fit `scale`, clockwise `rotation`, `opacity`, `beats`, `mode`, source `trimStart/trimEnd` seconds, `bounce`, `react`, optional `hidden`, and `keys`. Keys contain `beat` and transform values.

Managed files:

```
assets/<sha256>/source.<extension>
assets/<sha256>/meta.json
assets/<sha256>/frames/000001.png  (visual cache)
assets/<sha256>/audio.wav         (audio preview)
scenes/<scene-id>.json
scenes/<scene-id>.jpg
exports/<job-id>.mp4
```

Asset references do not depend on the original filename or location. Two scenes can share the same asset directory. Portable backups include the scene and referenced asset directories. Restore validates paths and size, reimports originals, rebuilds caches, and assigns a new scene ID to avoid silently replacing an existing scene. Unknown schema versions fail explicitly.

## Why CPU rendering first

Using one actual renderer for preview and export removes differences in keyframe math, clip sampling, transformations and compositing during this timing proof. The tradeoff is throughput and UI latency. This is an architectural checkpoint, not the finished high-performance design.

A production GPU renderer should preserve this scene schema and deterministic time evaluator, move frames into a bounded texture cache, and render preview/export through the same GPU scene implementation. That migration needs numerical and visual parity fixtures before it replaces the CPU reference. Decoder seeking, alpha handling, color space and memory limits matter more than simply switching drawing libraries.

## Next milestones

1. **Native packaging:** bundle Python and licensed FFmpeg distributions; test Windows and Apple Silicon; build signed installers; add graceful export cancellation/shutdown.
2. **Playback and asset scale:** GPU canvas, bounded decode cache, responsive seek, import cancellation, disk quota/cleanup and large-library indexing. Preserve exact offline frame times.
3. **Editor:** drag handles, crop/masks, camera, timeline keyframe editing, easing, reusable collections and explicit scene-only presets independent from audio.
4. **Musical analysis:** multi-band flux/onsets, onset overlays, band-specific mappings, attack/release/smoothing, confidence and user correction; evaluate against real beats with known tempo annotations. Instrument-specific labels must remain approximate unless stems are provided.
5. **Loop craft:** crossfades, motion endpoint matching, long-clip proxy workflows and expanded trim UX.
6. **Character systems:** independently imported head/body layers first; consider mesh/bone deformation only after the core workflow is reliable.
7. **Optional host integration:** design a lightweight DAW transport bridge separately. A desktop scene editor is not automatically a VST.

Hard problems still open include broad real-world BPM reliability, seamless source content, low-latency audio/video preview, production GPU/CPU parity, robust native codec packaging, and articulated character animation from properly prepared layers.
