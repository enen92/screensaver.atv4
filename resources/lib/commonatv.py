"""
   Copyright (C) 2015- enen92
   This file is part of screensaver.atv4 - https://github.com/enen92/screensaver.atv4

   SPDX-License-Identifier: GPL-2.0-only
   See LICENSE for more information.
"""

import xbmcaddon
import xbmcgui

addon = xbmcaddon.Addon()
addon_path = addon.getAddonInfo("path")
addon_icon = addon.getAddonInfo("icon")
dialog = xbmcgui.Dialog()


def translate(text):
    return addon.getLocalizedString(text)


def notification(header, message, time=2000, icon=addon_icon,
                 sound=True):
    xbmcgui.Dialog().notification(header, message, icon, time, sound)
