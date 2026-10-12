# Validation record · 2026-10-12

## Passed

`python -m unittest discover -s tests -v`: **12 tests passed**.

- Known-tempo synthetic click signal with an offset; silent input marked uncertain.
- Loop boundaries at 60, 87.3, 120 and 177 BPM, including a decimal-rounding regression.
- Ping-pong frame indexing and identical rendering at a complete loop boundary.
- Non-finite tempo values rejected.
- Asset deduplication and scene serialization/loading.
- Portable restore into a fresh store after deleting the original imported file.
- Archive traversal rejection.
- Transform keyframe interpolation against a rendered pixel mask.
- MP4 H.264 video / AAC audio, frame count and duration.
- Decoded MP4 frames compared to the deterministic reference renderer at eight timestamps (mean absolute channel error below 4/255).
- Decoded audio transients present at the expected half-second beat times.
- Nonzero export start selects the expected absolute scene frame.

`node tests/ui-smoke.cjs`: **passed in headless Chromium 153 on Linux**.

- Load original example through the restore endpoint, display both layers and render preview.
- Import audio and visual files through the actual file-picker controls.
- Edit BPM, half/double tempo, play audio and advance the playhead.
- Capture and close transform keyframes.
- Save and reload a named scene.
- Recover unsaved tags after reload.
- Queue a 360 × 640, 24 FPS MP4 export and download it.
- Decode and play the exported MP4 in a browser video element; dimensions and advancing playback time checked.
- Reject a state-changing request without its session token.
- No browser JavaScript errors during this workflow.

The editor screenshot and a decoded frame from the demo were inspected visually. Screenshots are internal QA artifacts, not included in the source bundle.

`python -m examples.make_demo`: generated the included original “Night shift” scene, portable backup and **1080 × 1920, 30 FPS, 4-second MP4**. The example's synthetic 120 BPM beat was estimated at 120.1 BPM with heuristic confidence 0.917; the scene itself uses the known exact 120 BPM. The example is a correctness fixture, not a claim about detection performance on all music.

## Not verified

- Native Windows or macOS execution, installation, signing and dependency discovery.
- Native Electron window lifecycle in a normal graphical desktop. The Electron dependency downloaded, but its headless Linux launch did not finish; the tested editor route is the local browser route using the same engine/UI files.
- Real-world tempo-detection accuracy across genres, long-session reliability or large-scene performance.
- All codec variants within MOV/WebM/MP4/WebP containers, GPU behavior, or every export dimension/frame-rate combination.

## Reproducing the UI test

Install Playwright as a development-only dependency and its Chromium runtime, start from this project directory and run:

```sh
npm install --no-save playwright
npx playwright install chromium
node tests/ui-smoke.cjs
```

The test starts and stops its own local engine and uses disposable scene data. `SYNTHOSIZE_PYTHON` can select Python; `SYNTHOSIZE_TEST_BROWSER` can select a locally installed Chromium executable. The normal app does not require Playwright.

## Hosted edition

Seven additional Flask tests cover unauthenticated access, login and CSRF validation, cross-origin and Host checks, saved-scene persistence across app restarts, portable restore and JPEG preview, completed MP4 export/download, logout and secure cookie attributes. Total: 19 core/hosted tests. Live Railway deployment verification is recorded separately once the source repository is connected.
