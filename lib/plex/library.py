from server import PlexServer

class PlexLibrary(object):
    
    def __init__(self, ip, port):
        self.s = PlexServer(ip, port)


    def onDeck(self):
        return self.s.query('library/onDeck')


    def recentlyAdded(self):
        return self.s.query('library/recentlyAdded')


    def sections(self):
        return self.s.query('library/sections')


    def getSection(self, id):
        return self.s.query('library/sections/%s/all' % id)


    def machineId(self, username, password):
        return self.s.machineId(username, password)
