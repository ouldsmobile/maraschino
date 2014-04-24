import urllib2, sys
sys.path.append("..")
from xmltodict import xmltodict

class PlexClient(object):

    def __init__(self, ip, port, token=None):
        self.ip = ip
        self.port = port
        self.token = token


    def __str__(self):
        return "<PlexClient: %s:%d/>" % (self.ip, self.port)


    def __repr__(self):
        return "<PlexClient: %s:%d/>" % (self.ip, self.port)


    def setToken(self, token):
        self.token = token


    def buildURL(self, params):
        return "http://%s:%d/%s?X-Plex-Token=%s" % (self.ip, self.port, params, self.token)


    def query(self, url):
        try:
            r = urllib2.Request(url)
            r = urllib2.urlopen(r, None, 20)
            return xmltodict.parse(r.read())
        except urllib2.URLError, e:
            raise e

        return False


    def playback(self, command):
        """
        COMMANDS:
        play
        pause
        stop
        skipNext
        skipPrevious
        stepForward
        stepBack
        setParameters?volume=[0, 100]&shuffle=0/1&repeat=0/1/2
        setStreams?audioStreamID=X&subtitleStreamID=Y&videoStreamID=Z
        seekTo?offset=XXX` - Offset is measured in milliseconds
        skipTo?key=X` - Playback skips to item with matching key
        playMedia` now accepts key, offset, machineIdentifier
        """
        return self.query(self.buildURL('player/playback/%s'%(command)))
