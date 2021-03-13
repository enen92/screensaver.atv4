"""
   Copyright (C) 2015- enen92
   This file is part of screensaver.atv4 - https://github.com/enen92/screensaver.atv4

   SPDX-License-Identifier: GPL-2.0-only
   See LICENSE for more information.
"""

import os
import xbmcaddon
import xbmcgui

addon = xbmcaddon.Addon()
addon_path = addon.getAddonInfo("path")
addon_icon = addon.getAddonInfo("icon")
dialog = xbmcgui.Dialog()

# Apple's URL of the resources.tar file containing entries.json
apple_resources_tar_url = "http://sylvan.apple.com/Aerials/resources.tar"

# Local temporary save location of the Apple TAR file
apple_local_tar_path = os.path.join(addon_path, "resources.tar")

# Local save location of the entries.json file containing video URLs
local_entries_json_path = os.path.join(addon_path, "resources", "entries.json")

# Array of "All" plus each unique "accessibilityLabel" in entries.json
places = ["All", "London", "Hawaii", "New York City", "San Francisco",
          "China", "Greenland", "Dubai", "Los Angeles", "Liwa", "Hong Kong"]


def translate(text):
    return addon.getLocalizedString(text)


def notification(header, message, time=2000, icon=addon_icon,
                 sound=True):
    xbmcgui.Dialog().notification(header, message, icon, time, sound)
