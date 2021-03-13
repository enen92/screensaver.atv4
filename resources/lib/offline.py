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
places = ["All", "London", "Hawaii", "New York City", "San Francisco",
          "China", "Greenland", "Dubai", "Los Angeles", "Liwa", "Hong Kong"]


# Parse the JSON to get a list of URLs and download the files to the download folder
def offline():
    if addon.getSetting("download-folder") and xbmcvfs.exists(addon.getSetting("download-folder")):
        choose = dialog.select(translate(32014), places)
        if choose > -1:
            # Initialize the Playlist class, and get the JSON containing URLs
            top_level_json = AtvPlaylist().get_playlist_json()
            download_list = []
            if top_level_json:
                # Top-level JSON has assets array, initialAssetCount, version. Inspect each block in assets
                for block in top_level_json["assets"]:
                    # Each block contains a location/scene whose name is stored in accessibilityLabel. These may recur
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
