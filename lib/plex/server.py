import urllib2, json

class PlexServer(object):

    def __init__(self, ip='192.168.0.10', port=32400):
        self.ip = ip
        self.port = port


    def __str__(self):
        return "<PlexServer: %s:%d/>" % (self.ip, self.port) 
    

    def __repr__(self):
        return "<PlexServer: %s:%d/>" % (self.ip, self.port) 


    def address(self, params=''):
        return "http://%s:%s/%s" %(self.ip, self.port, params)


    def query(self, params=''):
        headers = {'Accept': 'application/json'}
        try:
            r = urllib2.Request(self.address(params), None, headers)
            r = urllib2.urlopen(r)
            return json.load(r)
        except urllib2.URLError, e:
            print e
        
        return False
            

    def basicInfo(self, param=''):
        try:
            info = self.query()
            if param is not '':
                return info[param]

            return info
        except:
            print 'Error loading Plex Info from %s' %(self.address())
        
        return False
