# -*- coding: utf-8 -*-
"""
	WUTU
"""

from resources.lib.modules import control, log_utils, my_accounts
from sys import version_info, platform as sys_platform
from threading import Thread
window = control.homeWindow
pythonVersion = '{}.{}.{}'.format(version_info[0], version_info[1], version_info[2])
plugin = 'plugin://plugin.video.wutu/'
LOGINFO = log_utils.LOGINFO


class CheckSettingsFile:
	def run(self):
		try:
			control.log('[ plugin.video.wutu ]  CheckSettingsFile Service Starting...', LOGINFO)
			window.clearProperty('wutu_settings')
			profile_dir = control.dataPath
			if not control.existsPath(profile_dir):
				success = control.makeDirs(profile_dir)
				if success: control.log('%s : created successfully' % profile_dir, LOGINFO)
			else: control.log('%s : already exists' % profile_dir, LOGINFO)
			settings_xml = control.joinPath(profile_dir, 'settings.xml')
			if not control.existsPath(settings_xml):
				control.setSetting('trakt.message2', '')
				control.log('%s : created successfully' % settings_xml, LOGINFO)
			else: control.log('%s : already exists' % settings_xml, LOGINFO)
			return control.log('[ plugin.video.wutu ]  Finished CheckSettingsFile Service', LOGINFO)
		except:
			log_utils.error()

class SettingsMonitor(control.monitor_class):
	def __init__ (self):
		control.monitor_class.__init__(self)
		control.refresh_playAction()
		control.refresh_libPath()
		window.setProperty('wutu.debug.reversed', control.setting('debug.reversed'))
		control.log('[ plugin.video.wutu ]  Settings Monitor Service Starting...', LOGINFO)

	def onSettingsChanged(self): # Kodi callback when the addon settings are changed
		window.clearProperty('wutu_settings')
		control.sleep(50)
		refreshed = control.make_settings_dict()
		control.refresh_playAction()
		control.refresh_libPath()
		control.refresh_debugReversed()

class SyncMyAccounts:
	def run(self):
		control.log('[ plugin.video.wutu ]  Sync "My Accounts" Service Starting...', LOGINFO)
		my_accounts.syncMyAccounts(silent=True)
		return control.log('[ plugin.video.wutu ]  Finished Sync "My Accounts" Service', LOGINFO)

class ReuseLanguageInvokerCheck:
	def run(self):
		control.log('[ plugin.video.wutu ]  ReuseLanguageInvokerCheck Service Starting...', LOGINFO)
		try:
			import xml.etree.ElementTree as ET
			from resources.lib.modules.language_invoker import gen_file_hash
			addon_xml = control.joinPath(control.addonPath('plugin.video.wutu'), 'addon.xml')
			tree = ET.parse(addon_xml)
			root = tree.getroot()
			current_addon_setting = control.addon('plugin.video.wutu').getSetting('reuse.languageinvoker')
			try: current_xml_setting = [str(i.text) for i in root.iter('reuselanguageinvoker')][0]
			except: return control.log('[ plugin.video.wutu ]  ReuseLanguageInvokerCheck failed to get settings.xml value', LOGINFO)
			if current_addon_setting == '':
				current_addon_setting = 'true'
				control.setSetting('reuse.languageinvoker', current_addon_setting)
			if current_xml_setting == current_addon_setting:
				return control.log('[ plugin.video.wutu ]  ReuseLanguageInvokerCheck Service Finished', LOGINFO)
			control.okDialog(message='%s\n%s' % (control.lang(33023), control.lang(33020)))
			for item in root.iter('reuselanguageinvoker'):
				item.text = current_addon_setting
				hash_start = gen_file_hash(addon_xml)
				tree.write(addon_xml)
				hash_end = gen_file_hash(addon_xml)
				control.log('[ plugin.video.wutu ]  ReuseLanguageInvokerCheck Service Finished', LOGINFO)
				if hash_start != hash_end:
					current_profile = control.infoLabel('system.profilename')
					control.execute('LoadProfile(%s)' % current_profile)
				else: control.okDialog(title='default', message=33022)
			return
		except:
			log_utils.error()

class AddonCheckUpdate:
	def run(self):
		control.log('[ plugin.video.wutu ]  Addon checking available updates', LOGINFO)
		try:
			import re
			import requests
			repo_xml = requests.get('https://raw.githubusercontent.com/Ezra-Hubbard/Ezra-Hubbard.github.io/master/repo/zips/addons.xml')
			if not repo_xml.status_code == 200:
				return control.log('[ plugin.video.wutu ]  Could not connect to remote repo XML: status code = %s' % repo_xml.status_code, LOGINFO)
			repo_version = re.findall(r'<addon id=\"plugin.video.wutu\".+version=\"(\d*.\d*.\d*)\"', repo_xml.text)[0]
			local_version = control.getwutuVersion()[:5] # 5 char max so pre-releases do try to compare more chars than github version
			def check_version_numbers(current, new): # Compares version numbers and return True if github version is newer
				current = current.split('.')
				new = new.split('.')
				step = 0
				for i in current:
					if int(new[step]) > int(i): return True
					if int(i) > int(new[step]): return False
					if int(i) == int(new[step]):
						step += 1
						continue
				return False
			if check_version_numbers(local_version, repo_version):
				while control.condVisibility('Library.IsScanningVideo'):
					control.sleep(10000)
				control.log('[ plugin.video.wutu ]  A newer version is available. Installed Version: v%s, Repo Version: v%s' % (local_version, repo_version), LOGINFO)
				control.notification(message=control.lang(35523) % repo_version)
			return control.log('[ plugin.video.wutu ]  Addon update check complete', LOGINFO)
		except:
			log_utils.error()

class VersionIsUpdateCheck:
	def run(self):
		try:
			from resources.lib.database import cache
			isUpdate = False
			oldVersion, isUpdate = cache.update_cache_version()
			if isUpdate:
				window.setProperty('wutu.updated', 'true')
				curVersion = control.getwutuVersion()
				clearDB_version = '6.5.6' # set to desired version to force any db clearing needed
				do_cacheClear = (int(oldVersion.replace('.', '')) < int(clearDB_version.replace('.', '')) <= int(curVersion.replace('.', '')))
				if do_cacheClear:
					clr_fanarttv = False
					cache.clrCache_version_update(clr_providers=False, clr_metacache=True, clr_cache=True, clr_search=False, clr_bookmarks=False)
					from resources.lib.database import traktsync
					clr_traktSync = {'bookmarks': False, 'hiddenProgress': False, 'liked_lists': False, 'movies_collection': False, 'movies_watchlist': False, 'popular_lists': False,
											'public_lists': False, 'shows_collection': False, 'shows_watchlist': False, 'trending_lists': False, 'user_lists': False, 'watched': False}
					cleared = traktsync.delete_tables(clr_traktSync)
					if cleared:
						control.notification(message='Forced traktsync clear for version update complete.')
						control.log('[ plugin.video.wutu ]  Forced traktsync clear for version update complete.', LOGINFO)
					if clr_fanarttv:
						from resources.lib.database import fanarttv_cache
						cleared = fanarttv_cache.cache_clear()
						control.notification(message='Forced fanarttv.db clear for version update complete.')
						control.log('[ plugin.video.wutu ]  Forced fanarttv.db clear for version update complete.', LOGINFO)
				control.setSetting('trakt.message2', '') # force a settings write for any added settings that may have been added in new version
				control.log('[ plugin.video.wutu ]  Forced new User Data settings.xml saved', LOGINFO)
				control.log('[ plugin.video.wutu ]  Plugin updated to v%s' % curVersion, LOGINFO)
		except:
			log_utils.error()

class SyncTraktCollection:
	def run(self):
		control.log('[ plugin.video.wutu ]  Trakt Collection Sync Starting...', LOGINFO)
		control.execute('RunPlugin(%s?action=library_tvshowsToLibrarySilent&url=traktcollection)' % plugin)
		control.execute('RunPlugin(%s?action=library_moviesToLibrarySilent&url=traktcollection)' % plugin)
		control.log('[ plugin.video.wutu ]  Trakt Collection Sync Complete', LOGINFO)

class LibraryService:
	def run(self):
		control.log('[ plugin.video.wutu ]  Library Update Service Starting (Update check every 6hrs)...', LOGINFO)
		from resources.lib.modules import library
		library.lib_tools().service() # method contains control.monitor().waitForAbort() while loop every 6hrs

class SyncTraktService:
	def run(self):
		service_syncInterval = control.setting('trakt.service.syncInterval') or '15'
		control.log('[ plugin.video.wutu ]  Trakt Sync Service Starting (sync check every %s minutes)...' % service_syncInterval, LOGINFO)
		from resources.lib.modules import trakt
		trakt.trakt_service_sync() # method contains "control.monitor().waitForAbort()" while loop every "service_syncInterval" minutes

try:
	kodiVersion = control.getKodiVersion(full=True)
	addonVersion = control.addon('plugin.video.wutu').getAddonInfo('version')
	repoVersion = control.addon('repository.ezra').getAddonInfo('version')
	fsVersion = control.addon('script.module.ezscrapers').getAddonInfo('version')
	maVersion = control.addon('script.module.myaccounts').getAddonInfo('version')
	log_utils.log('########   CURRENT wutu VERSIONS REPORT   ########', level=LOGINFO)
	log_utils.log('##   Platform: %s' % str(sys_platform), level=LOGINFO)
	log_utils.log('##   Kodi Version: %s' % str(kodiVersion), level=LOGINFO)
	log_utils.log('##   python Version: %s' % pythonVersion, level=LOGINFO)
	log_utils.log('##   plugin.video.wutu Version: %s' % str(addonVersion), level=LOGINFO)
	log_utils.log('##   repository.ezra Version: %s' % str(repoVersion), level=LOGINFO)
	log_utils.log('##   script.module.ezscrapers Version: %s' % str(fsVersion), level=LOGINFO)
	log_utils.log('##   script.module.myaccounts Version: %s' % str(maVersion), level=LOGINFO)
	log_utils.log('######   wutu SERVICE ENTERING KEEP ALIVE   #####', level=LOGINFO)
except:
	log_utils.log('## ERROR GETTING wutu VERSION - Missing Repo or failed Install ', level=LOGINFO)

def getTraktCredentialsInfo():
	username = control.setting('trakt.username').strip()
	token = control.setting('trakt.token')
	refresh = control.setting('trakt.refresh')
	if (username == '' or token == '' or refresh == ''): return False
	return True

def main():
	while not control.monitor.abortRequested():
		control.log('[ plugin.video.wutu ]  Service Started', LOGINFO)
		schedTrakt = None
		libraryService = None
		CheckSettingsFile().run()
		SyncMyAccounts().run()
		ReuseLanguageInvokerCheck().run()
		if control.setting('library.service.update') == 'true':
			libraryService = Thread(target=LibraryService().run)
			libraryService.start()
		if control.setting('general.checkAddonUpdates') == 'true':
			AddonCheckUpdate().run()
		VersionIsUpdateCheck().run()

		syncTraktService = Thread(target=SyncTraktService().run) # run service in case user auth's trakt later, sync will loop and do nothing without valid auth'd account
		syncTraktService.start()

		if getTraktCredentialsInfo():
			if control.setting('autoTraktOnStart') == 'true':
				SyncTraktCollection().run()
			if int(control.setting('schedTraktTime')) > 0:
				import threading
				log_utils.log('#################### STARTING TRAKT SCHEDULING ################', level=LOGINFO)
				log_utils.log('#################### SCHEDULED TIME FRAME '+ control.setting('schedTraktTime')  + ' HOURS ###############', level=LOGINFO)
				timeout = 3600 * int(control.setting('schedTraktTime'))
				schedTrakt = threading.Timer(timeout, SyncTraktCollection().run) # this only runs once at the designated interval time to wait...not repeating
				schedTrakt.start()
		break
	SettingsMonitor().waitForAbort()
	control.log('[ plugin.video.wutu ]  Settings Monitor Service Stopping...', LOGINFO)
	del syncTraktService # prob does not kill a running thread
	control.log('[ plugin.video.wutu ]  Trakt Sync Service Stopping...', LOGINFO)
	if libraryService:
		del libraryService # prob does not kill a running thread
		control.log('[ plugin.video.wutu ]  Library Update Service Stopping...', LOGINFO)
	if schedTrakt:
		schedTrakt.cancel()
	control.log('[ plugin.video.wutu ]  Service Stopped', LOGINFO)

main()
