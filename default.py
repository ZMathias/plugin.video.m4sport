# -*- coding: utf-8 -*-
import sys
import xbmcaddon, os, xbmcgui, re, xbmcplugin, json, xbmc, inputstreamhelper
from resources.lib import client
from resources.lib.utils import py2_encode

if sys.version_info[0] == 3:
    import urllib.parse as urlparse
    from urllib.parse import quote_plus
    from urllib.parse import parse_qsl
else:
    import urlparse
    from urllib import quote_plus
    from urlparse import parse_qsl

m4_url = 'https://www.m4sport.hu'
syshandle = int(sys.argv[1])


def root():
    addDir({'title': '[COLOR red]''[B]' + u'M4 \u00C9l\u0151' + '[/B][/COLOR]', 'action': 'getLive',
            'streamid': 'mtv4live', 'isFolder': 'false'})
    addDir({'title': '[COLOR orange]' + u'M4 id\u0151szakos stream 1' + '[/COLOR]', 'action': 'getLive',
            'streamid': 'extra', 'isFolder': 'false'})
    addDir({'title': '[COLOR orange]' + u'M4 id\u0151szakos stream 2' + '[/COLOR]', 'action': 'getLive',
            'streamid': 'extra2', 'isFolder': 'false'})
    addDir({'title': '[COLOR orange]' + u'M4 id\u0151szakos stream 3' + '[/COLOR]', 'action': 'getLive',
            'streamid': 'extra3', 'isFolder': 'false'})
    addDir({'title': '[COLOR orange]' + u'M4 id\u0151szakos stream 4' + '[/COLOR]', 'action': 'getLive',
            'streamid': 'extra4', 'isFolder': 'false'})
    addDir({'title': '[COLOR orange]' + u'M4 id\u0151szakos stream 5' + '[/COLOR]', 'action': 'getLive',
            'streamid': 'extra5', 'isFolder': 'false'})
    addDir({'title': '[COLOR orange]' + u'M4 Sport 1' + '[/COLOR]', 'action': 'getLive', 'streamid': 'm4sport1',
            'isFolder': 'false'})
    addDir({'title': '[COLOR orange]' + u'M4 Sport 2' + '[/COLOR]', 'action': 'getLive', 'streamid': 'm4sport2',
            'isFolder': 'false'})
    addDir({'title': '[COLOR orange]' + u'M4 Sport 3' + '[/COLOR]', 'action': 'getLive', 'streamid': 'm4sport3',
            'isFolder': 'false'})
    addDir({'title': '[COLOR orange]' + u'M4 Sport 4' + '[/COLOR]', 'action': 'getLive', 'streamid': 'm4sport4',
            'isFolder': 'false'})
    addDir({'title': '[COLOR orange]' + u'M4 Sport 5' + '[/COLOR]', 'action': 'getLive', 'streamid': 'm4sport5',
            'isFolder': 'false'})

    categories = [{'category': '1020',
                   'title': u'Sporth\u00EDrek'},

                  {'category': '768',
                   'title': 'Magyar foci'},

                  {'category': '548',
                   'title': 'Boxutca'},

                  {'category': '1025',
                   'title': u'Sportk\u00F6zvet\u00EDt\u00E9sek'}]

    [i.update({'action': 'getEpisodes', 'page': '1', 'isFolder': 'true'}) for i in categories]
    for i in categories:
        addDir(i)
    xbmcplugin.endOfDirectory(syshandle)


def getEpisodes():
    query = urlparse.urljoin(m4_url,
                             '/wp-content/plugins/telesport.hu.widgets/widgets/newSubCategory/ajax_loadmore.php?cat_id={0}&post_type=video&blog_id=4&page_number={1}'.format(
                                 category, page))
    r = client.request(query)
    result = json.loads(r)
    for i in result:
        # if i['has_video'] != True: continue
        title = client.replaceHTMLCodes(i['title'])
        title = py2_encode(title)
        link = py2_encode(i['link'])
        if link.startswith('//'): link = 'http:' + link
        img = py2_encode(i['image'])
        if img.startswith('//'): img = 'http:' + img
        addDir({'title': title, 'url': link, 'action': 'getVideo', 'image': img, 'isFolder': 'false'})
    if len(result) >= 10:
        addDir({'title': '[COLOR green]Következő oldal[/COLOR]', 'action': 'getEpisodes', 'page': str(int(page) + 1),
                'category': category, 'isFolder': 'true'})
    xbmcplugin.endOfDirectory(syshandle)


def isDirty(candidate: str):
    if candidate is None:
        return True

    blocklist = ['bumper', 'promo', 'advertisement', 'reklam']
    return any(word in candidate.lower() for word in blocklist)


def getValidStreams(playlist_data):
    ls = []
    valid_list = []
    if isinstance(playlist_data, dict):  # if it is only one object and not an array then add it to the list
        ls.append(playlist_data)
    elif isinstance(playlist_data, list):
        ls = playlist_data

    for obj in ls:
        if not isDirty(obj.get('file', None)):  # an URL is dirty if it contains promo keywords or if it is of type None
            print(f'Found valid URL: {obj.get('file')}')
            valid_list.append(obj)
        else:
            print(f'Filtered the following URL: {obj.get('file')}')

    return valid_list


def getLive():
    content_id = streamid
    embedded_url = 'https://player.mediaklikk.hu/playernew/player.php?video={0}&noflash=yes&osfamily=Android&osversion=7.0&browsername=Chrome%20Mobile&browserversion=&title=&contentid={0}&embedded=1'.format(
        content_id)
    r = client.request(embedded_url)

    regex_match = re.search(r'var\s+playData\s*=\s*(\[[\s\S]*?\])\s*;', r)

    if regex_match is None:
        regex_match = re.search(r'(\[[^\]]*?"connectmedia"[^\]]*?\])',r)  # fallback regex to search for the connectmedia string if the edge server generated JS code changes

    if regex_match is None:  # only throw fatal error if both failed
        if content_id.startswith('extra'):
            error_msg = 'Ezen az időszakos streamen jelenleg nincsen adás.'
        else:
            error_msg = 'Nem található egy helyes stream URL sem.'
        ok = xbmcgui.Dialog().ok('Stream hiba', error_msg)
        return  # fatal error

    valid_streams = []
    for group in regex_match.groups():  # check every matched json
        try:
            json_data = json.loads(group)
        except json.JSONDecodeError as e:
            print(f'Captured content: \n{group}\n not a valid JSON structure')
        # if loaded successfully then try to filter
        valid_streams.extend(getValidStreams(json_data))

    # if there is nothing to play, should never happen...
    if len(valid_streams) == 0:
        xbmcgui.Dialog().ok(
            'Stream figyelmeztetés',
            'Nem találtunk érvényes közvetítést...'
        )
        return

    # build playlist for kodi to resolve with multiple streams
    kodi_playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    kodi_playlist.clear()

    for index, item in enumerate(valid_streams):
        stream_url = item.get("file")
        stream_type = item.get("type", "").lower()

        if not stream_url:
            continue

        stream_url = stream_url.replace('\\', '')
        if not stream_url.startswith("http"):
            stream_url = "https:" + stream_url if stream_url.startswith("//") else stream_url

        item_title = f"{title} Stream {index + 1}"

        list_item = xbmcgui.ListItem(label=item_title)
        list_item.setProperty('IsPlayable', 'true')

        if stream_type == "dash":
            list_item.setProperty('inputstream', 'inputstream.adaptive')
            list_item.setProperty('inputstream.adaptive.manifest_type', 'mpd')

            drm = item.get("drm", {}).get("widevine", {})
            if drm:
                license_key = drm.get("url")
                if license_key:
                    list_item.setProperty('inputstream.adaptive.license_type', 'com.widevine.alpha')
                    list_item.setProperty('inputstream.adaptive.license_key', f"{license_key}||R{{SSM}}|")

        elif stream_type == "hls" or stream_url.endswith(".m3u8"):
            list_item.setProperty('inputstream', 'inputstream.adaptive')
            list_item.setProperty('inputstream.adaptive.manifest_type', 'hls')

        kodi_playlist.add(url=stream_url, listitem=list_item)

    if kodi_playlist.size() > 0:
        is_helper = inputstreamhelper.Helper('mpd', drm='widevine')

        if not is_helper.check_inputstream():
            xbmcgui.Dialog().ok('Hiba', 'Widevine CDM telepítése sikertelen vagy megszakítva.')
            return

        xbmcplugin.setResolvedUrl(syshandle, False, xbmcgui.ListItem())
        xbmc.Player().play(kodi_playlist)


def getVideo():
    r = client.request(url)
    token = re.search(r'[\'"]token[\'"]\s*:\s*[\'"]([^\'"]+)', r).group(1)
    m = client.request('http://player.mediaklikk.hu/playernew/player.php?video=' + token)
    link = re.search(r'"file"\s*:\s*"([^"]+)', m).group(1)
    link = link.replace('\\', '')
    if (not link.startswith("http:") or not link.startswith("https:")):
        link = "%s%s" % ("https:", link)
    stream = getStream(link)
    if stream:
        resolve(stream, image, title)
    else:
        return


def getStream(url):
    if xbmcaddon.Addon().getSetting('quality') == 'true':
        return url
    result = client.request(url)
    from resources.lib import m3u8_parser
    playlist = m3u8_parser.parse(result)['playlists']

    if not playlist:
        return url

    try:
        playlist = sorted(playlist, key=lambda tup: tup['stream_info']['bandwidth'], reverse=True)
    except:
        pass

    qkey = 'resolution' if 'resolution' in playlist[0]['stream_info'] else 'bandwidth'
    qualities = []
    urls = []

    for item in playlist:
        quality = str(item['stream_info'][qkey])
        uri = item['uri']
        uri = urlparse.urljoin(url, uri)
        qualities.append(quality)
        urls.append(uri)

    dialog = xbmcgui.Dialog()
    q = dialog.select('Minőség', qualities)
    if q <= len(qualities) and not q == -1:
        return (urls[q])
    else:
        return None


def resolve(url, icon, title):
    item = xbmcgui.ListItem(path=url)
    item.setArt({'icon': icon, 'thumb': icon})
    info_tag = item.getVideoInfoTag()
    info_tag.setTitle(title)
    xbmcplugin.setResolvedUrl(syshandle, True, item)


def addDir(item):
    sysimage = xbmcaddon.Addon().getAddonInfo('icon');
    sysfanart = xbmcaddon.Addon().getAddonInfo('fanart')

    label = item['title']
    if 'image' in item:
        image = item['image']
    else:
        image = sysimage
    fanart = item['fanart'] if 'fanart' in item else sysfanart
    isFolder = False if 'isFolder' in item and not item['isFolder'] == 'true' else True
    url = '%s?action=%s' % (sys.argv[0], item['action'])
    try:
        url += '&title=%s' % quote_plus(item['title'])
    except KeyError:
        url += '&title=%s' % quote_plus(py2_encode(item['title']))
    try:
        url += '&url=%s' % quote_plus(item['url'])
    except:
        pass
    try:
        url += '&image=%s' % quote_plus(item['image'])
    except:
        pass
    try:
        url += '&category=%s' % quote_plus(item['category'])
    except:
        pass
    try:
        url += '&page=%s' % quote_plus(item['page'])
    except:
        pass
    try:
        url += '&streamid=%s' % quote_plus(item['streamid'])
    except:
        pass

    liz = xbmcgui.ListItem(label=label)
    liz.setArt({'icon': image, 'thumb': image, 'poster': image, 'fanart': fanart})
    info_tag = liz.getVideoInfoTag()
    info_tag.setTitle(label)

    if isFolder is False:
        if item.get('action') != 'getLive':
            liz.setProperty('IsPlayable', 'true')

    xbmcplugin.addDirectoryItem(handle=syshandle, url=url, listitem=liz, isFolder=isFolder)


params = dict(parse_qsl(sys.argv[2].replace('?', '')))

url = params.get("url")
title = params.get("title")
image = params.get("image")
action = params.get("action")
page = params.get("page")
category = params.get("category")
streamid = params.get("streamid", '')

if action is None:
    root()
elif action == 'getEpisodes':
    getEpisodes()
elif action == 'getVideo':
    getVideo()
elif action == 'getLive':
    getLive()