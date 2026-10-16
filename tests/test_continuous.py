"""
   Copyright (C) 2026 Jeremiah Steven Marquez <jmarquez90@gmail.com>
   This file is part of screensaver.atv4 - https://github.com/enen92/screensaver.atv4

   SPDX-License-Identifier: GPL-2.0-only
   See LICENSE for more information.
"""

import os
import tempfile
import unittest

from kodi_stubs import install

install()

from resources.lib import continuous  # noqa: E402


class FakeProcess:
    def __init__(self):
        self.returncode = None
        self.terminated = False
        self.killed = False

    def poll(self):
        return self.returncode

    def terminate(self):
        self.terminated = True
        self.returncode = -15

    def wait(self, timeout=None):
        return self.returncode

    def kill(self):
        self.killed = True
        self.returncode = -9


class RecordingProcessFactory:
    def __init__(self):
        self.args = None
        self.kwargs = None
        self.process = FakeProcess()

    def __call__(self, args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        return self.process


class ContinuousStreamTests(unittest.TestCase):
    def test_manifest_preserves_the_randomized_session_order(self):
        path = continuous.write_concat_manifest([
            "/storage/aerials/b.mov",
            "http://example.test/a.mov",
        ])
        try:
            with open(path, "r", encoding="utf-8") as manifest:
                self.assertEqual([
                    "ffconcat version 1.0",
                    "file '/storage/aerials/b.mov'",
                    "file 'http://example.test/a.mov'",
                ], manifest.read().splitlines())
        finally:
            os.remove(path)

    def test_start_uses_one_realtime_loopback_transport(self):
        with tempfile.TemporaryDirectory() as directory:
            ffmpeg_path = os.path.join(directory, "ffmpeg")
            with open(ffmpeg_path, "w", encoding="utf-8"):
                pass
            factory = RecordingProcessFactory()
            stream = continuous.ContinuousStream(
                ["first.mov", "second.mov"],
                ffmpeg_path=ffmpeg_path,
                process_factory=factory,
            )

            playback_url = stream.start()
            manifest_path = stream.manifest_path
            try:
                self.assertTrue(playback_url.startswith("udp://@127.0.0.1:"))
                self.assertIn("-re", factory.args)
                self.assertIn("-stream_loop", factory.args)
                self.assertIn("file,http,https,tcp,tls,crypto", factory.args)
                self.assertIn("+resend_headers", factory.args)
                self.assertTrue(factory.args[-1].startswith("udp://127.0.0.1:"))
                self.assertTrue(stream.is_running())
            finally:
                stream.stop()

            self.assertTrue(factory.process.terminated)
            self.assertFalse(os.path.exists(manifest_path))

    def test_unavailable_without_the_libreelec_tool(self):
        stream = continuous.ContinuousStream(
            ["first.mov"], ffmpeg_path="missing-ffmpeg"
        )
        self.assertFalse(stream.is_available())


if __name__ == "__main__":
    unittest.main()
