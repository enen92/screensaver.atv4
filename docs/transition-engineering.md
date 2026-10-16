<!--
Copyright (C) 2026 Jeremiah Steven Marquez <jmarquez90@gmail.com>
SPDX-License-Identifier: GPL-2.0-only
-->

# Smooth random transitions: engineering baseline

Status: cached and streamed diagnostic checkpoints completed; no transition fix is implemented here.

## Non-negotiable behavior

- Choose Aerial videos randomly. A fixed or pre-generated reel is not an acceptable substitute.
- Show moving Aerial footage continuously across a transition. Hiding a spinner while the video surface is black is not a fix.
- Preserve streaming and local-cache playback.
- Preserve Kodi exit/input behavior, DPMS/CEC behavior, audio behavior, and the rest of the media-center regression surface.
- Leave room for time, date, weather, and shared-family-calendar overlays.

## Current component boundaries

| Responsibility | Current owner | Evidence |
| --- | --- | --- |
| Fetch and parse the Aerial catalog | `resources/lib/playlist.py` | Source-demonstrated |
| Apply location and quality filters | `resources/lib/playlist.py` | Source-demonstrated |
| Substitute a cached path for a network URL | `resources/lib/playlist.py` | Source-demonstrated |
| Randomize a screensaver session | `shuffle(self.playlist)` in `resources/lib/playlist.py` | Source-demonstrated |
| Start each selected item | `Screensaver.start_playback()` in `resources/lib/atv.py` | Source-demonstrated |
| Decode, buffer, render, and tear down an item | Kodi `xbmc.Player` / VideoPlayer | Source-demonstrated in Kodi; not controlled by this add-on |
| Loading and video-window presentation | the add-on skin XML | Source-demonstrated |
| Screensaver lifecycle, exit, DPMS, and CEC | `resources/lib/atv.py`, `resources/lib/screensaver.py`, and `resources/lib/trans.py` | Source-demonstrated |

The smallest replaceable playback boundary is therefore the consumer of the
already-filtered, already-randomized list returned by `AtvPlaylist`. Catalog,
filtering, cache selection, and system lifecycle are outside that boundary.

## Established failure mechanism

The following statements have different evidence levels and must not be blended:

### Demonstrated by this add-on's source

1. The add-on starts one URL with `xbmc.Player.play(..., windowed=True)`.
2. It waits in one-second intervals and polls `isPlaying()`.
3. Only after a poll reports that playback has stopped does it call `play()` for
   the next URL.

This design necessarily creates a scheduling interval between Kodi reaching the
stopped state and the add-on requesting the successor. The interval can approach
one second. The regression harness records this ordering without requiring Kodi.

### Demonstrated by the prior experiments

- Supplying the randomized videos as a Kodi playlist did not eliminate the
  visible inter-item gap.
- Substituting locally cached media did not eliminate the gap.
- The attempted screenshot did not produce a PNG, so it is not visual evidence
  of which Kodi surface was black.

These results rule out network download time and this add-on's explicit
per-item `play()` call as complete explanations. They do not prove that storage
and network latency are irrelevant to startup time.

### Demonstrated by the inspected Kodi 21.3 source

Kodi's item transition tears down or flushes player state before preparing the
next item, including demux/input and render-buffer state. A Kodi playlist still
crosses that item boundary; it does not provide two simultaneously prepared
video frames for a moving crossfade.

### Demonstrated by the target-Pi diagnostic checkpoint

The committed diagnostic build (`5dd818a`) was deployed to LibreELEC 12.2.1 / Kodi 21.3. Its
`resources/lib/atv.py` SHA-256 was verified as
`e10e010a772003d438e68ba3544af0a6b08abb632400e96ea64e63e71348449a` before activation. A natural
transition between two locally cached H.264 Aerial videos produced this timeline:

| Event | Session time | Delta |
| --- | ---: | ---: |
| `playback-ended` | 190196.588 ms | — |
| `stopped-observed` | 190452.682 ms | 256.094 ms |
| `play-requested` | 190452.884 ms | 0.202 ms |
| `play-returned` | 190452.999 ms | 0.115 ms |
| `av-started` | 190904.298 ms | 451.414 ms from request |

Kodi logged demuxer EOF at `16:45:32.212`, followed by queue drain, video-thread exit, codec
deletion, and file close. After the add-on requested the successor, Kodi opened the local file,
created a new input stream and demuxer, opened the DRM PRIME V4L2 H.264 decoder, and created a new
video thread before `onAVStarted()` fired.

The result demonstrates two independent contributors with network transfer absent: 256 ms in the
add-on's polling handoff and 451 ms between the next request and Kodi emitting `onAVStarted()`. The
total was 708 ms from `playback-ended` and approximately 1.12 seconds from demuxer EOF. Removing
the polling delay alone therefore cannot produce a continuous transition.

No resolution or HDMI mode change was logged. `CVideoSyncGbm::Setup` did reopen during the
boundary, so the display path cannot yet be excluded entirely.

The user reports that the visible black interval in the prior equivalent test felt slightly under
one second and lasted only a split second. That observation is consistent with the measured 708 ms
`playback-ended`-to-callback interval, but it is not a frame-accurate display measurement.

### Demonstrated by the target-Pi streamed checkpoint

The controlled streamed comparison retained the existing two-item randomized playlist. Only the
Alaskan Jellies location was enabled, both eligible files were present in the normal cache, and the
test temporarily pointed cache lookup at a nonexistent directory while `force-offline` was false.
Thus either random selection remained eligible but had to use its network URL. Kodi was stopped
before editing settings, and the original settings file had a verified byte-for-byte backup.
Direct edits made while Kodi was running did not change the live screensaver behavior; stop Kodi
before editing add-on settings files so its cached state cannot ignore or overwrite the change.

The first streamed item ran to its natural end without a diagnostic playback-error callback. Its
`play-requested` to `av-started` interval was 619.117 ms. The successor then produced this timeline:

| Event | Session time | Delta |
| --- | ---: | ---: |
| `playback-ended` | 388162.444 ms | — |
| `stopped-observed` | 388646.956 ms | 484.512 ms |
| `play-requested` | 388647.313 ms | 0.357 ms |
| `play-returned` | 388647.731 ms | 0.418 ms |
| `av-started` | 389191.143 ms | 543.830 ms from request |

The callback arrived 1,028.699 ms after `playback-ended`, but the television remained black after
the successor was nominally started. Kodi had created the input stream, demuxer, V4L2 H.264 decoder,
and video thread and emitted `onAVStarted()`. When playback was stopped roughly 30 seconds later,
Kodi logged `OutputPicture - timeout waiting for buffer`. It did not emit the diagnostic
`playback-error` callback.

This is not evidence of a Kodi process crash. It demonstrates a failed streamed handoff after
player setup and proves that `onAVStarted()` cannot be treated as a first-visible-frame signal.

Read-only follow-up analysis assigned stable opaque IDs to both assets. The failed streamed
successor later played from the normal cache to its natural end, which weakens the hypothesis that
the media asset is intrinsically unplayable. Both logged stream locations identify `.mov`, SDR,
2K, AVC renditions, and Kodi opened both with codec ID 27 through the V4L2 H.264 wrapper. The INFO
log does not expose authoritative dimensions, frame rate, color metadata, pixel format, bitrate,
or container structure.

Kodi's Omega source also narrows what the shutdown warning establishes. `OutputPicture` logs the
warning when the render manager's buffer wait returns negatively, but player teardown sets the
output-abort flag before stopping the video thread. Because this warning appeared only after
`CloseFile()` began, it shows that the thread was in the picture-output path during shutdown; it
does not prove that the output path was stalled for the preceding black interval. The current logs
therefore do not distinguish post-start HTTP or demux starvation, lower-level retained decoder
state, and rendering or video-plane output failure.

After the test, Kodi was stopped, the original settings file was restored to its pre-test SHA-256,
the catalog hash was confirmed unchanged, and Kodi was restarted. A cached launch then selected
`source=local`, emitted `av-started`, and stopped cleanly. Visible output in that final regression
launch was not independently confirmed.

### Not yet demonstrated on the target Pi

- The frame-accurate relationship between `onAVStarted()` and the first frame actually visible on
  the television. The user-observed duration is already consistent with the measured timeline.
- Whether any portion of the visible interval occurs in display synchronization despite no logged
  resolution or HDMI mode change.
- Whether the black streamed successor is reproducible and whether it follows the HTTP source
  path, buffering, retained lower-level decoder state, or rendering/video-plane output across the
  item boundary.
- Whether Kodi playback time advances while the television remains black.
- Whether identical codec, resolution, frame-rate, color-space, and HDR metadata
  materially reduce the gap on this exact display chain.
- Whether Kodi exposes a usable final decoded frame during teardown.
- Whether a continuously fed custom renderer can meet hardware-decoding and
  overlay requirements on the Pi.

## Candidate implementation boundaries

These are alternatives, not decisions:

1. **Long-lived dynamic stream.** Keep one Kodi media item open while a local
   process selects random clips at runtime and feeds a continuous stream. This
   avoids Kodi's media-item boundary, but introduces a stream producer and may
   constrain codec changes, seeking, and hardware decoding.
2. **Frame bridge inside the add-on.** Hold a real last or first frame over the
   Kodi teardown interval. This retains `xbmc.Player` and is smaller, but it is a
   visual bridge rather than a moving-video crossfade and depends on obtaining a
   reliable frame.
3. **Independent renderer.** Replace `xbmc.Player` at the playback boundary with
   a renderer that can prebuffer two clips and composite the transition. This is
   the only candidate that naturally supports a true moving crossfade and rich
   overlays, but it has the largest hardware-decoding, lifecycle, and packaging
   surface.

The cached and streamed timing checkpoints are complete, but no candidate should be implemented
until the streamed-successor failure is isolated. External frame-accurate recording remains useful
for validating a final implementation, but it is not a prerequisite for investigating this stall
or comparing architecture boundaries.

## Regression harness

Run from the repository root:

```text
python -m unittest discover -s tests -v
```

The baseline tests are intentionally Kodi-independent. They characterize the
current contract at the future replacement seam:

- eligible items are collected before the session list is shuffled;
- cached paths replace URLs without changing selection membership;
- forced-offline mode excludes only unavailable files; and
- the successor `play()` request happens only after the polling loop observes a
  stopped player.

The instrumented cached and streamed checkpoints are complete. Retain these tests as protection
for randomness, cache behavior, and item selection while the streamed-successor failure is
isolated.

## Diagnostic event timeline

The diagnostic build emits Kodi log entries at `LOGINFO` prefixed with
`[Aerial transition]`. Each entry contains a session-relative monotonic time, a
sequence number, an event name, and only the minimum metadata needed for the
test. It records whether an item is streamed or local and a stable 16-hex-character
SHA-256 prefix derived from the selected asset basename. It deliberately does not
record the basename, URL, query string, or filesystem path.

The next diagnostic build also samples player state through the existing one-second supervision
loop. After each `onAVStarted()` callback it records at most ten `playback-progress` events with
the opaque asset ID, sample number, fractional playback time, total duration, and whether Kodi
reports video playback. The sampler does not add a thread, change selection, or issue player
commands. Its purpose is to separate an internally advancing player with black physical output
from a player whose clock stops after nominal startup.

The relevant intervals are:

| Start event | End event | What the interval measures |
| --- | --- | --- |
| `playback-ended` | `stopped-observed` | The add-on's polling/scheduling contribution |
| `stopped-observed` | `play-requested` | The add-on's selection and dispatch contribution |
| `play-requested` | `av-started` | Kodi input, demux, decode, and renderer startup |
| successive `playback-progress` samples | — | Whether Kodi's playback clock advances after startup |

`play-returned` only records when the Python call returns; it does not claim that
a decoded frame is visible. The streamed checkpoint demonstrated that Kodi can emit
`onAVStarted()` while the television remains black. The later teardown-time output-buffer warning
does not establish the duration or cause of that black interval. Kodi callbacks therefore cannot
prove what the display is showing. External recording remains useful for final visual validation,
but direct observation and Kodi logs are sufficient to reject this streamed handoff as
unsuccessful.
