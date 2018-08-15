# -*- coding: utf-8 -*-

"""
    screensaver.atv4
    Copyright (C) 2015-2018 enen92

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import json
import xbmc
import xbmcgui
import offline as off
import playlist
import threading
from commonatv import translate, addon, addon_path


class Screensaver(xbmcgui.WindowXML):

    class ExitMonitor(xbmc.Monitor):

        def __init__(self):
            pass

        def onScreensaverDeactivated(self):
            print("KODI ASKED TO DEACTIVATE THE SCREENSAVER...and it has just started..")

    def __init__(self, *args, **kwargs):
        #Enable monitor to check for deactivation
        self.active = True
        self.monitor = self.ExitMonitor()
        # get the list of videos
        self.videoplaylist = playlist.AtvPlaylist().getPlaylist()

    def onInit(self):
        self.getControl(32502).setLabel(translate(32008))
        self.setProperty("screensaver-atv4-loading", "true")

        if self.videoplaylist:
            self.setProperty("screensaver-atv4-loading", "false")
            self.atv4player = xbmc.Player()

            # Start player thread (it will block with waitforabort there)
            threading.Thread(target=self.start_playback).start()

        else:
            self.novideos()


    def novideos(self):
        self.setProperty("screensaver-atv4-loading", "false")
        self.getControl(32503).setVisible(True)
        self.getControl(32503).setLabel(translate(32007))


    def clearAll(self, close=True):
        self.active = False
        self.atv4player.stop()
        self.close()

    def onAction(self, action):
        addon.setSetting("is_locked", "false")
        self.clearAll()

    def start_playback(self):
        self.playindex = 0
        self.atv4player.play(self.videoplaylist[self.playindex], windowed=True)
        while self.active and not self.monitor.abortRequested():
            self.monitor.waitForAbort(1)
            if not self.atv4player.isPlaying() and self.active:
                if self.playindex < len(self.videoplaylist) - 1:
                    self.playindex += 1
                else:
                    self.playindex = 0
                self.atv4player.play(self.videoplaylist[self.playindex], windowed=True)


def run(params=False):
    if not params:
        screensaver = Screensaver(
            'screensaver-atv4.xml',
            addon_path,
            'default',
            '',
        )
        screensaver.doModal()
        xbmc.sleep(100)
        del screensaver
