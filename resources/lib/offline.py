"""
   Copyright (C) 2015- enen92
   This file is part of screensaver.atv4 - https://github.com/enen92/screensaver.atv4

   SPDX-License-Identifier: GPL-2.0-only
   See LICENSE for more information.
"""

import xbmcvfs

from .commonatv import dialog, addon, translate
from .downloader import Downloader
from .playlist import AtvPlaylist

# Array of "All" plus each unique "accessibilityLabel" in entries.json
# Used in a popup to allow the user to choose what to download
locations = ["All", "Italy to Asia", "Iran and Afghanistan", "Dubai", "Africa and the Middle East",
             "California to Vegas", "Southern California to Baja", "China", "Antarctica", "Liwa", "Sahara and Italy",
             "Los Angeles", "San Francisco", "London", "Ireland to Asia", "New York", "West Africa to the Alps",
             "New Zealand", "Caribbean Day", "Hawaii", "Caribbean", "Africa Night", "North America Aurora",
             "New York Night", "Greenland", "Hong Kong", "Korean and Japan Night"]
# Sort the locations list alphabetically and in place
locations.sort()


# Parse the JSON to get a list of URLs and download the files to the download folder
# NOTE: the download folder must be saved by pushing OK in the settings dialog before this will succeed
def offline():
    if addon.getSetting("download-folder") and xbmcvfs.exists(addon.getSetting("download-folder")):
        # Present a popup to the user and allow them to select a single location to download, or all
        locations_chosen_index = dialog.select(translate(32014), locations)
        if locations_chosen_index > -1:
            # Initialize the Playlist class, and get the JSON containing URLs
            top_level_json = AtvPlaylist().get_playlist_json()
            download_list = []
            if top_level_json:
                # Top-level JSON has assets array, initialAssetCount, version. Inspect each block in assets
                for block in top_level_json["assets"]:

                    # If the chosen location was a specific place and not All
                    if not locations[locations_chosen_index] == "All":
                        # Each block contains a location whose name is stored in accessibilityLabel. These may recur
                        # Get the location from the current block
                        location = block["accessibilityLabel"]
                        # Exit block processing early if the location didn't match our preference.
                        # This prevents the location from being added to the download list
                        if not locations[locations_chosen_index] == location:
                            print("Current location {} is not chosen location, skipping download".format(location))
                            continue

                    # TODO grab only 4K SDR for now, but later fall back to others
                    # TODO add place filtering here as well
                    url = block["url-4K-SDR"]

                    # If the URL contains HTTPS, we need revert to HTTP to avoid bad SSL cert
                    # NOTE: Old Apple URLs were HTTP, new URLs are HTTPS with a bad cert
                    if "https" in url:
                        url = url.replace("https://", "http://")
                    download_list.append(url)

            # call downloader if the download_list has been populated
            if download_list:
                Downloader().download_videos_from_urls(download_list)
            else:
                dialog.ok(translate(32000), translate(32012))
    else:
        dialog.ok(translate(32000), translate(32013))
