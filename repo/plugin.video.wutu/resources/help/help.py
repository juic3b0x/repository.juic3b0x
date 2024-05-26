# -*- coding: utf-8 -*-
"""
	WUTU
"""

from resources.lib.modules.control import addonPath, addonId, getwutuVersion, joinPath
from resources.lib.windows.textviewer import TextViewerXML


def get(file):
	wutu_path = addonPath(addonId())
	wutu_version = getwutuVersion()
	helpFile = joinPath(wutu_path, 'resources', 'help', file + '.txt')
	f = open(helpFile, 'r', encoding='utf-8', errors='ignore')
	text = f.read()
	f.close()
	heading = '[B]wutu -  v%s - %s[/B]' % (wutu_version, file)
	windows = TextViewerXML('textviewer.xml', wutu_path, heading=heading, text=text)
	windows.run()
	del windows