"""
   Copyright (C) 2026 Jeremiah Steven Marquez <jmarquez90@gmail.com>
   This file is part of screensaver.atv4 - https://github.com/enen92/screensaver.atv4

   SPDX-License-Identifier: GPL-2.0-only
   See LICENSE for more information.
"""

import os
import socket
import subprocess
import tempfile


FFMPEG_PATH = "/storage/.kodi/addons/tools.ffmpeg-tools/bin/ffmpeg"


def _concat_quote(value):
    """Quote one concat-demuxer path without exposing it to a shell."""
    return "'{}'".format(str(value).replace("'", "'\\''"))


def write_concat_manifest(items):
    """Write the already-randomized session order for FFmpeg's concat demuxer."""
    manifest = tempfile.NamedTemporaryFile(
        mode="w",
        prefix="screensaver-atv4-",
        suffix=".ffconcat",
        delete=False,
        encoding="utf-8",
        newline="\n",
    )
    try:
        manifest.write("ffconcat version 1.0\n")
        for item in items:
            manifest.write("file {}\n".format(_concat_quote(item)))
        return manifest.name
    finally:
        manifest.close()


def reserve_udp_port():
    """Ask the kernel for an unused loopback UDP port."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


class ContinuousStream:
    """Remux a shuffled Aerial playlist into one Kodi player session."""

    def __init__(self, items, ffmpeg_path=FFMPEG_PATH, process_factory=subprocess.Popen):
        self.items = list(items)
        self.ffmpeg_path = ffmpeg_path
        self.process_factory = process_factory
        self.manifest_path = None
        self.process = None
        self.playback_url = None

    def is_available(self):
        return bool(self.items) and os.path.isfile(self.ffmpeg_path)

    def _command(self, port):
        output_url = "udp://127.0.0.1:{}?pkt_size=1316".format(port)
        return [
            self.ffmpeg_path,
            "-nostdin",
            "-hide_banner",
            "-loglevel",
            "error",
            "-re",
            "-stream_loop",
            "-1",
            "-protocol_whitelist",
            "file,http,https,tcp,tls,crypto",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            self.manifest_path,
            "-map",
            "0:v:0",
            "-an",
            "-c:v",
            "copy",
            "-mpegts_flags",
            "+resend_headers",
            "-f",
            "mpegts",
            output_url,
        ]

    def start(self):
        if not self.is_available():
            raise RuntimeError("FFmpeg Tools is unavailable")

        self.manifest_path = write_concat_manifest(self.items)
        port = reserve_udp_port()
        self.playback_url = "udp://@127.0.0.1:{}".format(port)
        try:
            self.process = self.process_factory(
                self._command(port),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=True,
            )
        except Exception:
            self.stop()
            raise
        return self.playback_url

    def is_running(self):
        return self.process is not None and self.process.poll() is None

    def stop(self):
        process = self.process
        self.process = None
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=2)

        if self.manifest_path:
            try:
                os.remove(self.manifest_path)
            except FileNotFoundError:
                pass
            self.manifest_path = None
