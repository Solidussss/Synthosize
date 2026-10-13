# Synthosize FL Studio VST3 — first integration milestone

This is an **early source-code scaffold, not a finished plugin binary**.
It reads BPM, PPQ song position, and play/stop state through the official
VST3 host interface and leaves the incoming audio unchanged. A localhost-only tempo bridge now sends host timing to the local Synthosize editor. The editor has a manual **Use FL BPM** button. Automatic timeline following, preview synchronization, and in-plugin video rendering are not implemented yet.

## Build (developer machine)

Requires CMake 3.22+, Git, a C++17 compiler, and network access to fetch
JUCE. From the repository root:

```sh
cmake -S plugin -B plugin/build -DCMAKE_BUILD_TYPE=Release
cmake --build plugin/build --config Release
```

Find the built VST3 package under `plugin/build/SynthosizeFL_artefacts/`
(platform/config-specific). Install it into the appropriate VST3 location
for your OS, then rescan plugins in FL Studio. On macOS VST3 plugins
typically live under `~/Library/Audio/Plug-Ins/VST3/`. On Windows
the standard system location is `C:\\Program Files\\Common Files\\VST3\\`.

## Current functionality
- Host BPM, musical PPQ position, and play/stop indication.
- Stereo audio passthrough (no effects or synthesis).
- Basic plugin GUI.
- Loopback UDP transport metadata to the local editor on port 48383; no media/audio transmission.
- Manual import of the FL Studio BPM into the local scene editor.
- No scene editing or video export in-plugin.

## Next milestone

Complete and validate the local bridge on real FL Studio sessions: test Windows and macOS VST3 compilation, add editor connection status, open-editor action, and opt-in live transport follow. Keep network I/O off the realtime audio thread. Never imply sample-accurate visual synchronization before measuring it. Keep the Railway hosted editor separate.
Do not claim sample-accurate video synchronization until measured.

Do not upload unlicensed clips for public distribution; the tool edits
user-supplied media without granting rights to that media.
