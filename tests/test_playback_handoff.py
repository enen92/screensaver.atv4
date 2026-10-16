"""
   Copyright (C) 2026 Jeremiah Steven Marquez <jmarquez90@gmail.com>
   This file is part of screensaver.atv4 - https://github.com/enen92/screensaver.atv4

   SPDX-License-Identifier: GPL-2.0-only
   See LICENSE for more information.
"""

import unittest
from unittest.mock import Mock, patch

from kodi_stubs import install

install()

from resources.lib import atv  # noqa: E402


class RecordingMonitor:
    def __init__(self, events):
        self.events = events

    def waitForAbort(self, timeout):
        self.events.append(("wait", timeout))
        return False

    def abortRequested(self):
        return False


class RecordingDiagnostics:
    def __init__(self):
        self.events = []

    def record(self, event, **fields):
        self.events.append((event, fields))


class StoppedPlayer:
    def __init__(self, owner, events, stop_after_plays):
        self.owner = owner
        self.events = events
        self.stop_after_plays = stop_after_plays
        self.play_count = 0
        self.active_item = None

    def set_active_item(self, item):
        self.active_item = item

    def play(self, item, windowed=False):
        self.play_count += 1
        self.events.append(("play", item, windowed))
        if self.play_count >= self.stop_after_plays:
            self.owner.active = False

    def isPlaying(self):
        self.events.append(("isPlaying", False))
        return False

    def record_progress_sample(self):
        raise AssertionError("progress must not be sampled after playback stops")


class PlaybackHandoffContractTests(unittest.TestCase):
    def make_screensaver(self, playlist_items, stop_after_plays):
        events = []
        subject = object.__new__(atv.Screensaver)
        subject.active = True
        subject.video_playlist = playlist_items
        subject.atv4player = StoppedPlayer(subject, events, stop_after_plays)
        subject.transition_diagnostics = RecordingDiagnostics()
        return subject, events, subject.transition_diagnostics.events

    def test_waits_before_observing_stop_and_requesting_successor(self):
        subject, events, diagnostic_events = self.make_screensaver(
            ["first.mov", "second.mov"], 2
        )
        original_monitor = atv.monitor
        atv.monitor = RecordingMonitor(events)
        try:
            subject.start_playback()
        finally:
            atv.monitor = original_monitor

        self.assertEqual([
            ("play", "first.mov", True),
            ("wait", 1),
            ("isPlaying", False),
            ("play", "second.mov", True),
        ], events)
        self.assertEqual([
            ("playback-loop-start", {"playlist_count": 2}),
            ("play-requested", {
                "asset_id": atv.playback_asset_id("first.mov"),
                "index": 0,
                "source": "local",
            }),
            ("play-returned", {
                "asset_id": atv.playback_asset_id("first.mov"),
                "index": 0,
            }),
            ("stopped-observed", {
                "asset_id": atv.playback_asset_id("first.mov"),
                "index": 0,
            }),
            ("play-requested", {
                "asset_id": atv.playback_asset_id("second.mov"),
                "index": 1,
                "source": "local",
            }),
            ("play-returned", {
                "asset_id": atv.playback_asset_id("second.mov"),
                "index": 1,
            }),
        ], diagnostic_events)

    def test_cycles_the_once_randomized_session_order(self):
        subject, events, _ = self.make_screensaver(
            ["first.mov", "second.mov"], 3
        )
        original_monitor = atv.monitor
        atv.monitor = RecordingMonitor(events)
        try:
            subject.start_playback()
        finally:
            atv.monitor = original_monitor

        played_items = [event[1] for event in events if event[0] == "play"]
        self.assertEqual(["first.mov", "second.mov", "first.mov"], played_items)

    def test_prefers_continuous_transport_when_ffmpeg_is_available(self):
        subject, _, _ = self.make_screensaver(["first.mov", "second.mov"], 1)
        continuous_stream = Mock()
        continuous_stream.is_available.return_value = True
        subject.start_continuous_playback = Mock()
        subject.start_direct_playback = Mock()

        with patch.object(atv, "ContinuousStream", return_value=continuous_stream):
            subject.start_playback()

        subject.start_continuous_playback.assert_called_once_with(continuous_stream)
        subject.start_direct_playback.assert_not_called()

    def test_intentional_shutdown_does_not_start_direct_fallback(self):
        subject, _, _ = self.make_screensaver(["first.mov", "second.mov"], 1)
        continuous_stream = Mock()
        continuous_stream.is_available.return_value = True
        subject.start_direct_playback = Mock()

        def stop_during_continuous_playback(_stream):
            subject.active = False
            raise RuntimeError("continuous FFmpeg process exited")

        subject.start_continuous_playback = stop_during_continuous_playback

        with patch.object(atv, "ContinuousStream", return_value=continuous_stream):
            subject.start_playback()

        continuous_stream.stop.assert_called_once_with()
        subject.start_direct_playback.assert_not_called()

    def test_player_callbacks_are_recorded_without_controlling_playback(self):
        diagnostics = RecordingDiagnostics()
        player = atv.TransitionPlayer(diagnostics)
        player.set_active_item("https://example.test/a.mov")
        asset_id = atv.playback_asset_id("https://example.test/a.mov")

        player.onAVStarted()
        player.onPlayBackEnded()
        player.onPlayBackStopped()
        player.onPlayBackError()

        self.assertEqual([
            ("av-started", {"asset_id": asset_id}),
            ("playback-ended", {"asset_id": asset_id}),
            ("playback-stopped", {"asset_id": asset_id}),
            ("playback-error", {"asset_id": asset_id}),
        ], diagnostics.events)

    def test_source_classification_does_not_log_the_media_location(self):
        self.assertEqual("stream", atv.playback_source("https://example.test/a.mov"))
        self.assertEqual("stream", atv.playback_source("http://example.test/a.mov"))
        self.assertEqual("local", atv.playback_source("/storage/aerials/a.mov"))

    def test_asset_id_matches_stream_and_cached_copy_without_exposing_location(self):
        stream = "https://example.test/private/path/A%20Scene.mov?token=secret"
        cached = "/storage/aerial-cache/A Scene.mov"

        self.assertEqual(atv.playback_asset_id(stream), atv.playback_asset_id(cached))
        self.assertNotIn("A Scene", atv.playback_asset_id(stream))
        self.assertEqual(16, len(atv.playback_asset_id(stream)))

    def test_progress_sampling_is_bounded_and_records_player_time(self):
        diagnostics = RecordingDiagnostics()
        player = atv.TransitionPlayer(diagnostics)
        player.set_active_item("https://example.test/a.mov")
        player.isPlayingVideo = lambda: True
        player.getTime = lambda: 2.5
        player.getTotalTime = lambda: 189.0

        player.onAVStarted()
        for _ in range(player.progress_sample_limit + 1):
            player.record_progress_sample()

        progress = [event for event in diagnostics.events
                    if event[0] == "playback-progress"]
        self.assertEqual(player.progress_sample_limit, len(progress))
        self.assertEqual({
            "asset_id": atv.playback_asset_id("https://example.test/a.mov"),
            "sample": 0,
            "time_s": "2.500",
            "total_s": "189.000",
            "video": "true",
        }, progress[0][1])

    def test_diagnostics_emit_a_parseable_monotonic_timeline(self):
        timestamps = iter([1_000_000_000, 1_250_000_000])
        diagnostics = atv.TransitionDiagnostics(clock=lambda: next(timestamps))

        with patch.object(atv.xbmc, "log") as kodi_log:
            diagnostics.record("play-requested", index=4, source="stream")

        kodi_log.assert_called_once_with(
            msg=(
                "[Aerial transition] seq=1 elapsed_ms=250.000 "
                "event=play-requested index=4 source=stream"
            ),
            level=atv.xbmc.LOGINFO,
        )


if __name__ == "__main__":
    unittest.main()
