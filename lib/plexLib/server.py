import urllib2, json, base64
import sys
sys.path.append("..")
from xmltodict import xmltodict

class PlexServer(object):

    def __init__(self, ip=None, port=32400, username=None, password=None):
        self.ip = ip
        self.port = port
        self.username = username
        self.password = password


    def __str__(self):
        return "<PlexServer: %s:%d/>" % (self.ip, self.port) 
    

    def __repr__(self):
        return "<PlexServer: %s:%d/>" % (self.ip, self.port) 


    def address(self, params=''):
        return "http://%s:%s/%s" %(self.ip, self.port, params)


    def query(self, params=''):
        try:
            r = urllib2.Request(self.address(params))
            r = urllib2.urlopen(r)
            return xmltodict.parse(r.read())
        except urllib2.URLError, e:
            print e
        
        return False
            

    def basicInfo(self, param=''):
        try:
            info = self.query()
            if param is not '':
                return info.childNodes[0].attributes[param].value 

            return info
        except:
            print 'Error loading Plex Info from %s' %(self.address())
        
        return False


    def getServerInfo(self):
        try:
            r = urllib2.Request("https://plex.tv/pms/servers.xml")
            base64string = base64.encodestring('%s:%s' % (self.username, self.password)).replace('\n', '')
            r.add_header("Authorization", "Basic %s" % base64string)
            r = urllib2.urlopen(r)
            el = xmltodict.parse(r.read())
            return el['MediaContainer']
        except urllib2.URLError:
            raise

