"""
   Copyright (C) 2015- enen92
   This file is part of screensaver.atv4 - https://github.com/enen92/screensaver.atv4

   SPDX-License-Identifier: GPL-2.0-only
   See LICENSE for more information.
"""

import os
from random import shuffle
# Unused imports removed: json, tarfile, urllib.request

import xbmc
import xbmcvfs

from .commonatv import addon

# Apple-related constants (apple_resources_tar_url, apple_local_tar_path) removed as they are no longer used.
# This also resolves the NameError for addon_path as it was only used in apple_local_tar_path definition.

class AtvPlaylist:
    def __init__(self, ):
        self.playlist = []
        # All logic related to Apple's JSON, force_offline, extra_local_folder_only, etc., is removed.
        # The playlist will be populated solely by local files.
        xbmc.log("[screensaver.localvideo] AtvPlaylist initialized for local-only playback.", level=xbmc.LOGDEBUG)

    def _scan_directory_recursively(self, base_path):
        video_extensions = ['.mp4', '.mov', '.mkv', '.avi', '.ts', '.m2ts']  # Common video extensions
        found_videos = []
        try:
            dirs, files = xbmcvfs.listdir(base_path)
            for file_name in files:
                # Ensure file_name is a string, as listdir can sometimes return unicode
                if not isinstance(file_name, str):
                    file_name = file_name.decode('utf-8', 'ignore')
                if os.path.splitext(file_name)[1].lower() in video_extensions:
                    # xbmcvfs.listdir returns names, not full paths. Need to join.
                    # Ensure base_path also doesn't have trailing slash issues with os.join
                    # However, Kodi paths are usually well-formed with xbmcvfs.
                    full_path = os.path.join(base_path, file_name)
                    found_videos.append(full_path)

            for dir_name in dirs:
                # Ensure dir_name is a string
                if not isinstance(dir_name, str):
                    dir_name = dir_name.decode('utf-8', 'ignore')
                # Construct full path for subdirectory
                sub_dir_path = os.path.join(base_path, dir_name)
                # Recursive call
                found_videos.extend(self._scan_directory_recursively(sub_dir_path))
        except Exception as e:
            xbmc.log(f"[screensaver.localvideo] Error during recursive scan of {base_path}: {e}", level=xbmc.LOGERROR)
        return found_videos

    # get_playlist_json is no longer needed as top_level_json is removed.

    def compute_playlist_array(self):
        # All logic related to Apple videos (top_level_json, block_key_list, etc.) is removed.
        # The playlist is now solely populated by recursively scanning the extra_local_folder.

        extra_folder_path = addon.getSetting("extra-local-folder")
        if extra_folder_path and xbmcvfs.exists(extra_folder_path):
            xbmc.log(f"Scanning extra local folder (recursively): {extra_folder_path}", level=xbmc.LOGDEBUG)
            try:
                local_videos_found = self._scan_directory_recursively(extra_folder_path)
                if local_videos_found:
                    for video_path in local_videos_found:
                        if video_path not in self.playlist:
                            self.playlist.append(video_path)
                            xbmc.log(f"Added local video to playlist: {video_path}", level=xbmc.LOGDEBUG)
                    if self.playlist: # Shuffle if any videos are present (Apple's or local)
                        shuffle(self.playlist)
            except Exception as e:
                xbmc.log(f"Error scanning or listing files in extra local folder: {extra_folder_path}. Error: {e}", level=xbmc.LOGERROR)

        if self.playlist:
            return self.playlist
        else:
            # If after all attempts the playlist is empty, return None.
            # This could happen if no Apple videos were found/selected and no valid local folder/videos were provided.
            xbmc.log("Playlist is empty after attempting to populate from all sources.", level=xbmc.LOGWARNING)
            return None
