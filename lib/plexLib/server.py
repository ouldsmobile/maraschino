import urllib2, base64, sys, platform
sys.path.append("..")
from xmltodict import xmltodict


class PlexServer(object):

    def __init__(self, ip=None, port=32400, username=None, password=None, token=None, scheme="http://"):
        self.ip = ip
        self.port = port
        self.username = username
        self.password = password
        self.token = token
        self.scheme = scheme


    def __str__(self):
        return "<PlexServer: %s:%d/>" % (self.ip, self.port)


    def __repr__(self):
        return "<PlexServer: %s:%d/>" % (self.ip, self.port)


    def setIp(self, ip):
        self.ip = ip


    def setPort(self, port):
        self.port = port


    def setPassword(self, password):
        self.password = password


    def setUsername(self, username):
        self.username = username


    def setToken(self, token):
        self.token = token


    def setScheme(self, scheme):
        self.scheme = scheme


    def buildURL(self, path, params=""):
        return "%s%s?X-Plex-Token=%s&%s" % (self.address(), path, self.token, params)


    def address(self):
        return "%s%s:%s/" % (self.scheme, self.ip, self.port)


    def query(self, url):
        try:
            r = urllib2.Request(url)
            r = urllib2.urlopen(r)
            return xmltodict.parse(r.read())
        except urllib2.URLError, e:
            raise e

        return False


    def getServers(self):
        try:
            r = urllib2.Request("https://plex.tv/pms/servers.xml")
            base64string = base64.encodestring('%s:%s' % (self.username, self.password)).replace('\n', '')
            r.add_header("Authorization", "Basic %s" % base64string)
            r = urllib2.urlopen(r)
            el = xmltodict.parse(r.read())
            return el['MediaContainer']
        except urllib2.URLError:
            raise


    def getToken(self):
        try:
            system = str(platform.system())
            if 'Darwin' in system:
                system = 'MacOSX'
            r = urllib2.Request("https://my.plexapp.com/users/sign_in.xml", data="")
            base64string = base64.encodestring('%s:%s' % (self.username, self.password)).replace('\n', '')
            r.add_header("Authorization", "Basic %s" % base64string)
            r.add_header("X-Plex-Client-Identifier", str(platform.node()))
            r.add_header('X-Plex-Platform', system)
            r.add_header('X-Plex-Platform-Version', str(platform.release()))
            r.add_header('X-Plex-Product', 'Maraschino')
            r.add_header('X-Plex-Product-Version', ':D')
            r.add_header('X-Plex-Device', str(platform.node()))
            r.add_header('X-Plex-Device-Name', 'Web Frontend')
            r.add_header('X-Plex-Model', ':-) :)')
            r = urllib2.urlopen(r)
            el = xmltodict.parse(r.read())
            return el['user']['@authenticationToken']
        except urllib2.URLError:
            raise


    def image(self, path):
        try:
            r = urllib2.Request(self.buildURL(path))
            r = urllib2.urlopen(r)
            return r.read()
        except urllib2.URLError, e:
            raise e

    def onDeck(self):
        return self.query(self.buildURL('library/onDeck'))


    def recentlyAdded(self, section=None, params=""):
        if section:
            return self.query(self.buildURL('library/sections/%s/recentlyAdded' % (section), params))

        return self.query(self.buildURL('library/recentlyAdded', params))


    def sections(self):
        return self.query(self.buildURL('library/sections'))


    def getSection(self, id):
        return self.query(self.buildURL('library/sections/%s/all' % id))


    def refreshSection(self, id):
        return self.query(self.buildURL('library/section/%s/refresh' % id))


    def nowPlaying(self):
        return self.query(self.buildURL('status/sessions'))


