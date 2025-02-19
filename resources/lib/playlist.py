"""
   Copyright (C) 2015- enen92
   This file is part of screensaver.atv4 - https://github.com/enen92/screensaver.atv4

   SPDX-License-Identifier: GPL-2.0-only
   See LICENSE for more information.
"""

import json
import plistlib
import os
import tarfile
from random import shuffle
from urllib import request

import xbmc
import xbmcvfs

from .commonatv import addon, addon_path, find_ranked_key_in_dict, compute_block_key_list

# Apple's URL of the resources.tar file containing entries.json
apple_resources_tar_url = "http://sylvan.apple.com/Aerials/resources-15.tar"

# Local temporary save location of the Apple TAR file
apple_local_tar_path = os.path.join(addon_path, "resources.tar")

# Local save location of the entries.json file containing video URLs
local_entries_json_path = os.path.join(addon_path, "resources", "entries.json")

# Path to the local file where we store the plist with video descriptions
local_plist_path_parts = [addon_path, "resources", "TVIdleScreenStrings.bundle", "{}.lproj", "Localizable.nocache.strings"]

# location in the tar file for the plist file with descriptions
language_description_format_str = "TVIdleScreenStrings.bundle/{}.lproj/Localizable.nocache.strings"

def tar_has_member(tar, key):
    try:
        tar.getmember(key)
        return True
    except KeyError:
        return False

# Fetch the TAR file containing the latest entries.json and overwrite the local copy
def get_latest_entries_from_apple():
    xbmc.log("Downloading the Apple Aerials resources.tar to disk", level=xbmc.LOGDEBUG)

    # Alternatively, just use the HTTP link instead of HTTPS to download the TAR locally
    request.urlretrieve(apple_resources_tar_url, apple_local_tar_path)
    # https://www.tutorialspoint.com/How-are-files-extracted-from-a-tar-file-using-Python
    apple_tar = tarfile.open(apple_local_tar_path)
    xbmc.log("Extracting entries.json and video descriptions from resources.tar and placing in ./resources", level=xbmc.LOGDEBUG)
    dest_dir = os.path.join(addon_path, "resources")
    apple_tar.extract("entries.json", dest_dir)
    language = xbmc.getLanguage(xbmc.ISO_639_1)
    if tar_has_member(apple_tar, language_description_format_str.format(language)):
        apple_tar.extract(language_description_format_str.format(language), dest_dir)
    else:
        xmbc.log("No descriptions for language {}, defaulting to English", level=xbmc.LOGWARNING)
        apple_tar.extract(language_description_format_str.format('en'), dest_dir)

    apple_tar.close()
    xbmc.log("Deleting resources.tar now that we've grabbed what we need from it", level=xbmc.LOGDEBUG)
    os.remove(apple_local_tar_path)

class PlaylistEntry:
    def __init__(self, url, location, pois):
        self.url = url
        self.location = location
        self.pois = pois

class POI:
    def __init__(self, secs, description):
        self.secs = secs
        self.description = description
    def __repr__(self):
        return "POI secs:{}, description: {}".format(self.secs, self.description)

class AtvPlaylist:
    def __init__(self, ):
        self.playlist = []
        # Set a class variable as the Bool response of our Setting.
        self.force_offline = addon.getSettingBool("force-offline")
        if not xbmc.getCondVisibility("Player.HasMedia"):
            # If we're not forcing offline state and not using custom JSON:
            if not self.force_offline and addon.getSettingBool("get-videos-from-apple"):
                try:
                    # Update local JSON with the copy from Apple
                    get_latest_entries_from_apple()
                except Exception:
                    # If we hit an exception: ignore, log, and continue
                    xbmc.log(msg="Caught an exception while retrieving Apple's resources.tar to extract entries.json",
                             level=xbmc.LOGWARNING)
            # Regardless of if we grabbed new Apple JSON, hit an exception, or are in offline mode, load the local copy
            with open(local_entries_json_path, "r") as f:
                self.top_level_json = json.loads(f.read())

            language = xbmc.getLanguage(xbmc.ISO_639_1)
            plist_language_parts = local_plist_path_parts.copy()
            plist_language_parts[3] = plist_language_parts[3].format(language)
            plist_path = os.path.join(*plist_language_parts)
            if not xbmcvfs.exists(plist_path):
                xbmc.log("No descriptions for language {}, defaulting to English", level=xbmc.LOGWARNING)
                plist_language_parts[3] = "en.lproj"
                plist_path = os.path.join(*plist_language_parts)
            if xbmcvfs.exists(plist_path):
                with open(plist_path, "rb") as f:
                    self.plist = plistlib.loads(f.read())
            else:
                xbmc.log("Could not find description file, cannot enable subtitles", level=xbmc.LOGWARNING)
                self.plist = None
        else:
            self.top_level_json = {}

    def get_playlist_json(self):
        return self.top_level_json

    def compute_playlist_array(self):
        if self.top_level_json:

            # Parse the H264, HDR, and 4K settings to determine URL preference.
            block_key_list = compute_block_key_list(addon.getSettingBool("enable-4k"),
                                                    addon.getSettingBool("enable-hdr"),
                                                    addon.getSettingBool("enable-hevc"))

            # Top-level JSON has assets array, initialAssetCount, version. Inspect each block in "assets"
            for block in self.top_level_json["assets"]:
                # Each block contains a location/scene whose name is stored in accessibilityLabel. These may recur
                # Retrieve the location name
                location = block["accessibilityLabel"]
                try:
                    # Get the corresponding setting Bool by adding "enable-" + lowercase + no whitespace
                    current_location_enabled = addon.getSettingBool("enable-" + location.lower().replace(" ", ""))
                except TypeError:
                    xbmc.log("Location {} did not have a matching enable/disable setting".format(location),
                             level=xbmc.LOGDEBUG)
                    # Leave the location in the rotation if we couldn't find a corresponding setting disabling it
                    current_location_enabled = True

                # Skip the rest of the loop if the current block's location setting has been explicitly disabled
                if not current_location_enabled:
                    continue

                # Get the URL from the current block to download
                url = find_ranked_key_in_dict(block, block_key_list)

                # If the URL is empty/None, skip the rest of the loop
                if not url:
                    continue

                # If the URL contains HTTPS, we need revert to HTTP to avoid bad SSL cert
                # NOTE: Old Apple URLs were HTTP, new URLs are HTTPS with a bad cert
                if "https" in url:
                    url = url.replace("https://", "http://")

                # Get just the file's name, without the Apple HTTP URL part
                file_name = url.split("/")[-1]

                # By default, we assume a local copy of the file doesn't exist
                exists_on_disk = False
                # Inspect the disk to see if the file exists in the download location
                local_file_path = os.path.join(addon.getSetting("download-folder"), file_name)
                if xbmcvfs.exists(local_file_path):
                    # Mark that the file exists on disk
                    exists_on_disk = True
                    # Overwrite the network URL with the local path to the file
                    url = local_file_path
                    xbmc.log("Video available locally, path is: {}".format(local_file_path), level=xbmc.LOGDEBUG)

                # If the file exists locally or we're not in offline mode, add it to the playlist
                if exists_on_disk or not self.force_offline:
                    xbmc.log("Adding video for location {} to playlist".format(location), level=xbmc.LOGDEBUG)
                    pois = []
                    if self.plist:
                        if "pointsOfInterest" in block:
                            for secs, key in block["pointsOfInterest"].items():
                                if key in self.plist:
                                    pois.append(POI(int(secs), self.plist[key]))
                        elif "shotID" in block and block["shotID"] in self.plist:
                            pois.append(POI(0,self.plist[block["shotID"]]))
                        else:
                            xbmc.log("Could not find any descriptions for {}".format(url), level=xbmc.LOGWARNING)
                        pois.sort(key=lambda poi: poi.secs, reverse=False)
                    self.playlist.append(PlaylistEntry(url, location, pois))

            # Now that we're done building the playlist, shuffle and return to the caller
            shuffle(self.playlist)
            return self.playlist
        else:
            return None
