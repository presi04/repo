﻿#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
import re
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3
if PY2:
	from urllib import quote, unquote, quote_plus, unquote_plus, urlencode  # Python 2.X
elif PY3:
	from urllib.parse import quote, unquote, quote_plus, unquote_plus, urlencode  # Python 3+
import json
import xbmcvfs
import shutil
import socket
import time
from datetime import datetime, timedelta
import requests
try:
	from requests.packages.urllib3.exceptions import InsecureRequestWarning
	requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
except: pass


global debuging
SEP = os.sep
pluginhandle = int(sys.argv[1])
addon = xbmcaddon.Addon()
addonPath = xbmc.translatePath(addon.getAddonInfo('path')).encode('utf-8').decode('utf-8')
dataPath = xbmc.translatePath(addon.getAddonInfo('profile')).encode('utf-8').decode('utf-8')
masterOLD  = 'my_TLC_favourites.txt'
masterNEW = 'my_TLC_favourites.txt'
masterBACK = '(BACKUP)my_TLC_favourites.txt'
sourceOLD = os.path.join('special:'+SEP+SEP+'home'+SEP+'userdata'+SEP+'addon_data'+SEP+'plugin.video.L0RE.tlc'+SEP, masterOLD)
sourceNEW = os.path.join('special:'+SEP+SEP+'home'+SEP+'userdata'+SEP+'addon_data'+SEP+'plugin.video.tyl0re.tlc'+SEP, masterNEW)
sourceBACK = os.path.join('special:'+SEP+SEP+'home'+SEP+'userdata'+SEP+'addon_data'+SEP+'plugin.video.L0RE.tlc'+SEP, masterBACK)
channelFavsFile = os.path.join(dataPath, 'my_TLC_favourites.txt').encode('utf-8').decode('utf-8')
defaultFanart = os.path.join(addonPath, 'fanart.jpg')
icon = os.path.join(addonPath, 'icon.png')
artpic = os.path.join(addonPath, 'resources', 'media', '').encode('utf-8').decode('utf-8')
useThumbAsFanart = addon.getSetting('useThumbAsFanart') == 'true'
enableAdjustment = addon.getSetting('show_settings') == 'true'
enableInputstream = addon.getSetting('inputstream') == 'true'
DEB_LEVEL = (xbmc.LOGNOTICE if addon.getSetting('enableDebug') == 'true' else xbmc.LOGDEBUG)
baseURL = 'https://www.tlc.de/'

__HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:60.0) Gecko/20100101 Firefox/60.0', 'Accept-Encoding': 'gzip, deflate'}
xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')

if xbmcvfs.exists(sourceOLD):
	if not xbmcvfs.exists(dataPath) and not os.path.isdir(dataPath):
		xbmcvfs.mkdirs(dataPath)
		xbmc.sleep(500)
	if xbmcvfs.exists(sourceOLD) and not xbmcvfs.exists(sourceNEW):
		xbmcvfs.copy(sourceOLD, sourceNEW)
		xbmcvfs.rename(sourceOLD, sourceBACK)

def py2_enc(s, encoding='utf-8'):
	if PY2:
		if not isinstance(s, basestring):
			s = str(s)
		s = s.encode(encoding) if isinstance(s, unicode) else s
	return s

def py2_uni(s, encoding='utf-8'):
	if PY2 and isinstance(s, str):
		s = unicode(s, encoding)
	return s

def py3_dec(d, encoding='utf-8'):
	if PY3 and isinstance(d, bytes):
		d = d.decode(encoding)
	return d

def translation(id):
	return py2_enc(addon.getLocalizedString(id))

def failing(content):
	log(content, xbmc.LOGERROR)

def debug_MS(content):
	log(content, DEB_LEVEL)

def log(msg, level=xbmc.LOGNOTICE):
	xbmc.log('[{0} v.{1}]{2}'.format(addon.getAddonInfo('id'), addon.getAddonInfo('version'), py2_enc(msg)), level)

def getUrl(url, method, allow_redirects=False, verify=False, stream=False, headers="", data="", timeout=40):
	response = requests.Session()
	access_token = '00'
	if method == 'GET':
		content = response.get(url, allow_redirects=allow_redirects, verify=verify, stream=stream, headers=headers, data=data, timeout=timeout).text
	elif method == 'POST':
		content = response.post(url, data=data, allow_redirects=allow_redirects, verify=verify).text
	if 'sonicToken' in response.cookies and response.cookies['sonicToken']:
		access_token = response.cookies['sonicToken']
	content = py2_enc(content)
	return content, access_token

def ADDON_operate(TESTING):
	js_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Addons.GetAddonDetails", "params": {"addonid":"'+TESTING+'", "properties": ["enabled"]}, "id":1}')
	if '"enabled":false' in js_query:
		try:
			xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Addons.SetAddonEnabled", "params": {"addonid":"'+TESTING+'", "enabled":true}, "id":1}')
			failing("(ADDON_operate) ERROR - ERROR - ERROR :\n##### Das benötigte Addon : *{0}* ist NICHT aktiviert !!! #####\n##### Es wird jetzt versucht die Aktivierung durchzuführen !!! #####".format(TESTING))
		except: pass
	if '"error":' in js_query:
		xbmcgui.Dialog().ok(addon.getAddonInfo('id'), translation(30501).format(TESTING))
		failing("(ADDON_operate) ERROR - ERROR - ERROR :\n##### Das benötigte Addon : *{0}* ist NICHT installiert !!! #####".format(TESTING))
		return False
	if '"enabled":true' in js_query:
		return True

def index():
	addDir(translation(30601), "", 'listShowsFavs', icon)
	addDir(translation(30602), baseURL+'api/search?query=*&limit=50', 'listSeries', icon, nosub='overview_all')
	addDir(translation(30603), "", 'listThemes', icon)
	addDir(translation(30604), baseURL+'api/shows/highlights?limit=50', 'listSeries', icon, nosub='featured')
	addDir(translation(30605), baseURL+'api/shows/neu?limit=50', 'listSeries', icon, nosub='recently_added')
	addDir(translation(30606), baseURL+'api/shows/beliebt?limit=50', 'listSeries', icon, nosub='most_popular')
	if enableAdjustment:
		addDir(translation(30607), "", 'aSettings', icon)
		if enableInputstream:
			if ADDON_operate('inputstream.adaptive'):
				addDir(translation(30608), "", 'iSettings', icon)
			else:
				addon.setSetting('inputstream', 'false')
	xbmcplugin.endOfDirectory(pluginhandle)

def listThemes():
	debug_MS("(listThemes) ------------------------------------------------ START = listThemes -----------------------------------------------")
	xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_SORT_TITLE)
	content, access_token = getUrl(baseURL+'themen', 'GET', False, False, False, __HEADERS)
	response = content[content.find('href="/themen">Themen</a><div class="header__nav__dd-wrapper">')+1:]
	response = response[:response.find('</ul></div>')]
	result = re.compile('<a href="(.*?)">(.*?)</a>').findall(response)
	for link, name in result:
		url = baseURL+'api/genres/'+link.split('/')[-1]+'?limit=100'
		name = py2_enc(name).replace('&amp;', '&').strip()
		debug_MS("(listThemes) ### NAME : {0} || LINK : {1} || URL : {2} ###".format(str(name), str(link), str(url)))
		if 'themen' in link:
			addDir(name, url, 'listSeries', icon, nosub='overview_themes')
	xbmcplugin.endOfDirectory(pluginhandle)

def listSeries(url, PAGE, POS, ADDITION):
	debug_MS("(listSeries) ------------------------------------------------ START = listSeries -----------------------------------------------")
	debug_MS("(listSeries) ### URL : {0} ### PAGE : {1} ### POS : {2} ### ADDITION : {3} ###".format(str(url), str(PAGE), str(POS), str(ADDITION)))
	count = int(POS)
	readyURL = url+'&page='+str(PAGE)
	content, access_token = getUrl(readyURL, 'GET', False, False, False, __HEADERS)
	debug_MS("++++++++++++++++++++++++")
	debug_MS("(listSeries) XXXXX CONTENT : {0} XXXXX".format(str(content)))
	debug_MS("++++++++++++++++++++++++")
	DATA = json.loads(content)
	if 'search?query' in url:
		elements = DATA['shows']
	else:
		elements = DATA['items']
	for elem in elements:
		debug_MS("(listSeries) ##### ELEMENT : {0} #####".format(str(elem)))
		title = py2_enc(elem['title']).strip()
		name = title
		idd = ""
		if 'id' in elem and elem['id'] != "" and elem['id'] != None:
			idd = elem['id']
		plot = ""
		if 'description' in elem and elem['description'] != "" and elem['description'] != None:
			plot = py2_enc(elem['description']).replace('\n\n\n', '\n\n').strip()
		image = ""
		if 'image' in elem and 'src' in elem['image'] and elem['image']['src'] != "" and elem['image']['src'] != None:
			image = elem['image']['src']
		debug_MS("(listSeries) noFilter ### NAME : {0} || IDD : {1} || IMAGE : {2} ###".format(str(name), str(idd), str(image)))
		if idd !="" and len(idd) < 9 and plot != "" and image != "":
			count += 1
			if 'beliebt' in url:
				name = '[COLOR chartreuse]'+str(count)+' •  [/COLOR]'+title
			try: 
				if elem['hasNewEpisodes']: name = name+translation(30609)
			except: pass
			debug_MS("(listSeries) Filtered --- NAME : {0} || IDD : {1} || IMAGE : {2} ---".format(str(name), str(idd), str(image)))
			addType=1
			if os.path.exists(channelFavsFile):
				with open(channelFavsFile, 'r') as output:
					lines = output.readlines()
					for line in lines:
						if line.startswith('###START'):
							part = line.split('###')
							idd_FS = part[2]
							if idd == idd_FS: addType=2
			addDir(name, idd, 'listEpisodes', image, plot, nosub=ADDITION, origSERIE=title, addType=addType)
	currentRESULT = count
	debug_MS("(listSeries) NUMBERING ### currentRESULT : {0} ###".format(str(currentRESULT)))
	try:
		currentPG = DATA['meta']['currentPage']
		totalPG = DATA['meta']['totalPages']
		debug_MS("(listSeries) PAGES ### currentPG : {0} from totalPG : {1} ###".format(str(currentPG), str(totalPG)))
		if int(currentPG) < int(totalPG):
			addDir(translation(30610), url, 'listSeries', artpic+'nextpage.png', page=int(currentPG)+1, position=int(currentRESULT), nosub=ADDITION)
	except: pass
	xbmcplugin.endOfDirectory(pluginhandle)

def listEpisodes(idd, origSERIE):
	debug_MS("(listEpisodes) ------------------------------------------------ START = listEpisodes -----------------------------------------------")
	COMBI = []
	SELECT = []
	pos1 = 0
	url = baseURL+'api/show-detail/'+str(idd)
	debug_MS("(listEpisodes) ### URL : {0} ### origSERIE : {1} ###".format(str(url), str(origSERIE)))
	try:
		content, access_token = getUrl(url, 'GET', False, False, False, __HEADERS)
		debug_MS("++++++++++++++++++++++++")
		debug_MS("(listEpisodes) XXXXX CONTENT : {0} XXXXX".format(str(content)))
		debug_MS("++++++++++++++++++++++++")
		DATA = json.loads(content)
	except: return xbmcgui.Dialog().notification(translation(30521).format(str(idd)), translation(30522), icon, 12000)
	genstr = ""
	genreList=[]
	if 'show' in DATA and 'genres' in DATA['show'] and DATA['show']['genres'] != "" and DATA['show']['genres'] != None:
		for item in DATA['show']['genres']:
			gNames = py2_enc(item['name'])
			genreList.append(gNames)
		genstr =' / '.join(genreList)
	if 'episode' in DATA['videos'] or 'standalone' in DATA['videos']:
		if 'episode' in DATA['videos']:
			subelement = DATA['videos']['episode']
			if PY2: makeITEMS = subelement.iteritems # for (key, value) in subelement.iteritems():  # Python 2x
			elif PY3: makeITEMS = subelement.items # for (key, value) in subelement.items():  # Python 3+
			for number,videos in makeITEMS():
				for vid in videos:
					if 'isPlayable' in vid and vid['isPlayable'] == True:
						debug_MS("(listEpisodes) ##### subelement-1-vid : {0} #####".format(str(vid)))
						season = ""
						if 'season' in vid and vid['season'] != "" and str(vid['season']) != "0" and vid['season'] != None:
							season = str(vid['season']).zfill(2)
						episode = ""
						if 'episode' in vid and vid['episode'] != "" and str(vid['episode']) != "0" and vid['episode'] != None:
							episode = str(vid['episode']).zfill(2)
						title = py2_enc(vid['name']).strip()
						if season != "" and episode != "":
							title1 = '[COLOR chartreuse]S'+season+'E'+episode+':[/COLOR]'
							title2 = title
							number = 'S'+season+'E'+episode
						else:
							title1 = title
							title2 = ""
							number = ""
						begins = None
						year = None
						startTIMES = None
						endTIMES = None
						Note_1 = ""
						Note_2 = ""
						Note_3 = ""
						if 'publishStart' in vid and vid['publishStart'] != "" and vid['publishStart'] != None and not str(vid['publishStart']).startswith('1970'):
							try:
								startDATES = datetime(*(time.strptime(vid['publishStart'][:19], '%Y{0}%m{0}%dT%H{1}%M{1}%S'.format('-', ':'))[0:6])) # 2019-06-23T14:10:00Z
								LOCALstart = utc_to_local(startDATES)
								startTIMES = LOCALstart.strftime('%d{0}%m{0}%y {1} %H{2}%M').format('.', '•', ':')
								begins =  LOCALstart.strftime('%d{0}%m{0}%Y').format('.')
							except: pass
						if 'publishEnd' in vid and vid['publishEnd'] != "" and vid['publishEnd'] != None and not str(vid['publishEnd']).startswith('1970'):
							try:
								endDATES = datetime(*(time.strptime(vid['publishEnd'][:19], '%Y{0}%m{0}%dT%H{1}%M{1}%S'.format('-', ':'))[0:6])) # 2019-06-23T14:10:00Z
								LOCALend = utc_to_local(endDATES)
								endTIMES = LOCALend.strftime('%d{0}%m{0}%y {1} %H{2}%M').format('.', '•', ':')
							except: pass
						if 'airDate' in vid and vid['airDate'] != "" and vid['airDate'] != None and not str(vid['airDate']).startswith('1970'):
							year = vid['airDate'][:4]
						if startTIMES: Note_1 = translation(30611).format(str(startTIMES))
						if endTIMES: Note_2 = translation(30612).format(str(endTIMES))
						if 'description' in vid and vid['description'] != "" and vid['description'] != None:
							Note_3 = py2_enc(vid['description']).replace('\n\n\n', '\n\n').strip()
						plot = Note_1+Note_2+Note_3
						image = ""
						if 'image' in vid and 'src' in vid['image'] and vid['image']['src'] != "" and vid['image']['src'] != None:
							image = vid['image']['src']
						idd2 = ""
						if 'id' in vid and vid['id'] != "" and vid['id'] != None:
							idd2 = str(vid['id'])
						else: continue
						duration = int(vid['videoDuration']/1000)
						COMBI.append([number, title1, title2, idd2, image, plot, duration, season, episode, genstr, year, begins])
		if 'standalone' in DATA['videos']:
			subelement = DATA['videos']['standalone']
			for item in subelement:
				if 'isPlayable' in item and item['isPlayable'] == True:
					debug_MS("(listEpisodes) ##### subelement-2-item : {0} #####".format(str(item)))
					season = "00"
					if 'season' in item and item['season'] != "" and str(item['season']) != "0" and item['season'] != None:
						season = str(item['season']).zfill(2)
					episode = ""
					if 'episode' in item and item['episode'] != "" and str(item['episode']) != "0" and item['episode'] != None:
						episode = str(item['episode']).zfill(2)
					title = py2_enc(item['name']).strip()
					begins = None
					year = None
					airdate = None
					startTIMES = None
					endTIMES = None
					Note_1 = ""
					Note_2 = ""
					Note_3 = ""
					if 'publishStart' in item and item['publishStart'] != "" and item['publishStart'] != None and not str(item['publishStart']).startswith('1970'):
						try:
							startDATES = datetime(*(time.strptime(item['publishStart'][:19], '%Y{0}%m{0}%dT%H{1}%M{1}%S'.format('-', ':'))[0:6])) # 2019-06-23T14:10:00Z
							LOCALstart = utc_to_local(startDATES)
							startTIMES = LOCALstart.strftime('%d{0}%m{0}%y {1} %H{2}%M').format('.', '•', ':')
							begins =  LOCALstart.strftime('%d{0}%m{0}%Y').format('.')
						except: pass
					if 'publishEnd' in item and item['publishEnd'] != "" and item['publishEnd'] != None and not str(item['publishEnd']).startswith('1970'):
						try:
							endDATES = datetime(*(time.strptime(item['publishEnd'][:19], '%Y{0}%m{0}%dT%H{1}%M{1}%S'.format('-', ':'))[0:6])) # 2019-06-23T14:10:00Z
							LOCALend = utc_to_local(endDATES)
							endTIMES = LOCALend.strftime('%d{0}%m{0}%y {1} %H{2}%M').format('.', '•', ':')
						except: pass
					if 'airDate' in item and item['airDate'] != "" and item['airDate'] != None and not str(item['airDate']).startswith('1970'):
						year = item['airDate'][:4]
						airdate = item['airDate'][:10]
					if startTIMES: Note_1 = translation(30611).format(str(startTIMES))
					if endTIMES: Note_2 = translation(30612).format(str(endTIMES))
					if 'description' in item and item['description'] != "" and item['description'] != None:
						Note_3 = py2_enc(item['description']).replace('\n\n\n', '\n\n').strip()
					plot = Note_1+Note_2+Note_3
					image = ""
					if 'image' in item and 'src' in item['image'] and item['image']['src'] != "" and item['image']['src'] != None:
						image = item['image']['src']
					idd2 = ""
					if 'id' in item and item['id'] != "" and item['id'] != None:
						idd2 = str(item['id'])
					else: continue
					duration = int(item['videoDuration']/1000)
					SELECT.append([title, idd2, image, plot, duration, season, episode, genstr, year, airdate, begins])
			if SELECT:
				for title, idd2, image, plot, duration, season, episode, genstr, year, airdate, begins in sorted(SELECT, key=lambda ad:ad[9], reverse=False):
					pos1 += 1
					if season != "00" and episode != "":
						title1 = '[COLOR orangered]S'+season+'E'+episode+':[/COLOR]'
						title2 = title
						number = 'S'+season+'E'+episode
					else:
						episode = str(pos1).zfill(2)
						title1 = '[COLOR orangered]S00E'+episode+':[/COLOR]'
						title2 = title+'  (Special)'
						number = 'S00E'+episode
					COMBI.append([number, title1, title2, idd2, image, plot, duration, season, episode, genstr, year, begins])
	else:
		debug_MS("(listEpisodes) ##### Keine COMBINATION-List - Kein Eintrag gefunden #####")
		return xbmcgui.Dialog().notification(translation(30523), translation(30524).format(origSERIE), icon, 8000)
	if COMBI:
		if addon.getSetting('sorting') == "1":
			xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)
			xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL)
			xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DURATION)
		else:
			COMBI = sorted(COMBI, key=lambda b:b[0], reverse=True)
		for number, title1, title2, idd2, image, plot, duration, season, episode, genstr, year, begins in COMBI:
			if addon.getSetting('sorting') == "1" and begins:
				xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DATE)
			name = title1.strip()+"  "+title2.strip()
			if title2 == "":
				name = title1.strip()
			debug_MS("(listEpisodes) ##### NAME : {0} || IDD : {1} || GENRE : {2} #####".format(str(name), idd2, str(genstr)))
			debug_MS("(listEpisodes) ##### IMAGE : {0} || SEASON : {1} || EPISODE : {2} #####".format(str(image), str(season), str(episode)))
			addLink(name, idd2, 'playVideo', image, plot, duration, origSERIE=origSERIE, season=season, episode=episode, genre=genstr, year=year, begins=begins)
	xbmcplugin.endOfDirectory(pluginhandle)

def playVideo(idd2):
	debug_MS("(playVideo) ------------------------------------------------ START = playVideo -----------------------------------------------")
	content, access_token = getUrl(baseURL, 'GET', False, False, False, __HEADERS)
	debug_MS("(playVideo) ##### COOKIE : {0} #####".format(str(access_token)))
	playURL = 'https://sonic-eu1-prod.disco-api.com/playback/videoPlaybackInfo/'+str(idd2)
	__access_header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:60.0) Gecko/20100101 Firefox/60.0', 'Content-Type': 'application/json', 'Authorization': 'Bearer {}'.format(access_token)}
	result, access_token = getUrl(playURL, 'GET', True, False, False, __access_header)
	debug_MS("++++++++++++++++++++++++")
	debug_MS("(playVideo) XXXXX RESULT : {0} XXXXX".format(str(result)))
	debug_MS("++++++++++++++++++++++++")
	DATA = json.loads(result)
	videoURL = DATA['data']['attributes']['streaming']['hls']['url']
	log("(playVideo) StreamURL : "+videoURL)
	listitem = xbmcgui.ListItem(path=videoURL)
	if enableInputstream:
		if ADDON_operate('inputstream.adaptive'):
			licfile = DATA['data']['attributes']['protection']['schemes']['clearkey']['licenseUrl']
			licurl, access_token = getUrl(licfile, 'GET', True, False, False, __access_header)
			lickey = json.loads(licurl)['keys'][0]['kid']
			debug_MS("(playVideo) ##### LIC-FILE : {0} || LIC-KEY : {1} #####".format(str(licfile), str(lickey)))
			listitem.setProperty('inputstreamaddon', 'inputstream.adaptive')
			listitem.setProperty('inputstream.adaptive.manifest_type', 'hls')
			listitem.setProperty('inputstream.adaptive.license_key', lickey)
		else:
			addon.setSetting('inputstream', 'false')
	xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)

def listShowsFavs():
	debug_MS("(listShowsFavs) ------------------------------------------------ START = listShowsFavs -----------------------------------------------")
	xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_SORT_TITLE)
	if os.path.exists(channelFavsFile):
		with open(channelFavsFile, 'r') as textobj:
			lines = textobj.readlines()
			for line in lines:
				if line.startswith('###START'):
					part = line.split('###')
					debug_MS("(listShowsFavs) ##### NAME : {0} || URL : {1} #####".format(str(part[3]), str(part[2])))
					addDir(name=part[3], url=part[2], mode="listEpisodes", image=part[4].strip(), plot=part[5].replace('#n#', '\n').strip(), origSERIE=part[3], FAVdel=True)
	xbmcplugin.endOfDirectory(pluginhandle)

def favs(param):
	mode = param[param.find('MODE=')+5:+8]
	TVSe = param[param.find('###START'):]
	TVSe = TVSe[:TVSe.find('END###')]
	url = TVSe.split('###')[2]
	name = TVSe.split('###')[3]
	if mode == 'ADD':
		if os.path.exists(channelFavsFile):
			with open(channelFavsFile, 'a+') as textobj:
				content = textobj.read()
				if content.find(TVSe) == -1:
					textobj.seek(0,2) # change is here (for Windows-Error = "IOError: [Errno 0] Error") - because Windows don't like switching between reading and writing at same time !!!
					textobj.write(TVSe+'END###\n')
		else:
			with open(channelFavsFile, 'a') as textobj:
				textobj.write(TVSe+'END###\n')
		xbmc.sleep(500)
		xbmcgui.Dialog().notification(translation(30525), translation(30526).format(name), icon, 8000)
	elif mode == 'DEL':
		with open(channelFavsFile, 'r') as output:
			lines = output.readlines()
		with open(channelFavsFile, 'w') as input:
			for line in lines:
				if url not in line:
					input.write(line)
		xbmc.executebuiltin('Container.Refresh')
		xbmc.sleep(1000)
		xbmcgui.Dialog().notification(translation(30525), translation(30527).format(name), icon, 8000)

def utc_to_local(dt):
	if time.localtime().tm_isdst: return dt - timedelta(seconds=time.altzone)
	else: return dt - timedelta(seconds=time.timezone)

def addQueue(vid):
	PL = xbmc.PlayList(1)
	STREAMe = vid[vid.find('###START'):]
	STREAMe = STREAMe[:STREAMe.find('END###')]
	url = STREAMe.split('###')[2]
	name = STREAMe.split('###')[3]
	image = STREAMe.split('###')[4]
	listitem = xbmcgui.ListItem(name)
	listitem.setArt({'icon': icon, 'thumb': image, 'poster': image, 'fanart': defaultFanart})
	listitem.setProperty('IsPlayable', 'true')
	PL.add(url, listitem)

def parameters_string_to_dict(parameters):
	paramDict = {}
	if parameters:
		paramPairs = parameters[1:].split('&')
		for paramsPair in paramPairs:
			paramSplits = paramsPair.split('=')
			if (len(paramSplits)) == 2:
				paramDict[paramSplits[0]] = paramSplits[1]
	return paramDict

def addDir(name, url, mode, image, plot=None, page=1, position=0, nosub=0, origSERIE="", addType=0, FAVdel=False):
	u = '{0}?url={1}&mode={2}&page={3}&position={4}&nosub={5}&origSERIE={6}'.format(sys.argv[0], quote_plus(url), str(mode), str(page), str(position), str(nosub), quote_plus(origSERIE))
	liz = xbmcgui.ListItem(name)
	liz.setInfo(type='Video', infoLabels={'Title': name, 'Plot': plot})
	liz.setArt({'icon': icon, 'thumb': image, 'poster': image, 'fanart': defaultFanart})
	if useThumbAsFanart and image != icon:
		liz.setArt({'fanart': image})
	entries = []
	if addType == 1 and FAVdel == False:
		FAVInfos_1 = 'MODE=ADD###START###{0}###{1}###{2}###{3}###END###'.format(url, origSERIE, image, plot.replace('\n', '#n#'))
		entries.append([translation(30651), 'RunPlugin('+sys.argv[0]+'?mode=favs&url='+quote_plus(FAVInfos_1)+')'])
	if FAVdel == True:
		FAVInfos_2 = 'MODE=DEL###START###{0}###{1}###{2}###{3}###END###'.format(url, name, image, plot)
		entries.append([translation(30652), 'RunPlugin('+sys.argv[0]+'?mode=favs&url='+quote_plus(FAVInfos_2)+')'])
	liz.addContextMenuItems(entries, replaceItems=False)
	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)

def addLink(name, url, mode, image, plot=None, duration=None, origSERIE=None, season=None, episode=None, genre=None, year=None, begins=None):
	u = '{0}?url={1}&mode={2}'.format(sys.argv[0], quote_plus(url), str(mode))
	liz = xbmcgui.ListItem(name)
	ilabels = {}
	ilabels['Season'] = season
	ilabels['Episode'] = episode
	ilabels['Tvshowtitle'] = origSERIE
	ilabels['Title'] = name
	ilabels['Tagline'] = None
	ilabels['Plot'] = plot
	ilabels['Duration'] = duration
	if begins != None:
		ilabels['Date'] = begins
	ilabels['Year'] = year
	ilabels['Genre'] = genre
	ilabels['Director'] = None
	ilabels['Writer'] = None
	ilabels['Studio'] = 'TLC'
	ilabels['Mpaa'] = None
	ilabels['Mediatype'] = 'episode'
	liz.setInfo(type='Video', infoLabels=ilabels)
	liz.setArt({'icon': icon, 'thumb': image, 'poster': image, 'fanart': defaultFanart})
	if useThumbAsFanart and image != icon:
		liz.setArt({'fanart': image})
	liz.addStreamInfo('Video', {'Duration': duration})
	liz.setProperty('IsPlayable', 'true')
	liz.setContentLookup(False)
	playInfos = '###START###{0}###{1}###{2}###END###'.format(u, name, image)
	liz.addContextMenuItems([(translation(30653), 'RunPlugin('+sys.argv[0]+'?mode=addQueue&url='+quote_plus(playInfos)+')')])
	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)

params = parameters_string_to_dict(sys.argv[2])
name = unquote_plus(params.get('name', ''))
url = unquote_plus(params.get('url', ''))
mode = unquote_plus(params.get('mode', ''))
image = unquote_plus(params.get('image', ''))
page = unquote_plus(params.get('page', ''))
position = unquote_plus(params.get('position', ''))
nosub = unquote_plus(params.get('nosub', ''))
origSERIE = unquote_plus(params.get('origSERIE', ''))

if mode == 'aSettings':
	addon.openSettings()
elif mode == 'iSettings':
	xbmcaddon.Addon('inputstream.adaptive').openSettings()
elif mode == 'listThemes':
	listThemes()  
elif mode == 'listSeries':
	listSeries(url, page, position, nosub)
elif mode == 'listEpisodes':
	listEpisodes(url, origSERIE)
elif mode == 'playVideo':
	playVideo(url)
elif mode == 'listShowsFavs':
	listShowsFavs()
elif mode == 'favs':
	favs(url)
elif mode == 'addQueue':
	addQueue(url)
else:
	index()