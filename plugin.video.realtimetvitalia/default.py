import xbmc, xbmcaddon, xbmcgui, xbmcplugin
import os, re, sys
import httplib, urllib, urllib2, urlparse

import StorageServer

from BeautifulSoup import BeautifulSoup

from pyamf import remoting

addon = xbmcaddon.Addon()
addonID = addon.getAddonInfo('id')
thisPlugin = int(sys.argv[1])
urlSearchParameters = "http://www.realtimetv.it/video/"
urlThumbnails = "http://www.realtimetv.it/web/"
baseUrl = "http://www.realtimetv.it"

height = 1080;#268|356|360|400|572|576
const_str = "ef59d16acbb13614346264dfe58844284718fb7b"
const_playerID = 1464964207001;
const_publisherID = 1265527910001;
const_playerKey = "AQ~~,AAABJqdXbnE~,swSdm6mQzrHdUAncp0a9cwAjGy8zF2fs"
maxBitRate = 5120000

thumbnailsCache = StorageServer.StorageServer("plugin.video.realtimetvitalia", 24*7)

def loadPage(url):
	print "Load: " + url
	req = urllib2.Request(url)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:29.0) Gecko/20100101 Firefox/29.0')
	response = urllib2.urlopen(req)
	link = response.read()
	response.close()
	return link

def addDirectoryItem(label, url, mode, iconImage):
	url = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
	li = xbmcgui.ListItem(label, iconImage="DefaultFolder.png", thumbnailImage=iconImage)
	li.setInfo(type="Video", infoLabels={"title": label})
	return xbmcplugin.addDirectoryItem(handle=thisPlugin, url=url, listitem=li, isFolder=True)
	
def addLinkItem(label, url, mode, iconImage, description="", duration=""):
	url = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
	li = xbmcgui.ListItem(label, iconImage="DefaultVideo.png", thumbnailImage=iconImage)
	li.setInfo(type="Video", infoLabels={"title": label, "plot": description, "duration": str(round(int(duration)/60,0))})
	if duration:
		li.addStreamInfo("video", {"duration": int(duration)})
	li.setProperty('IsPlayable', 'true')
	return xbmcplugin.addDirectoryItem(handle=thisPlugin, url=url, listitem=li, isFolder=False) 

def getSearchParameters():
	global thisPlugin
	page = loadPage(urlSearchParameters)
	soup = BeautifulSoup(page)
	search_parameters = soup.find('ul', {'id': 'video-section-list'}).findAll('li','last-child')
	for parameter in search_parameters:
		parameter_label = parameter.find('strong').string
		parameter_link = parameter.find('a')['href']
		addDirectoryItem(parameter_label, parameter_link, "search","")
	xbmcplugin.addSortMethod(thisPlugin, xbmcplugin.SORT_METHOD_LABEL)
	xbmcplugin.endOfDirectory(thisPlugin)

def	getShows(link):
	global thisPlugin
	page = loadPage(baseUrl + link)
	soup = BeautifulSoup(page)
	search_from = soup.findAll('ol', {'class': 'letter-a'})
	for search_item in search_from:
		search_list = search_item.findAll('li')
		for item in search_list:
			item_title = item.find('a').string
			item_link = item.find('a')['href']
			#item_thumbnail = thumbnailsCache.cacheFunction(getShowThumbnail, item_link.rsplit('/',2)[1])
			addDirectoryItem(item_title, item_link, "category", "")
	xbmcplugin.addSortMethod(thisPlugin, xbmcplugin.SORT_METHOD_LABEL)
	xbmcplugin.endOfDirectory(thisPlugin)
	
def getCategories(link):
	addDirectoryItem("Episodi", link + "altri-episodi/", "show", "")
	addDirectoryItem("Video", link + "altri-video/", "show", "")
	xbmcplugin.addSortMethod(thisPlugin, xbmcplugin.SORT_METHOD_LABEL)
	xbmcplugin.endOfDirectory(thisPlugin)

def getShowThumbnail(link):
	try:
		page = loadPage(urlThumbnails + link)
		soup = BeautifulSoup(page)
	except:
		show_thumbnail = "None"
	try:
		show_banner = soup.find('img', {'class': 'article-banner'})['src']
		show_thumbnail = baseUrl + show_banner
	except:
		show_thumbnail = "None"
	return show_thumbnail

def getEpisodes(link):
	global thisPlugin
	page = loadPage(baseUrl + link + "?sort=date")  
	soup = BeautifulSoup(page)
	previousPage = soup.find(title="Torna indietro")
	nextPage = soup.find(title="Continua")
	if previousPage is not None:
		parsed_link = urlparse.urlparse(link)
		episode_link = parsed_link[0] + parsed_link[1] + parsed_link[2] + previousPage['href']
		addDirectoryItem("Precedenti", episode_link, "previous_page", "")
	episodes_containers_list = soup.findAll('dl', {'class': re.compile(' item item-')})
	for episode_container in episodes_containers_list:
		episode_title = episode_container.find('dd',{'class': 'thumbnail'}).find('a')['title']
		try:
			episode_number = episode_container.find('dd',{'class': 'description'}).string
		except:
			episode_number = ""
		try:
			episode_part = episode_container.find('dd',{'class': 'part'}).string
		except:
			episode_part = ""
		episode_link = episode_container.find('dd',{'class': 'thumbnail'}).find('a')['href']
		episode_thumbnail = episode_container.find('dd',{'class': 'thumbnail'}).find('a').find('img')['src']
		try:
			episode_description = episode_container.find('dd',{'class': 'extended-info'}).find('dl').find('dd',{'class': 'summary'}).string
		except:
			episode_description = "None"
		try:
			episode_duration_str = re.match('\((\d{2}:\d{2})\)', episode_container.find('dd',{'class': 'duration'}).string)
			split_duration = episode_duration_str.group(1).split(':')
			duration_in_seconds = int(split_duration[0])*60+int(split_duration[1])
			episode_duration = duration_in_seconds
		except:
			episode_duration = 0
		addLinkItem(episode_title + " " + episode_number + " " + episode_part, episode_link, "episode", episode_thumbnail, episode_description, episode_duration)
	if nextPage is not None:
		parsed_link = urlparse.urlparse(link)
		episode_link = parsed_link[0] + parsed_link[1] + parsed_link[2] + nextPage['href']
		addDirectoryItem("Successivi", episode_link, "next_page", "")
	xbmcplugin.endOfDirectory(thisPlugin)

def watchEpisode(link):
	page = loadPage(baseUrl + link)
	soup = BeautifulSoup(page)
	videoID = soup.find('param', {'name': '@videoPlayer'})['value']
	playBrightCoveStream(videoID)
	xbmc.sleep(4000)
	xbmc.executebuiltin('XBMC.PlayerControl(Play)')

def playBrightCoveStream(videoID):
	playerID = const_playerID
	publisherID = const_publisherID
	const = const_str
	conn = httplib.HTTPConnection("c.brightcove.com")
	envelope = remoting.Envelope(amfVersion=3)
	envelope.bodies.append(("/1", remoting.Request(target="com.brightcove.player.runtime.PlayerMediaFacade.findMediaById", body=[const, playerID, videoID, publisherID], envelope=envelope)))
	conn.request("POST", "/services/messagebroker/amf?playerId=" + str(playerID), str(remoting.encode(envelope).read()), {'content-type': 'application/x-amf'})
	response = conn.getresponse().read()
	response = remoting.decode(response).bodies[0][1].body
	streamUrl = ""
	for item in sorted(response['renditions'], key=lambda item: item['encodingRate'], reverse=False):
		encRate = item['encodingRate']
		if encRate < maxBitRate:
			streamUrl = item['defaultURL']
	if streamUrl.find("http://") == 0:
		listItem = xbmcgui.ListItem(path=streamUrl+"?videoId="+videoID+"&lineUpId=&pubId="+str(publisherID)+"&playerId="+str(playerID)+"&affiliateId=&v=&fp=&r=&g=")
	else:
		url = streamUrl[0:streamUrl.find("&")]
		playpath = streamUrl[streamUrl.find("&")+1:]
		listItem = xbmcgui.ListItem(path=url+"playpath="+playpath)
	xbmcplugin.setResolvedUrl(thisPlugin, True, listItem)

def getParams():
    param = []
    paramstring = sys.argv[2]
    if len(paramstring) >= 2:
        params = sys.argv[2]
        cleanedparams = params.replace('?', '')
        if (params[len(params) - 1] == '/'):
            params = params[0:len(params) - 2]
        pairsofparams = cleanedparams.split('&')
        param = {}
        for i in range(len(pairsofparams)):
            splitparams = {}
            splitparams = pairsofparams[i].split('=')
            if (len(splitparams)) == 2:
                param[splitparams[0]] = splitparams[1]
                                
        return param

if not sys.argv[2]:
	getSearchParameters()
else:
	params = getParams()
	print params['mode']
	if params['mode'] == "search":
		getShows(urllib.unquote(params['url']))
	elif params['mode'] == "episode":
		watchEpisode(urllib.unquote(params['url']))
	elif params['mode'] == "category":
		getCategories(urllib.unquote(params['url']))
	elif params['mode'] == "show":
		getEpisodes(urllib.unquote(params['url']))
	elif params['mode'] == "next_page":
		getEpisodes(urllib.unquote(params['url']))
	elif params['mode'] == "previous_page":
		getEpisodes(urllib.unquote(params['url']))
	else:
		getSearchParameters()
