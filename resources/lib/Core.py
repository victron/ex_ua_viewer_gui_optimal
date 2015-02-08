﻿'''
    Ex.Ua.Viewer plugin for XBMC
    Copyright (C) 2011 Vadim Skorba
    vadim.skorba@gmail.com

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
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import urllib
import urllib2
import cookielib
import re
import os
import tempfile
import Localization
from Parser import Parser
from Gui import Gui
from BeautifulSoup import BeautifulSoup

class Core:
    __plugin__ = sys.modules[ "__main__"].__plugin__
    __settings__ = sys.modules[ "__main__" ].__settings__
    URL = 'http://www.ex.ua'
    URL_SECURE = 'http://www.ex.ua'
    USERAGENT = "Mozilla/5.0 (Windows NT 6.1; rv:5.0) Gecko/20100101 Firefox/5.0"
    ROWCOUNT = (15, 30, 50, 100)[int(__settings__.getSetting("rowcount"))]
    LANGUAGE = ('ru', 'uk', 'en')[int(__settings__.getSetting("language"))]
    ROOT = sys.modules[ "__main__"].__root__

    # Private and system methods
    def __init__(self):
        if 'true' == self.__settings__.getSetting("usegate"):
            self.URL = 'http://fex.net'
        if 'true' == self.__settings__.getSetting("useproxy"):
            self.URL = 'http://uaproxy.com/index.php?hl=2e7&q=http%3A%2F%2Fwww.ex.ua'

    def localize(self, text):
        try:
            return Localization.__localization__[self.LANGUAGE][text]
        except:
            return text

    def createPlaylist(self, playlist, content, flv = True):
        xbmc.executebuiltin("Action(Stop)")
        resultPlaylist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        resultPlaylist.clear()
        image = re.compile("<img.*?src='(.+?\.jpg)\?800'.+?>").search(content)
        if image:
            image = image.group(1) + '?200'
        else:
            image = self.ROOT + '/resources/media/icons/video.png'
        for episode in playlist:
            episodeName = re.compile("([^'\" ]+get(?:%2F|/)" + episode + ").*?>(.*?)</a>").search(content)
            if episodeName:
                listitem = xbmcgui.ListItem(Parser().unescape(Parser().stripHtml(episodeName.group(2))), iconImage=image, thumbnailImage=image)
                if flv:
                    episodeName = re.compile("\"url\": \"http://www.ex.ua(/show/%s/[abcdef0-9]+.flv)\"" % episode).search(content)
                resultPlaylist.add(self.formUrl(episodeName.group(1)), listitem)
        if 1 == resultPlaylist.size():
            player = xbmc.Player(xbmc.PLAYER_CORE_AUTO)
            player.play(resultPlaylist)
        else:
            xbmc.executebuiltin("ActivateWindow(VideoPlaylist)")

    def formUrl(self, url):
        if re.search("^/", url):
            url = self.URL + url
        if re.search("uaproxy", url):
            url = url + '&hl=2e7'

        return url
    
    def fetchData(self, url):
        url = self.formUrl(url)
        request = urllib2.Request(url)
        request.add_header('User-Agent', self.USERAGENT)
        if self.__settings__.getSetting("auth"):
            authString = '; ' + self.__settings__.getSetting("auth")
        else:
            authString = ''
        request.add_header('Cookie', 'uper=' + str(self.ROWCOUNT) + authString)
        try:
            connection = urllib2.urlopen(request)
            result = connection.read()
            connection.close()
            return (result)
        except urllib2.HTTPError, e:
            print self.__plugin__ + " fetchData(" + url + ") exception: " + str(e)
            return

    # Executable actions methods
    def sectionMenu(self):
        for section in Parser().sections(self.fetchData("/%s/video" % (self.LANGUAGE))):
            Gui().drawItem(section['title'], 'openSection', section['link'], section['image'])
        Gui().drawItem(self.localize('< Search Everywhere >'), 'searchAll', image=self.ROOT + '/resources/media/icons/search.png')
        Gui().drawItem(self.localize('< Search User Page >'), 'searchUser', image=self.ROOT + '/resources/media/icons/search_user.png')
        if self.__settings__.getSetting("auth"):
            Gui().drawItem(self.localize('< User Bookmarks >'), 'openSearch', '/buffer', self.ROOT + '/resources/media/icons/bookmarks.png')
            Gui().drawItem(self.localize('< User Logout >'), 'logoutUser', image=self.ROOT + '/resources/media/icons/logout.png')
        else:
            Gui().drawItem(self.localize('< User Login >'), 'loginUser', image=self.ROOT + '/resources/media/icons/login.png')
        Gui().lockView('info')

    def openSection(self, params = {}):
        get = params.get
        url = urllib.unquote_plus(get("url"))
        if 'True' == get("contentReady"):
            videos = self.__settings__.getSetting("lastContent")
            if 0 == len(Parser().sections(videos)):
                videos = self.fetchData(url)
        else:
            videos = self.fetchData(url)
        originalId = Parser().originalId(videos)
        if originalId:
            Gui().drawItem(self.localize('< Search >'), 'openSearch', originalId, self.ROOT + '/resources/media/icons/search.png')
        else:
            Gui().drawItem(self.localize('< Search >'), 'openSearch', re.search("(\d+)$", url).group(1), self.ROOT + '/resources/media/icons/search.png')

        for section in Parser().sections(videos):
            contextMenu = [(
                self.localize('Search Like That'),
                'XBMC.Container.Update(%s)' % ('%s?action=%s&url=%s&like=%s' % (sys.argv[0], 'openSearch', re.search("(\d+)$", url).group(1), urllib.quote_plus(section['title'])))
            )]
            xbmc.log('%s: url %s'  % (sys.argv[0], section['link']), xbmc.LOGNOTICE)
            description = self.openPage2(section['link'])
            Gui().drawItem(section['title'], 'openPage', section['link'], section['image'], contextMenu=contextMenu, fanart=True, description= description)
        Gui().drawPaging(videos, 'openSection')
        xbmcplugin.setContent(int(sys.argv[1]), 'movies')
        Gui().lockView('info_big')

    def openSearch(self, params = {}):
        get = params.get
        if re.match('\d+', get("url")):
            try:
                keyboard = xbmc.Keyboard(urllib.unquote_plus(get("like")), self.localize("Edit Line For Searching:"))
            except:
                keyboard = xbmc.Keyboard('', self.localize("Input Search Phrase:"))
            keyboard.doModal()
            query = keyboard.getText()
            if keyboard.isConfirmed() and query:
                url = '/search?original_id=%s&s=%s' % (re.search("(\d+)$", get("url")).group(1), urllib.quote_plus(query))
            else:
                return
        else:
            url = urllib.unquote_plus(get("url"))
        videos = self.fetchData(url)
        for section in Parser().search(videos):
            Gui().drawItem(section['title'], 'openPage', section['link'], section['image'])
        Gui().drawPaging(videos, 'openSearch')
        Gui().lockView('info_big')

    def searchAll(self, params = {}):
        keyboard = xbmc.Keyboard("", self.localize("Input Search Phrase:"))
        keyboard.doModal()
        query = keyboard.getText()
        if not query:
            return
        elif keyboard.isConfirmed():
            params["url"] = urllib.quote_plus('/search?s=' + query)
            self.openSearch(params)

    def searchUser(self, params = {}):
        keyboard = xbmc.Keyboard("", self.localize("Input Search Username:"))
        keyboard.doModal()
        query = keyboard.getText()
        if not query:
            return
        elif keyboard.isConfirmed():
            params["url"] = '/user/' + query
            self.openSearch(params)
    
    def leaveComment(self, params = {}):
        get = params.get
        if re.match('\d+', get("url")) and self.__settings__.getSetting("auth"):
            content = self.fetchData('/edit?original_id=' + get("url") + '&link_id=2')
            commentId = re.compile("<form name=edit method=post action='/edit/(\d+)'>").search(content).group(1)
            
            if re.match('\d+', commentId):
                keyboardTitle = xbmc.Keyboard(self.localize("Sent from XBMC"), self.localize("Enter Message Title:"))
                keyboardTitle.doModal()
                title = keyboardTitle.getText()

                keyboardText = xbmc.Keyboard("", self.localize("Enter Message Text:"))
                keyboardText.doModal()
                text = keyboardText.getText()
                if not text:
                    return

                request = urllib2.Request('/r_edit/' + commentId, urllib.urlencode({'avatar_id' : 0, 'post' : text, 'public' : -1, 'title' : title}))
                request.add_header('Cookie', self.__settings__.getSetting("auth"))
                try:
                    connection = urllib2.urlopen(request)
                    result = connection.read()
                    connection.close()
                    if '1' == result:
                        xbmc.executebuiltin("Notification(%s, %s, 2500)" % (self.localize('Commenting'), self.localize('Message sent successfully')))
                        xbmc.executebuiltin("Container.Refresh()")
                    else:
                        xbmc.executebuiltin("Notification(%s, %s, 2500)" % (self.localize('Commenting'), self.localize('Message not sent')))
                except urllib2.HTTPError, e:
                    print self.__plugin__ + " leaveComment() exception: " + str(e)
                    return
        else:
            return

    def loginUser(self, params = {}):
        if self.__settings__.getSetting("auth"):
            xbmc.executebuiltin("Notification(%s, %s, 2500)" % (self.localize('Auth'), self.localize('Already logged in')))
            return

        xbmcplugin.endOfDirectory(handle=int(sys.argv[1]), succeeded=False)
        keyboardUser = xbmc.Keyboard("", self.localize("Input Username:"))
        keyboardUser.doModal()
        username = keyboardUser.getText()
        if not username:
            return

        keyboardPass = xbmc.Keyboard("", self.localize("Input Password:"))
        keyboardPass.setHiddenInput(True)
        keyboardPass.doModal()
        password = keyboardPass.getText()
        keyboardPass.setHiddenInput(False)
        if not password:
            return

        content = self.fetchData(self.URL_SECURE + '/login')
        captcha = re.compile("<img src='/captcha\?captcha_id=(\d+)'").search(content)
        if captcha:
            urllib.URLopener().retrieve(self.URL_SECURE + '/captcha?captcha_id=' + captcha.group(1), tempfile.gettempdir() + '/captcha.png')
            window = xbmcgui.Window(xbmcgui.getCurrentWindowId())
            image = xbmcgui.ControlImage(460, 20, 360, 160, tempfile.gettempdir() + '/captcha.png')
            window.addControl(image)
            keyboardCaptcha = xbmc.Keyboard("", self.localize("Input symbols from CAPTCHA image:"))
            keyboardCaptcha.doModal()
            captchaText = keyboardCaptcha.getText()
            captchaId = captcha.group(1)
            window.removeControl(image)
            if not captchaText:
                return
        else:
            captchaText = captchaId = ''

        try:
            cookieJar = cookielib.CookieJar()
            opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookieJar))
            data = urllib.urlencode({
                'login': username, 'password': password, 'flag_permanent': 1,
                'captcha_value': captchaText, 'captcha_id': captchaId
            })
            value = opener.open(self.URL_SECURE + "/login", data).read()
            if re.compile("<a href='/logout'>").search(value):
                xbmc.executebuiltin("Notification(%s, %s, 2500)" % (self.localize('Auth'), self.localize('Login successfull')))
                for cookie in cookieJar:
                    if cookie.name == 'ukey':
                        self.__settings__.setSetting("auth", 'ukey=' + cookie.value)
            else:
                xbmc.executebuiltin("Notification(%s, %s, 2500)" % (self.localize('Auth'), self.localize('Login failed')))
                self.loginUser()
        except urllib2.HTTPError, e:
            print self.__plugin__ + " loginUser() exception: " + str(e)
        xbmc.executebuiltin("Container.Refresh()")

    def logoutUser(self, params = {}):
        if not self.__settings__.getSetting("auth"):
            xbmc.executebuiltin("Notification(%s, %s, 2500)" % (self.localize('Auth'), self.localize('User not logged in')))
            return

        self.__settings__.setSetting("auth", '')
        xbmc.executebuiltin("Notification(%s, %s, 2500)" % (self.localize('Auth'), self.localize('User successfully logged out')))
        xbmc.executebuiltin("Container.Refresh()")

    def playM3U(self, params = {}):
        content = self.__settings__.getSetting("lastContent")
        if content:
            m3uPlaylistUrl = re.compile("([^'\" ]+).m3u").search(content)
            if m3uPlaylistUrl:
                m3uPlaylist = re.compile(".*/get/(\d+).*").findall(self.fetchData(m3uPlaylistUrl.group(1) + '.m3u'))
                if m3uPlaylist:
                    self.createPlaylist(m3uPlaylist, content, False)

    def playFLV(self, params = {}):
        content = self.__settings__.getSetting("lastContent")
        if content:
            flvPlaylist = re.compile("\"url\": \"http://www.ex.ua/show/(\d+)/[abcdef0-9]+.flv\"").findall(content)
            if flvPlaylist:
                self.createPlaylist(flvPlaylist, content)

    def showDetails(self, params = {}):
        Gui().showDetails()

    def openPage(self, params = {}):
        get = params.get
        content = self.fetchData(urllib.unquote_plus(get("url")))
        self.__settings__.setSetting("lastContent", content)
        artistMenu = re.compile("<div class=\"pg_menu\">.*?<a.+?</a>.*?<a(.+?)>.+?</div>", re.DOTALL).search(content)
        if artistMenu:
            if re.compile("class=\"active\"").search(artistMenu.group(1)):
                pass
            else:
                anchor = re.compile("href=\"(/view/\d+)\"").search(artistMenu.group(1))
                if anchor.group(1):
                    params.update({'url': urllib.quote_plus(anchor.group(1))})
                    return self.openPage(params)

        fileId = Parser().fileId(content)
        details = Parser().details(content)
        if details and fileId:
            if Parser().flv(content):
                Gui().drawItem(self.localize('FLV Playlist'), 'playFLV', '', self.ROOT + '/resources/media/icons/flash.png', False)
            if Parser().m3u(content):
                Gui().drawItem(self.localize('M3U Playlist'), 'playM3U', '', self.ROOT + '/resources/media/icons/video.png', False)
            comments = re.compile("<a href='(/view_comments/\d+).+?(\d+)</a>").search(content)
            if comments:
                Gui().drawDetails(details, Parser().comments(self.fetchData(comments.group(1))), comments.group(2))
            else:
                Gui().drawDetails(details, {}, 0)
            if self.__settings__.getSetting("auth"):
                Gui().drawItem(self.localize('Leave\nComment'), 'leaveComment', fileId, self.ROOT + '/resources/media/icons/comment.png', False)
                Gui().drawItem(self.localize('To My\nPage'), 'toMyPage', fileId, self.ROOT + '/resources/media/icons/add_to_user_page.png', False)
                Gui().drawItem(self.localize('To My\nBookmarks'), 'toBookmarks', fileId, self.ROOT + '/resources/media/icons/add_bookmark.png', False)
            Gui().lockView('icons')
        else:
            params.update({'contentReady': True})
            self.openSection(params)

    def openPage2(self,url, params = {}):
        get = params.get
        content =  self.fetchData(urllib.unquote_plus(url))
        self.__settings__.setSetting("lastContent", content)
        artistMenu = re.compile("<div class=\"pg_menu\">.*?<a.+?</a>.*?<a(.+?)>.+?</div>", re.DOTALL).search(content)
        if artistMenu:
            if re.compile("class=\"active\"").search(artistMenu.group(1)):
                pass
            else:
                anchor = re.compile("href=\"(/view/\d+)\"").search(artistMenu.group(1))
                if anchor.group(1):
                    params.update({'url': urllib.quote_plus(anchor.group(1))})
                    return self.openPage(params)

        fileId = Parser().fileId(content)
        details = Parser().details(content)
        description = details['description'].replace('смотреть онлайн', '')
        description = description.decode('utf-8')
        if details and fileId:
            cont_type = str(type(details['description']))
            #xbmc.log('%s: url %s content %s'  % (sys.argv[0], url, description), xbmc.LOGNOTICE)
            return description

    def toMyPage(self, params = {}):
        get = params.get
        self.addLink(get("url"), 'page')

    def toBookmarks(self, params = {}):
        get = params.get
        self.addLink(get("url"), 'bookmark')

    def addLink(self, pageId, actionName):
        actions = {'page': 6, 'bookmark': 4}
        try:
            action = actions[actionName]
        except:
            action = actions['page']
        if re.match('\d+', pageId) and self.__settings__.getSetting("auth"):
            self.fetchData('/add_link/' + str(pageId) + '/?link_id=' + str(action))
            xbmc.executebuiltin("Notification(%s, %s, 2500)" % (self.localize('Item Saving'), self.localize('Item saved successfully')))
            xbmc.executebuiltin("Container.Refresh()")
        else:
            xbmc.executebuiltin("Notification(%s, %s, 2500)" % (self.localize('Item Saving'), self.localize('Item not saved')))
            xbmc.executebuiltin("Container.Refresh()")
