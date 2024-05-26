# -*- coding: utf-8 -*-
"""
	WUTU
"""

from json import dumps as jsdumps
from urllib.parse import quote_plus
from resources.lib.modules.control import joinPath, transPath, dialog, getSourceHighlightColor, notification, setting as getSetting
from resources.lib.modules.source_utils import getFileType
from resources.lib.modules import tools
from resources.lib.windows.base import BaseDialog


class SourceResultsXML(BaseDialog):
	def __init__(self, *args, **kwargs):
		BaseDialog.__init__(self, args)
		self.window_id = 2000
		self.results = kwargs.get('results')
		self.uncached = kwargs.get('uncached')
		self.total_results = str(len(self.results))
		self.meta = kwargs.get('meta')
		self.make_items()
		self.set_properties()
		self.dnlds_enabled = True if getSetting('downloads') == 'true' and (getSetting('movie.download.path') != '' or getSetting('tv.download.path') != '') else False

	def onInit(self):
		win = self.getControl(self.window_id)
		win.addItems(self.item_list)
		self.setFocusId(self.window_id)

	def run(self):
		self.doModal()
		self.clearProperties()
		return self.selected

	def onAction(self, action):
		try:
			action_id = action.getId() # change to just "action" as the ID is already returned in that.
			if action_id in self.info_actions:
				chosen_source = self.item_list[self.get_position(self.window_id)]
				chosen_source = chosen_source.getProperty('wutu.source_dict')
				syssource = quote_plus(chosen_source)
				self.execute_code('RunPlugin(plugin://plugin.video.wutu/?action=sourceInfo&source=%s)' % syssource)
			if action_id in self.selection_actions:
				focus_id = self.getFocusId()
				if focus_id == 2001:
					position = self.get_position(self.window_id)
					self.load_uncachedTorrents()
					self.setFocusId(self.window_id)
					self.getControl(self.window_id).selectItem(position)
					self.selected = (None, '')
					return
				chosen_source = self.item_list[self.get_position(self.window_id)]
				source = chosen_source.getProperty('wutu.source')
				if 'UNCACHED' in source:
					debrid = chosen_source.getProperty('wutu.debrid')
					source_dict = chosen_source.getProperty('wutu.source_dict')
					link_type = 'pack' if 'package' in source_dict else 'single'
					sysname = quote_plus(self.meta.get('title'))
					if 'tvshowtitle' in self.meta and 'season' in self.meta and 'episode' in self.meta:
						poster = self.meta.get('season_poster') or self.meta.get('poster')
						sysname += quote_plus(' S%02dE%02d' % (int(self.meta['season']), int(self.meta['episode'])))
					elif 'year' in self.meta: sysname += quote_plus(' (%s)' % self.meta['year'])
					try: new_sysname = quote_plus(chosen_source.getProperty('wutu.name'))
					except: new_sysname = sysname
					self.execute_code('RunPlugin(plugin://plugin.video.wutu/?action=cacheTorrent&caller=%s&type=%s&title=%s&items=%s&url=%s&source=%s&meta=%s)' %
											(debrid, link_type, sysname, quote_plus(jsdumps(self.results)), quote_plus(chosen_source.getProperty('wutu.url')), quote_plus(source_dict), quote_plus(jsdumps(self.meta))))
					self.selected = (None, '')
				else:
					self.selected = ('play_Item', chosen_source)
				return self.close()
			elif action_id in self.context_actions:
				from re import match as re_match
				chosen_source = self.item_list[self.get_position(self.window_id)]
				source_dict = chosen_source.getProperty('wutu.source_dict')
				cm_list = [('[B]Additional Link Info[/B]', 'sourceInfo')]
				if 'cached (pack)' in source_dict:
					cm_list += [('[B]Browse Debrid Pack[/B]', 'showDebridPack')]
				source = chosen_source.getProperty('wutu.source')
				if not 'UNCACHED' in source and self.dnlds_enabled:
					cm_list += [('[B]Download[/B]', 'download')]
				if re_match(r'^CACHED.*TORRENT', source):
					debrid = chosen_source.getProperty('wutu.debrid')
					cm_list += [('[B]Save to %s Cloud[/B]' % debrid, 'saveToCloud')]
				chosen_cm_item = dialog.contextmenu([i[0] for i in cm_list])
				if chosen_cm_item == -1: return
				cm_action = cm_list[chosen_cm_item][1]
				if cm_action == 'sourceInfo':
					self.execute_code('RunPlugin(plugin://plugin.video.wutu/?action=sourceInfo&source=%s)' % quote_plus(source_dict))
				elif cm_action == 'showDebridPack':
					debrid = chosen_source.getProperty('wutu.debrid')
					name = chosen_source.getProperty('wutu.name')
					hash = chosen_source.getProperty('wutu.hash')
					self.execute_code('RunPlugin(plugin://plugin.video.wutu/?action=showDebridPack&caller=%s&name=%s&url=%s&source=%s)' %
									(quote_plus(debrid), quote_plus(name), quote_plus(chosen_source.getProperty('wutu.url')), quote_plus(hash)))
					self.selected = (None, '')
				elif cm_action == 'download':
					sysname = quote_plus(self.meta.get('title'))
					poster = self.meta.get('poster', '')
					if 'tvshowtitle' in self.meta and 'season' in self.meta and 'episode' in self.meta:
						sysname = quote_plus(self.meta.get('tvshowtitle'))
						poster = self.meta.get('season_poster') or self.meta.get('poster')
						sysname += quote_plus(' S%02dE%02d' % (int(self.meta['season']), int(self.meta['episode'])))
					elif 'year' in self.meta: sysname += quote_plus(' (%s)' % self.meta['year'])
					try: new_sysname = quote_plus(chosen_source.getProperty('wutu.name'))
					except: new_sysname = sysname
					self.execute_code('RunPlugin(plugin://plugin.video.wutu/?action=download&name=%s&image=%s&source=%s&caller=sources&title=%s)' %
										(new_sysname, quote_plus(poster), quote_plus(source_dict), sysname))
					self.selected = (None, '')
				elif cm_action == 'saveToCloud':
					magnet = chosen_source.getProperty('wutu.url')
					if debrid == 'AD':
						from resources.lib.debrid import alldebrid
						transfer_function = alldebrid.AllDebrid
						debrid_icon = alldebrid.ad_icon
					elif debrid == 'PM':
						from resources.lib.debrid import premiumize
						transfer_function = premiumize.Premiumize
						debrid_icon = premiumize.pm_icon
					elif debrid == 'RD':
						from resources.lib.debrid import realdebrid
						transfer_function = realdebrid.RealDebrid
						debrid_icon = realdebrid.rd_icon
					result = transfer_function().create_transfer(magnet)
					if result: notification(message='Sending MAGNET to the %s cloud' % debrid, icon=debrid_icon)
			elif action in self.closing_actions:
				self.selected = (None, '')
				self.close()
		except:
			from resources.lib.modules import log_utils
			log_utils.error()

	def get_quality_iconPath(self, quality):
		try:
			return joinPath(transPath('special://home/addons/plugin.video.wutu/resources/skins/Default/media/resolution'), '%s.png' % quality)
		except:
			from resources.lib.modules import log_utils
			log_utils.error()

	def debrid_abv(self, debrid):
		try:
			d_dict = {'AllDebrid': 'AD', 'Premiumize.me': 'PM', 'Real-Debrid': 'RD'}
			d = d_dict[debrid]
		except:
			d = ''
		return d

	def make_items(self):
		def builder():
			for count, item in enumerate(self.results, 1):
				try:
					listitem = self.make_listitem()
					quality = item.get('quality', 'SD')
					quality_icon = self.get_quality_iconPath(quality)
					extra_info = item.get('info')
					size_label = str(round(item.get('size', ''), 2)) + ' GB' if item.get('size') else 'NA'
					listitem.setProperty('wutu.source_dict', jsdumps([item]))
					listitem.setProperty('wutu.debrid', self.debrid_abv(item.get('debrid')))
					listitem.setProperty('wutu.provider', item.get('provider').upper())
					listitem.setProperty('wutu.source', item.get('source').upper())
					listitem.setProperty('wutu.seeders', str(item.get('seeders')))
					listitem.setProperty('wutu.hash', item.get('hash', 'N/A'))
					listitem.setProperty('wutu.name', item.get('name'))
					listitem.setProperty('wutu.quality', quality.upper())
					listitem.setProperty('wutu.quality_icon', quality_icon)
					listitem.setProperty('wutu.url', item.get('url'))
					listitem.setProperty('wutu.extra_info', extra_info)
					listitem.setProperty('wutu.size_label', size_label)
					listitem.setProperty('wutu.count', '%02d.)' % count)
					yield listitem
				except:
					from resources.lib.modules import log_utils
					log_utils.error()
		try:
			self.item_list = list(builder())
			self.total_results = str(len(self.item_list))
		except:
			from resources.lib.modules import log_utils
			log_utils.error()

	def set_properties(self):
		if self.meta is None: return
		try:
			self.setProperty('wutu.season', str(self.meta.get('season', '')))
			if 'tvshowtitle' in self.meta and 'season' in self.meta and 'episode' in self.meta: self.setProperty('wutu.seas_ep', 'S%02dE%02d' % (int(self.meta['season']), int(self.meta['episode'])))
			if self.meta.get('season_poster'):	self.setProperty('wutu.poster', self.meta.get('season_poster', ''))
			else: self.setProperty('wutu.poster', self.meta.get('poster', ''))
			self.setProperty('wutu.clearlogo', self.meta.get('clearlogo', ''))
			self.setProperty('wutu.plot', self.meta.get('plot', ''))
			self.setProperty('wutu.year', str(self.meta.get('year', '')))
			new_date = tools.convert_time(stringTime=str(self.meta.get('premiered', '')), formatInput='%Y-%m-%d', formatOutput='%m-%d-%Y', zoneFrom='utc', zoneTo='utc')
			self.setProperty('wutu.premiered', new_date)
			if self.meta.get('mpaa'): self.setProperty('wutu.mpaa', self.meta.get('mpaa'))
			else: self.setProperty('wutu.mpaa', 'NA ')
			if self.meta.get('duration'):
				duration = int(self.meta.get('duration')) / 60
				self.setProperty('wutu.duration', str(int(duration)))
			else: self.setProperty('wutu.duration', 'NA ')
			self.setProperty('wutu.total_results', self.total_results)
			self.setProperty('wutu.highlight.color', getSourceHighlightColor())
		except:
			from resources.lib.modules import log_utils
			log_utils.error()

	def load_uncachedTorrents(self):
		try:
			from resources.lib.windows.uncached_results import UncachedResultsXML
			from resources.lib.modules.control import addonPath, addonId
			window = UncachedResultsXML('uncached_results.xml', addonPath(addonId()), uncached=self.uncached, meta=self.meta)
			window.run()
		except:
			from resources.lib.modules import log_utils
			log_utils.error()