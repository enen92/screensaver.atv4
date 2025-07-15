"""
   Copyright (C) 2017- enen92
   This file is part of screensaver.atv4 - https://github.com/enen92/screensaver.atv4

   SPDX-License-Identifier: GPL-2.0-only
   See LICENSE for more information.
"""

from resources.lib import atv
import xbmc

xbmc.log("[screensaver.localvideo] entrypointscreensaver.py invoking resources.lib.atv.run()", level=xbmc.LOGDEBUG)
atv.run()
