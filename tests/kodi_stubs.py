"""
   Copyright (C) 2026 Jeremiah Steven Marquez <jmarquez90@gmail.com>
   This file is part of screensaver.atv4 - https://github.com/enen92/screensaver.atv4

   SPDX-License-Identifier: GPL-2.0-only
   See LICENSE for more information.
"""

# Minimal Kodi module stubs used by the host-side regression tests.

import sys
import types


class FakeAddon:
    def __init__(self):
        self.settings = {}

    def getAddonInfo(self, key):
        return {"path": ".", "icon": ""}.get(key, "")

    def getLocalizedString(self, text):
        return str(text)

    def getSetting(self, key):
        return self.settings.get(key, "")

    def getSettingBool(self, key):
        return bool(self.settings.get(key, False))

    def getSettingInt(self, key):
        return int(self.settings.get(key, 0))

    def setSettingBool(self, key, value):
        self.settings[key] = value


class DummyDialog:
    def notification(self, *args, **kwargs):
        pass


class DummyWindow:
    pass


class DummyMonitor:
    def waitForAbort(self, timeout):
        return False

    def abortRequested(self):
        return False


def install():
    """Install enough of Kodi's Python API for importing the add-on modules."""
    xbmc = types.ModuleType("xbmc")
    xbmc.LOGDEBUG = 0
    xbmc.LOGWARNING = 1
    xbmc.LOGERROR = 2
    xbmc.LOGINFO = 3
    xbmc.Monitor = DummyMonitor
    xbmc.Player = object
    xbmc.log = lambda *args, **kwargs: None
    xbmc.sleep = lambda *args, **kwargs: None
    xbmc.executebuiltin = lambda *args, **kwargs: None
    xbmc.executeJSONRPC = lambda *args, **kwargs: '{"result":{"value":0}}'
    xbmc.getCondVisibility = lambda *args, **kwargs: False

    xbmcgui = types.ModuleType("xbmcgui")
    xbmcgui.Dialog = DummyDialog
    xbmcgui.DialogProgress = DummyDialog
    xbmcgui.WindowXML = DummyWindow
    xbmcgui.WindowXMLDialog = DummyWindow

    xbmcaddon = types.ModuleType("xbmcaddon")
    xbmcaddon.Addon = FakeAddon

    xbmcvfs = types.ModuleType("xbmcvfs")
    xbmcvfs.exists = lambda path: False
    xbmcvfs.translatePath = lambda path: path

    sys.modules.update({
        "xbmc": xbmc,
        "xbmcaddon": xbmcaddon,
        "xbmcgui": xbmcgui,
        "xbmcvfs": xbmcvfs,
    })

