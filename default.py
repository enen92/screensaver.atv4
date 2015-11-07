# -*- coding: utf-8 -*-
'''
    screensaver.atv3
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

import sys
import playlist
import xbmc


if __name__ == '__main__':
	atvPlaylist = playlist.AtvPlaylist()
	playlist = atvPlaylist.getPlaylist()
	if playlist:
		xbmc.Player().play(playlist)
	sys.modules.clear()
