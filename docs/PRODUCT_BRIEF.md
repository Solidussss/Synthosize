# SYNTHOSIZE — Visual Studio
## Build a Reusable, Beat-Synchronized Animation Studio

I want to create a desktop application called **Synthosize Visual Studio**.

This is not a traditional music visualizer.

I am a music producer who makes trap, rage, R&B, alternative R&B, melodic, atmospheric, and experimental beats using FL Studio.

My goal is to create visually interesting, loopable animated scenes that play alongside my beats in TikTok, Instagram Reels, and YouTube Shorts.

I want to build a large, permanent library of custom scenes that I can reuse across hundreds of beats.

### The creative vision

I love unusual, memorable side characters from animated movies and television.

Examples of the kinds of characters I enjoy include:

- Goob from Meet the Robinsons
- Wybie from Coraline
- Grim from The Grim Adventures of Billy & Mandy
- Characters from Teen Titans Go!

These are examples of my personal taste, not a requirement to generate or reproduce copyrighted characters.

Sometimes I might make an upbeat, playful beat and want a funny animated character dancing.

Other times I might make a dark, emotional beat and want a lonely character sitting in a strange environment.

Another time I might want a cinematic scene, a nostalgic cartoon, an anime-inspired sequence, or something completely abstract.

**I do not want one consistent visual aesthetic forced onto every beat.**

The application should support many different characters, art styles, scenes, and moods.

I choose the visual content. The software helps animate, synchronize, edit, organize, and reuse it.

Users are responsible for having appropriate rights to media they import or publish.

---

# 1. Core Product Concept

Build a visual editing application with five primary functions:

1. Import visual assets.
2. Create animated scenes and seamless loops.
3. Synchronize animations with music.
4. Save scenes as reusable presets.
5. Export finished vertical videos.

The application should feel like a lightweight creative studio, not a complicated professional video editor.

It should be designed specifically for music producers.

### Ideal workflow

1. Open Synthosize Visual Studio.
2. Import a beat or audio file.
3. Detect its BPM or enter the BPM manually.
4. Browse the saved visual library.
5. Choose an existing scene or create a new one.
6. Import characters, images, GIFs, or videos.
7. Animate and customize the scene.
8. Synchronize animations to the beat.
9. Preview the result.
10. Export the finished video.
11. Save the scene for reuse with another beat.

The same scene should work with different songs and tempos without having to rebuild it.

---

# 2. Desktop Application

Target Windows and macOS.

Evaluate Electron as the preferred desktop framework, but select the architecture based on rendering performance, maintainability, audio synchronization, and video export requirements.

Keep the editor responsive even when rendering complex animation.

Prefer local processing for imported media and audio analysis.

Do not introduce recurring AI-generation costs into the core workflow.

The first release does not need generative AI.

---

# 3. Visual Asset Import

Support importing:

- PNG
- JPEG
- WebP
- Transparent images
- GIF
- MP4
- MOV
- WebM
- SVG, with safe handling
- WAV
- MP3
- FLAC, where supported

Users should be able to import an image, existing animated clip, or collection of visual layers.

### Editing controls

Provide controls for:

- Position
- Scale
- Rotation
- Opacity
- Crop
- Masks
- Layer order
- Playback speed
- Colour adjustments
- Basic effects
- Camera movement
- Keyframe animation

Allow transparent characters to be placed over separate backgrounds.

Do not require users to generate new characters inside the application.

---

# 4. Character Animation

This is one of the most important features.

I want to take static or animated characters and create interesting loops.

Support multiple animation methods.

### Imported animation

Allow users to import an existing clip or GIF and:

- Trim it
- Loop it
- Reverse it
- Adjust playback speed
- Freeze individual frames
- Synchronize actions with musical timing

### Static image animation

Allow users to animate a still image with:

- Position and rotation
- Scale and camera movement
- Subtle bouncing
- Floating
- Swaying
- Head movement where suitable layers are available
- Parallax
- Camera push-ins and pull-outs
- Keyframe animation

Do not pretend that a single flattened image can automatically provide true character articulation.

If advanced puppet animation is implemented, use an appropriate layer, mesh, bone, or deformation system.

### Seamless looping

Provide techniques such as:

- Matched start/end transforms
- Ping-pong loops
- Crossfade loops
- Repeating keyframes
- Cycle-based motion
- Loopable camera paths

Allow loops lasting 1, 2, 4, 8, or 16 measures, as well as custom durations.

---

# 5. BPM and Music Synchronization

This is the core technology.

Every visual scene should be able to synchronize with the imported beat.

### Audio analysis

Implement:

- BPM detection
- Manual BPM correction
- Beat-grid alignment
- Adjustable first-beat offset
- Half-time and double-time interpretation
- Onset detection
- Low-frequency energy analysis
- Transient detection
- RMS or loudness envelope analysis

Where practical, distinguish kick-like, snare-like, and high-frequency transient events.

Do not promise perfect instrument separation from a mixed beat.

Use confidence indicators and manual correction when detection is uncertain.

### Musical timing system

All animations should use musical timing.

Support:

- Individual beats
- Half beats
- Quarter beats
- Measures
- Every 2 measures
- Every 4 measures
- Every 8 measures
- Custom rhythmic subdivisions

For example:

A character might nod every two beats.

A camera might complete a movement over four measures.

A background light might change on every snare.

A scene transition might occur every eight measures.

### Critical requirement

Do not simply increase animation speed based on volume.

Build a genuine tempo-aware animation system.

Visual timing should remain synchronized to the beat grid.

Support musical easing and controlled rhythmic variations.

---

# 6. Audio-Reactive Animation

Create a flexible mapping system.

Users should be able to assign audio signals to visual properties.

Examples:

- Kick energy → character bounce
- Snare transient → quick rotation
- 808 energy → camera movement
- Hi-hat activity → light flicker
- Melody energy → background motion
- Overall intensity → scene transformation

Allow users to control:

- Sensitivity
- Minimum and maximum response
- Smoothing
- Attack and release
- Quantization
- Trigger cooldown
- Animation intensity

Users must be able to disable audio reactions and use purely tempo-synchronized movement instead.

A slow emotional beat should not automatically produce aggressive visual effects.

---

# 7. Visual Scene Editor

Create a layered scene editor with a useful preview.

Suggested layout:

**Left panel — Library**
- Saved scenes
- Imported media
- Characters
- Backgrounds
- Presets

**Centre — Visual canvas**
- Live preview
- Direct manipulation
- Transform controls
- Camera framing

**Right panel — Inspector**
- Selected layer properties
- Animation controls
- Audio-reactive mappings
- Loop settings

**Bottom — Timeline**
- Audio waveform
- Beat grid
- Animation tracks
- Keyframes
- Scene markers

The editor should feel clean and intuitive.

Avoid copying a full After Effects interface.

The goal is to make useful animations quickly.

---

# 8. Scene Library

Build a persistent library of reusable scenes.

Every saved scene should contain:

- Scene name
- Unique ID
- Associated assets
- Animation parameters
- Keyframes
- Audio mappings
- Camera settings
- Loop duration
- Preview thumbnail
- Tags
- Date created
- Date modified

### Organization

Support searching and filtering by:

- Character
- Show or inspiration
- Mood
- Genre
- Energy
- Animation style
- Colour palette
- BPM suitability

Allow users to create custom collections.

A scene should be reusable with a new song without duplicating all its assets.

Use stable asset references and avoid broken file paths.

Allow projects and scenes to be exported and imported for backup.

---

# 9. Scene Variety

Do not restrict the application to one visual style.

Support different types of scenes, including:

- Nostalgic cartoon loops
- Character animations
- Stop-motion-inspired scenes
- Anime-inspired visuals
- Film-like compositions
- Funny character loops
- Emotional character moments
- Surreal environments
- Abstract animation
- Experimental typography
- Music-driven motion graphics

These are categories of creative content, not mandatory presets.

The user should be free to make almost anything.

---

# 10. Video Export

Optimize the application for social content.

### Required formats

- 1080 × 1920 vertical video
- 1920 × 1080 landscape video
- 1080 × 1080 square video
- Custom resolution

### Frame rates

- 24 FPS
- 30 FPS
- 60 FPS

### Export options

- MP4 with H.264 video and AAC audio
- Adjustable bitrate and quality
- Custom duration
- Entire song or selected range
- Seamless visual loops
- Audio included or excluded

Use a reliable rendering/export pipeline.

The exported animation must remain synchronized to the audio.

Avoid relying on real-time screen recording for final export.

---

# 11. Performance Requirements

The application must support smooth preview and reliable exports.

Prioritize:

- GPU-accelerated rendering where appropriate
- Efficient texture management
- Media caching
- Frame-accurate rendering
- Deterministic animation
- Audio synchronization
- Reasonable memory use
- Background video export
- Project recovery

Avoid unnecessary dependencies and expensive cloud services.

---

# 12. MVP Scope

Do not attempt to build every advanced feature immediately.

For the first working version, prioritize:

1. Desktop application shell
2. Import audio and visual media
3. BPM detection and manual correction
4. Beat-aligned timeline
5. Layer-based canvas
6. Basic keyframe animation
7. Video and GIF looping
8. Audio-reactive property mapping
9. Reusable scene presets
10. MP4 export

Advanced character rigging, AI motion generation, sophisticated particle systems, and complex 3D scenes can come later.

The first version should already allow me to take a character clip, synchronize it with my beat, create a seamless loop, save it, and export a vertical video.

---

# 13. Architecture and Development

Before writing substantial code:

1. Inspect the available development environment.
2. Check whether any existing Synthosize visualizer project exists.
3. Do not modify SoundLens or SiteRemade.
4. Recommend the best architecture and libraries.
5. Design the scene and preset file formats.
6. Define the audio synchronization system.
7. Explain the export pipeline.
8. Identify difficult technical requirements.
9. Establish a realistic implementation sequence.

Then begin building a functional vertical slice.

The first proof of concept should demonstrate:

**Import beat → import animated visual → detect BPM → synchronize loop → preview → save preset → export MP4.**

Verify that the generated MP4 plays correctly and that visual timing matches the audio.

Add tests for BPM calculations, loop boundaries, serialization, project loading, and export synchronization.

Do not claim a feature is implemented unless it actually works.

---

# 14. Long-Term Vision

I want Synthosize Visual Studio to become an expanding personal library of beat-driven animations.

Over time, I should be able to save hundreds of characters, scenes, animations, and visual worlds.

One beat might use a funny cartoon sequence.

Another might use a dark, lonely character.

Another might use an animated film-inspired environment.

The application should never force me into one style.

The constant is the music.

**I choose the world. Synthosize makes it move with the beat.**

That is the product I want to build.