"""
   Copyright (C) 2015- enen92
   This file is part of screensaver.atv4 - https://github.com/enen92/screensaver.atv4

   SPDX-License-Identifier: GPL-2.0-only
   See LICENSE for more information.
"""

import json
import os
import tarfile
from random import shuffle
from urllib import request

import xbmc
import xbmcvfs

from .commonatv import addon, addon_path

# Apple's URL of the resources.tar file containing entries.json
apple_resources_tar_url = "http://sylvan.apple.com/Aerials/resources.tar"

# Local temporary save location of the Apple TAR file
apple_local_tar_path = os.path.join(addon_path, "resources.tar")

# Local save location of the entries.json file containing video URLs
local_entries_json_path = os.path.join(addon_path, "resources", "entries.json")


# Fetch the TAR file containing the latest entries.json and overwrite the local copy
def get_latest_entries_from_apple():
    print("Downloading the Apple Aerials resources.tar to disk")

    # Setup for disabling SSL cert verification, as the Apple cert is bad
    # https://stackoverflow.com/questions/43204012/how-to-disable-ssl-verification-for-urlretrieve
    # ssl._create_default_https_context = ssl._create_unverified_context

    # Alternatively, just use the HTTP link instead of HTTPS to download the TAR locally
    request.urlretrieve(apple_resources_tar_url, apple_local_tar_path)
    # https://www.tutorialspoint.com/How-are-files-extracted-from-a-tar-file-using-Python
    apple_tar = tarfile.open(apple_local_tar_path)
    print("Extracting entries.json from resources.tar and placing in ./resources")
    apple_tar.extract("entries.json", os.path.join(addon_path, "resources"))

    apple_tar.close()
    print("Cleaning up resources.tar now that we've grabbed entries.json from it")
    os.remove(apple_local_tar_path)


class AtvPlaylist:
    def __init__(self, ):
        self.playlist = []
        # Set a class variable as the string response of our Setting. "True" or "False" expected
        self.force_offline = addon.getSettingBool("force-offline")
        if not xbmc.getCondVisibility("Player.HasMedia"):
            # If we're not forcing offline state, update the local JSON with the copy from Apple
            if not self.force_offline:
                try:
                    # Overwrite the local entries.json from Apple servers
                    get_latest_entries_from_apple()
                    # Load the local JSON into this class instantiation
                    self.local_feed()
                except Exception:
                    # If we hit an exception: ignore, log, and load the local JSON instead
                    xbmc.log(msg="Caught an exception while retrieving Apple's resources.tar to extract entries.json",
                             level=xbmc.LOGWARNING)
                    self.local_feed()
            else:
                # If we're in offline mode, go directly to loading local JSON
                self.local_feed()
        else:
            self.top_level_json = {}

    # Create a class variable with the JSON loaded and parseable
    def local_feed(self):
        with open(local_entries_json_path, "r") as f:
            self.top_level_json = json.loads(f.read())

    def get_playlist_json(self):
        return self.top_level_json

    def compute_playlist_array(self):
        if self.top_level_json:
            # Top-level JSON has assets array, initialAssetCount, version. Inspect each block in "assets"
            for block in self.top_level_json["assets"]:
                # TODO grab only 4K SDR for now, but later fall back to others
                url = block["url-4K-SDR"]

                # If the URL contains HTTPS, we need revert to HTTP to avoid bad SSL cert
                # NOTE: Old Apple URLs were HTTP, new URLs are HTTPS with a bad cert
                if "https" in url:
                    url = url.replace("https://", "http://")

                # Get just the file's name, without the Apple HTTP URL part
                file_name = url.split("/")[-1]

                # Each block contains a location/scene whose name is stored in accessibilityLabel. These may recur
                # location = block["accessibilityLabel"]

                # By default, we assume a local copy of the file doesn't exist
                exists_on_disk = False
                # Inspect the disk to see if the file exists in the download location
                local_file_path = os.path.join(addon.getSetting("download-folder"), file_name)
                if xbmcvfs.exists(local_file_path):
                    # Mark that the file exists on disk
                    exists_on_disk = True
                    # Overwrite the Apple URL with the path to the file on disk
                    url = local_file_path

                # If the file exists locally or we're not in offline mode, add it to the playlist
                if exists_on_disk or not self.force_offline:
                    self.playlist.append(url)
                    # # build setting
                    # TODO add back location enable/disable
                    # thisvideosetting = "enable-" + location.lower().replace(" ", "")
                    # if addon.getSetting(thisvideosetting) == "true":
                    #     self.playlist.append(url)

            # Now that we're done building the playlist, shuffle and return to the caller
            shuffle(self.playlist)
            return self.playlist
        else:
            return None
