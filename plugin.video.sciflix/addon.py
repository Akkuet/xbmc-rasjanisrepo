from xbmcswift2 import Plugin
from xbmcswift2 import download_page as DP
from BeautifulSoup import BeautifulSoup as BS
from urllib2 import HTTPError
from time import sleep
from urlparse import urlparse
from os.path import basename
import re
import json

YOUTUBE_JSON_DATA_URL="http://gdata.youtube.com/feeds/api/videos/%s?v=2&alt=json"
BLOGGER_POSTS_JSON_DATA_URL="https://www.googleapis.com/blogger/v3/blogs/8574416417432246234/posts?key=AIzaSyBIUneOnieL9jxdA1MiKuvaMrcibJc8Og0%s"
THUMBNAIL_URL="http://img.youtube.com/vi/%s/hqdefault.jpg"
YOUTUBE_PLUGIN_URL="plugin://plugin.video.youtube/?action=play_video&videoid=%s"

plugin = Plugin()


def _convert_duration(val):
  m, s = divmod(int(val), 60)
  h, m = divmod(m, 60)
  ret = "%02d:%02d:%02d" % (h, m, s)
  return ret


def _jsonfy(url):
  return json.loads(DP(url))

def videourl(pid):
  return YOUTUBE_PLUGIN_URL  % pid

def thumbnailurl(pid):
  return THUMBNAIL_URL % pid

@plugin.cached_route('/')
def index():
  items = []
  items.append( 
    {
      'label': "All Videos",
      'path': plugin.url_for('category', name = 'all'),
      'is_playable': False,
    }
  )
  done = False
  jsondata = None
  token = "&maxResults=20&fetchBodies=false"
  categories = []
  while not done:
    if jsondata != None:
      if 'nextPageToken' in jsondata:
        token = "&maxResults=20&fetchBodies=false&pageToken=%s" % jsondata['nextPageToken']
      else:
        done = True
        token = ""

    if not done:
      url = BLOGGER_POSTS_JSON_DATA_URL % token
      jsondata = _jsonfy(url)
      for item in jsondata['items']:
        for label in item['labels']:
          if label not in categories:
            categories.append(label)
            if label.find("series:") != 0 and label not in ['sheepintheisland','fallout','half-life']:
              items.append(
                  {
                    'label': label.title(),
                    'path': plugin.url_for('category', name = label),
                    'is_playable': False,
                  }
              )
  return items

   
@plugin.cached_route('/category/<name>/')
def category(name):
  items = []
  done = False
  jsondata = None
  category = ''
 
  if name != 'all':
    category = '&labels=%s' % name

  token = "&maxResults=20&fetchBodies=true%s" % category

  while not done:
    if jsondata != None:
      if 'nextPageToken' in jsondata:
        token = "&maxResults=20&fetchBodies=true&pageToken=%s%s" % ( jsondata['nextPageToken'], category )
      else:
        done = True
        token = ""

    if not done:
      url = BLOGGER_POSTS_JSON_DATA_URL % token
      print url
      jsondata = _jsonfy(url)
      if name == 'series':
        sidlist = []
        for item in jsondata['items']:
          for label in item['labels']:
            if label.find('series:')==0:
              if label not in sidlist:
                sidlist.append(label)
                name = ' '.join(re.findall('[A-Z][^A-Z]*',label.partition(':')[2]))
                items.append(
                  {
                    'label': name,
                    'path': plugin.url_for('category', name = label),
                    'is_playable': False,
                  }
                )
                

      else:
        for item in jsondata['items']:
          foo = BS(item['content'])
          playid = basename(urlparse(foo.find('param')['value']).path)
          youtube_url = YOUTUBE_JSON_DATA_URL % playid
          try:
            videojsondata = _jsonfy( youtube_url )
          except HTTPError:
            pass
          else:
            items.append (
              {
                'label': item['title'],
                'label2': videojsondata['entry']['title']['$t'],
                'path': videourl(playid),
                'thumbnail': thumbnailurl(playid),
                'is_playable' : True,
                'info': {
                    'plot': videojsondata['entry']['media$group']['media$description']['$t'],
                    'plotoutline': videojsondata['entry']['title']['$t'],
                    'duration': _convert_duration(videojsondata['entry']['media$group']['yt$duration']['seconds']),
                    'rating': videojsondata['entry']['gd$rating']['average']
                    # 'aired': item['date'].split()[0],
                },
              }
            )

  return items

if __name__ == '__main__':
    plugin.run()
