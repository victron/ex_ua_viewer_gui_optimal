# ex_ua_viewer_gui_optimal
source code located on https://code.google.com/p/ex-ua-viewer/
#### Differences
- GUI view change
- file info taken during list creation 

#### diff from original not so big
```diff
diff -crB plugin.video.ex.ua.viewer/default.py plugin.video.ex.ua.viewer-optimal/default.py
*** plugin.video.ex.ua.viewer/default.py	2015-02-09 21:19:24.502643887 +0200
--- plugin.video.ex.ua.viewer-optimal/default.py	2015-02-09 21:20:30.149114539 +0200
***************
*** 25,29 ****
--- 25,30 ----
  __root__ = __settings__.getAddonInfo('path')
  
  if (__name__ == "__main__" ):
+ 
      from resources.lib.Router import Router
      Router(sys.argv[2])
diff -crB plugin.video.ex.ua.viewer/resources/lib/Core.py plugin.video.ex.ua.viewer-optimal/resources/lib/Core.py
*** plugin.video.ex.ua.viewer/resources/lib/Core.py	2015-02-09 21:19:24.502155704 +0200
--- plugin.video.ex.ua.viewer-optimal/resources/lib/Core.py	2015-02-09 21:20:30.142901679 +0200
***************
*** 115,121 ****
              Gui().drawItem(self.localize('< User Logout >'), 'logoutUser', image=self.ROOT + '/resources/media/icons/logout.png')
          else:
              Gui().drawItem(self.localize('< User Login >'), 'loginUser', image=self.ROOT + '/resources/media/icons/login.png')
!         Gui().lockView('list')
  
      def openSection(self, params = {}):
          get = params.get
--- 115,121 ----
              Gui().drawItem(self.localize('< User Logout >'), 'logoutUser', image=self.ROOT + '/resources/media/icons/logout.png')
          else:
              Gui().drawItem(self.localize('< User Login >'), 'loginUser', image=self.ROOT + '/resources/media/icons/login.png')
!         Gui().lockView('info')
  
      def openSection(self, params = {}):
          get = params.get
***************
*** 137,145 ****
                  self.localize('Search Like That'),
                  'XBMC.Container.Update(%s)' % ('%s?action=%s&url=%s&like=%s' % (sys.argv[0], 'openSearch', re.search("(\d+)$", url).group(1), urllib.quote_plus(section['title'])))
              )]
!             Gui().drawItem(section['title'], 'openPage', section['link'], section['image'], contextMenu=contextMenu)
          Gui().drawPaging(videos, 'openSection')
!         Gui().lockView('info')
  
      def openSearch(self, params = {}):
          get = params.get
--- 137,148 ----
                  self.localize('Search Like That'),
                  'XBMC.Container.Update(%s)' % ('%s?action=%s&url=%s&like=%s' % (sys.argv[0], 'openSearch', re.search("(\d+)$", url).group(1), urllib.quote_plus(section['title'])))
              )]
!             xbmc.log('%s: url %s'  % (sys.argv[0], section['link']), xbmc.LOGNOTICE)
!             description = self.openPage2(section['link'])
!             Gui().drawItem(section['title'], 'openPage', section['link'], section['image'], contextMenu=contextMenu, fanart=True, description= description)
          Gui().drawPaging(videos, 'openSection')
!         xbmcplugin.setContent(int(sys.argv[1]), 'movies')
!         Gui().lockView('info_big')
  
      def openSearch(self, params = {}):
          get = params.get
***************
*** 160,166 ****
          for section in Parser().search(videos):
              Gui().drawItem(section['title'], 'openPage', section['link'], section['image'])
          Gui().drawPaging(videos, 'openSearch')
!         Gui().lockView('info')
  
      def searchAll(self, params = {}):
          keyboard = xbmc.Keyboard("", self.localize("Input Search Phrase:"))
--- 163,169 ----
          for section in Parser().search(videos):
              Gui().drawItem(section['title'], 'openPage', section['link'], section['image'])
          Gui().drawPaging(videos, 'openSearch')
!         Gui().lockView('info_big')
  
      def searchAll(self, params = {}):
          keyboard = xbmc.Keyboard("", self.localize("Input Search Phrase:"))
***************
*** 336,341 ****
--- 339,367 ----
              params.update({'contentReady': True})
              self.openSection(params)
  
+     def openPage2(self,url, params = {}):
+         get = params.get
+         content =  self.fetchData(urllib.unquote_plus(url))
+         self.__settings__.setSetting("lastContent", content)
+         artistMenu = re.compile("<div class=\"pg_menu\">.*?<a.+?</a>.*?<a(.+?)>.+?</div>", re.DOTALL).search(content)
+         if artistMenu:
+             if re.compile("class=\"active\"").search(artistMenu.group(1)):
+                 pass
+             else:
+                 anchor = re.compile("href=\"(/view/\d+)\"").search(artistMenu.group(1))
+                 if anchor.group(1):
+                     params.update({'url': urllib.quote_plus(anchor.group(1))})
+                     return self.openPage(params)
+ 
+         fileId = Parser().fileId(content)
+         details = Parser().details(content)
+         description = details['description'].replace('смотреть онлайн', '')
+         description = description.decode('utf-8')
+         if details and fileId:
+             cont_type = str(type(details['description']))
+             #xbmc.log('%s: url %s content %s'  % (sys.argv[0], url, description), xbmc.LOGNOTICE)
+             return description
+ 
      def toMyPage(self, params = {}):
          get = params.get
          self.addLink(get("url"), 'page')
diff -crB plugin.video.ex.ua.viewer/resources/lib/Gui.py plugin.video.ex.ua.viewer-optimal/resources/lib/Gui.py
*** plugin.video.ex.ua.viewer/resources/lib/Gui.py	2015-02-09 21:19:24.501985761 +0200
--- plugin.video.ex.ua.viewer-optimal/resources/lib/Gui.py	2015-02-09 21:20:30.143987007 +0200
***************
*** 45,50 ****
--- 45,51 ----
              'list': 50,
              'info': 50,
              'icons': 500,
+             'info_big':504,
          },
          {#Transperency!
              'list': 50,
***************
*** 87,98 ****
          if nextButton:
              self.drawItem('[%s] ' % pages.group(1) + self.localize('Next >>'), action, self.URL + nextButton.group(1), self.ROOT + '/resources/media/icons/next.png')
  
!     def drawItem(self, title, action, link = '', image=ROOT + '/resources/media/icons/video.png', isFolder = True, contextMenu=None):
          listitem = xbmcgui.ListItem(title, iconImage=image, thumbnailImage=image)
          url = '%s?action=%s&url=%s' % (sys.argv[0], action, urllib.quote_plus(link))
          if contextMenu:
              listitem.addContextMenuItems(contextMenu)
          if isFolder:
              listitem.setProperty("Folder", "true")
          else:
              listitem.setInfo(type = 'Video', infoLabels = {"Title":title})
--- 88,102 ----
          if nextButton:
              self.drawItem('[%s] ' % pages.group(1) + self.localize('Next >>'), action, self.URL + nextButton.group(1), self.ROOT + '/resources/media/icons/next.png')
  
!     def drawItem(self, title, action, link = '', image=ROOT + '/resources/media/icons/video.png', isFolder = True, contextMenu=None, fanart=False, description = None):
          listitem = xbmcgui.ListItem(title, iconImage=image, thumbnailImage=image)
          url = '%s?action=%s&url=%s' % (sys.argv[0], action, urllib.quote_plus(link))
          if contextMenu:
              listitem.addContextMenuItems(contextMenu)
          if isFolder:
+             if fanart:
+                 listitem.setProperty('fanart_image', image)
+                 listitem.setInfo('video', {'plot': description})
              listitem.setProperty("Folder", "true")
          else:
              listitem.setInfo(type = 'Video', infoLabels = {"Title":title})
***************
*** 106,112 ****
              description += self.localize('[B]:::Comments:::[/B]\n\n')
              for comment in comments:
                  description += "[B]%s[/B]%s" % (comment['title'], comment['comment'])
!         listitem = xbmcgui.ListItem(self.localize('Description &\nComments') + ' [%s]' % count, iconImage=self.ROOT + '/resources/media/icons/description.png')
          description += "-----------------------------------------------------------------------------------------\n\n\n\n\n\n\n"
          listitem.setInfo(type = 'Video', infoLabels = {
              "Title": details['title'],
--- 109,116 ----
              description += self.localize('[B]:::Comments:::[/B]\n\n')
              for comment in comments:
                  description += "[B]%s[/B]%s" % (comment['title'], comment['comment'])
!         listitem = xbmcgui.ListItem(self.localize('Description &\nComments') + ' [%s]' % count, thumbnailImage=self.ROOT + '/resources/media/icons/description.png')
! #                                    iconImage=self.ROOT + '/resources/media/icons/description.png')
          description += "-----------------------------------------------------------------------------------------\n\n\n\n\n\n\n"
          listitem.setInfo(type = 'Video', infoLabels = {
              "Title": details['title'],
```
