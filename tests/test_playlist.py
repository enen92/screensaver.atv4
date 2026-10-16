"""
   Copyright (C) 2026 Jeremiah Steven Marquez <jmarquez90@gmail.com>
   This file is part of screensaver.atv4 - https://github.com/enen92/screensaver.atv4

   SPDX-License-Identifier: GPL-2.0-only
   See LICENSE for more information.
"""

import os
import unittest
from unittest.mock import Mock, patch

from kodi_stubs import install

install()

from resources.lib import playlist  # noqa: E402


class PlaylistContractTests(unittest.TestCase):
    def make_playlist(self, force_offline=False):
        subject = playlist.AtvPlaylist.__new__(playlist.AtvPlaylist)
        subject.playlist = []
        subject.force_offline = force_offline
        subject.top_level_json = {
            "assets": [
                {
                    "accessibilityLabel": "Alpha",
                    "url-1080-H264": "https://example.test/alpha.mov",
                },
                {
                    "accessibilityLabel": "Beta",
                    "url-1080-H264": "https://example.test/beta.mov",
                },
            ]
        }
        return subject

    @staticmethod
    def setting_value(key):
        if key == "download-folder":
            return os.path.join("cache", "aerials")
        return ""

    def test_collects_eligible_items_then_shuffles_once(self):
        subject = self.make_playlist()
        shuffle = Mock(side_effect=lambda items: items.reverse())

        with patch.object(playlist, "compute_block_key_list", return_value=["url-1080-H264"]), \
                patch.object(playlist.addon, "getSettingBool", return_value=True), \
                patch.object(playlist.addon, "getSetting", side_effect=self.setting_value), \
                patch.object(playlist.xbmcvfs, "exists", return_value=False), \
                patch.object(playlist, "shuffle", shuffle):
            result = subject.compute_playlist_array()

        self.assertEqual([
            "http://example.test/beta.mov",
            "http://example.test/alpha.mov",
        ], result)
        shuffle.assert_called_once_with(result)

    def test_cached_path_replaces_url_without_changing_membership(self):
        subject = self.make_playlist()
        local_alpha = os.path.join("cache", "aerials", "alpha.mov")

        with patch.object(playlist, "compute_block_key_list", return_value=["url-1080-H264"]), \
                patch.object(playlist.addon, "getSettingBool", return_value=True), \
                patch.object(playlist.addon, "getSetting", side_effect=self.setting_value), \
                patch.object(playlist.xbmcvfs, "exists", side_effect=lambda path: path == local_alpha), \
                patch.object(playlist, "shuffle", return_value=None):
            result = subject.compute_playlist_array()

        self.assertEqual([
            local_alpha,
            "http://example.test/beta.mov",
        ], result)

    def test_forced_offline_excludes_only_uncached_items(self):
        subject = self.make_playlist(force_offline=True)
        local_alpha = os.path.join("cache", "aerials", "alpha.mov")

        with patch.object(playlist, "compute_block_key_list", return_value=["url-1080-H264"]), \
                patch.object(playlist.addon, "getSettingBool", return_value=True), \
                patch.object(playlist.addon, "getSetting", side_effect=self.setting_value), \
                patch.object(playlist.xbmcvfs, "exists", side_effect=lambda path: path == local_alpha), \
                patch.object(playlist, "shuffle", return_value=None):
            result = subject.compute_playlist_array()

        self.assertEqual([local_alpha], result)


if __name__ == "__main__":
    unittest.main()
