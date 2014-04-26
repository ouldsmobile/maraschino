from helper import *

class Server(object):

    def __init__(self, ip, token=None, port=32400, scheme="http://"):
        self.__ip = ip
        self.__port = port
        self.__token = token
        self.__scheme = scheme
        self.__sections = None

    def __str__(self):
        return "<Plex Server: %s%s:%s/>" % (self.__scheme, self.__ip, self.__port)

    def __repr__(self):
        return "<Plex Server: %s%s:%s/>" % (self.__scheme, self.__ip, self.__port)

    def setIp(self, ip):
        self.__ip = ip

    def setPort(self, port):
        self.__port = port

    def setPassword(self, password):
        self.__password = password

    def setUsername(self, username):
        self.__username = username

    def setToken(self, token):
        self.__token = token

    def setScheme(self, scheme):
        self.__scheme = scheme

    def sections(self, force=False):
        if self.__sections is None or force is True:
            self.__getSections()

        return self.__sections

    def getXML(self, path, args=None, raw=False):
        baseURL = "%s%s:%s" % (self.__scheme, self.__ip, self.__port)

        if debug:
            print baseURL, path, self.__token

        XML = getXMLFromPMS(baseURL, path, args, self.__token, raw)
        if raw:
            return XML

        if not XML:
            return False

        return XML

    def __getSections(self):
        path = "/library/sections"
        XML = self.getXML(path)

        sections = []
        for section in XML.findall('Directory'):
            sectionToAdd = dict()
            for attr in section.attrib:
                sectionToAdd[str(attr)] = section.attrib[attr].encode('ascii', 'ignore')

            sections.append(sectionToAdd)

        self.__sections = sections
        return sections


    def image(self, path):
        if path.startswith('/'):
            path = path[1:]

        xargs = {}
        xargs['X-Plex-Token'] = self.__token
        url = "%s%s:%s/%s" % (self.__scheme, self.__ip, self.__port, path)

        try:
            r = urllib2.Request(url, None, xargs)
            r = urllib2.urlopen(r)
            return r.read()
        except:
            raise e


    def onDeck(self):
        path = "/library/onDeck"

        XML = self.getXML(path)
        if not XML:
            return False

        items = []
        for item in XML.findall('Video'):
            itemToAdd = dict()
            for attr in item.attrib:
                itemToAdd[str(attr)] = item.attrib[attr].encode('ascii', 'ignore')

            items.append(itemToAdd)

        return items


    def section(self, id):
        path = "/library/sections/%s/all" % id
        XML = self.getXML(path)
        if not XML:
            return False

        items = {}
        for attr in XML.getroot().attrib:
            items[attr] = XML.getroot().attrib[attr]

        videos = []
        for item in XML.findall('Video'):
            itemToAdd = dict()
            for attr in item.attrib:
                itemToAdd[str(attr)] = item.attrib[attr].encode('ascii', 'ignore')

            videos.append(itemToAdd)

        directories = []
        for item in XML.findall('Directory'):
            itemToAdd = dict()
            for attr in item.attrib:
                itemToAdd[str(attr)] = item.attrib[attr].encode('ascii', 'ignore')

            directories.append(itemToAdd)

        photos = []
        for item in XML.findall('Photo'):
            itemToAdd = dict()
            for attr in item.attrib:
                itemToAdd[str(attr)] = item.attrib[attr].encode('ascii', 'ignore')

            photos.append(itemToAdd)

        items['Video'] = videos
        items['Directory'] = directories
        items['Photo'] = photos

        return items


    def recentlyAdded(self, id, start=0, size=5):
        path = "/library/sections/%s/recentlyAdded" % id
        options = {'X-Plex-Container-Start': start, 'X-Plex-Container-Size': size}
        XML = self.getXML(path, args=options)
        if not XML:
            return False

        items = {}
        for attr in XML.getroot().attrib:
            items[attr] = XML.getroot().attrib[attr]

        videos = []
        for item in XML.findall('Video'):
            itemToAdd = dict()
            for attr in item.attrib:
                itemToAdd[str(attr)] = item.attrib[attr].encode('ascii', 'ignore')

            videos.append(itemToAdd)

        directories = []
        for item in XML.findall('Directory'):
            itemToAdd = dict()
            for attr in item.attrib:
                itemToAdd[str(attr)] = item.attrib[attr].encode('ascii', 'ignore')

            directories.append(itemToAdd)

        photos = []
        for item in XML.findall('Photo'):
            itemToAdd = dict()
            for attr in item.attrib:
                itemToAdd[str(attr)] = item.attrib[attr].encode('ascii', 'ignore')

            photos.append(itemToAdd)

        items['Video'] = videos
        items['Directory'] = directories
        items['Photo'] = photos

        return items


    def refreshSection(self, id):
        path = "/library/sections/%s/refresh" % id
        try:
            response = self.getXML(path, raw=True)
            if response.getcode() is 200:
                return True
        except:
            pass

        return False


    def nowPlaying(self):
        path = "/status/sessions"
        XML = self.getXML(path)

        items = {}
        for attr in XML.getroot().attrib:
            items[attr] = XML.getroot().attrib[attr]

        videos = []
        for item in XML.findall('Video'):
            itemToAdd = dict()
            for attr in item.attrib:
                itemToAdd[str(attr)] = item.attrib[attr].encode('ascii', 'ignore')
            for child in item:
                itemToAdd[child.tag] = child.attrib
            videos.append(itemToAdd)

        directories = []
        for item in XML.findall('Directory'):
            itemToAdd = dict()
            for attr in item.attrib:
                itemToAdd[str(attr)] = item.attrib[attr].encode('ascii', 'ignore')
            for child in item:
                itemToAdd[child.tag] = child.attrib

            directories.append(itemToAdd)

        photos = []
        for item in XML.findall('Photo'):
            itemToAdd = dict()
            for attr in item.attrib:
                itemToAdd[str(attr)] = item.attrib[attr].encode('ascii', 'ignore')
            for child in item:
                itemToAdd[child.tag] = child.attrib

            photos.append(itemToAdd)

        tracks = []
        for item in XML.findall('Track'):
            itemToAdd = dict()
            for attr in item.attrib:
                itemToAdd[str(attr)] = item.attrib[attr].encode('ascii', 'ignore')
            for child in item:
                itemToAdd[child.tag] = child.attrib

            tracks.append(itemToAdd)

        items['Video'] = videos
        items['Directory'] = directories
        items['Photo'] = photos
        items['Track'] = tracks

        return items

    def clients(self):
        path = "/clients"
        XML = self.getXML(path)

        servers = []
        for server in XML.findall('Server'):
            serverToAdd = dict()
            for attr in server.attrib:
                serverToAdd[str(attr)] = server.attrib[attr].encode('ascii', 'ignore')

            servers.append(serverToAdd)

        return servers

    def metadata(self, id):
        path = "/library/metadata/%s" % id
        XML = self.getXML(path)
        return xml_to_dict(XML.getroot())

