from server import PlexServer

class PlexLibrary(object):

    def __init__(self, ip, port=None):
        self.s = PlexServer(ip=ip)


    def onDeck(self):
        return self.s.query('library/onDeck')


    def recentlyAdded(self, section=None, params=""):
        if section:
            return self.s.query('library/sections/%s/recentlyAdded?%s' % (section, params))

        return self.s.query('library/recentlyAdded?%s' %params)


    def sections(self):
        return self.s.query('library/sections')


    def getSection(self, id):
        return self.s.query('library/sections/%s/all' % id)


    def refreshSection(self, id):
        return self.s.query('library/section/%s/refresh' % id)
