# -*- coding: utf-8 -*-
'''
    screensaver.atv4
    Copyright (C) 2015 enen92

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
'''

import xbmcaddon
import xbmcgui
import xbmc
import sys
import os
import urllib
from resources.lib import playlist
from resources.lib import atvplayer
from resources.lib.commonatv import *

class Screensaver(xbmcgui.WindowXMLDialog):
    def __init__( self, *args, **kwargs ):
        pass
    
    def onInit(self):
        xbmc.sleep(400)
        self.getControl(4).setLabel(translate(32008))
        xbmc.executebuiltin("SetProperty(loading,1,home)")
        atvPlaylist = playlist.AtvPlaylist()
        self.videoplaylist = atvPlaylist.getPlaylist()
        if self.videoplaylist:
            xbmc.executebuiltin("ClearProperty(loading,Home)")
            self.getControl(1).setImage("black.jpg")
            self.atv4player = atvplayer.ATVPlayer()
            if not xbmc.getCondVisibility("Player.HasMedia"):
                self.atv4player.play(self.videoplaylist,windowed=True)
        else:
            xbmc.executebuiltin("ClearProperty(loading,Home)")
            self.getControl(3).setLabel(translate(32007))


    def onAction(self,action):
        xbmc.PlayList(1).clear()
        xbmc.Player().stop()
        self.close()


if __name__ == '__main__':
    screensaver = Screensaver(
        'screensaver-atv4.xml',
        addon_path,
        'default',
        '',
    )
    screensaver.doModal()
    del screensaver
