import urllib2
# from server import PlexServer
from helper import *

try:
    import xml.etree.cElementTree as etree
except ImportError:
    import xml.etree.ElementTree as etree


class User(object):

    def __init__(self, username=None, password=None, token=None):
        self.__username = username
        self.__password = password
        self.__token = token
        self.__servers = None

    def __str__(self):
        return "<Plex User: %s (%s)/>" % (self.__username, self.__token)

    def __repr__(self):
        return "<Plex User: %s (%s)/>" % (self.__username, self.__token)

    def setPassword(self, password):
        self.__password = password

    def setUsername(self, username):
        self.__username = username

    def setToken(self, token):
        self.__token = token

    def getServers(self, force=False):
        if self.__servers is None or force is True:
            self.__getServersFromPlex()

        return self.__servers

    def MyPlexSignIn(self):
        # MyPlex web address
        MyPlexHost = 'plex.tv'
        MyPlexSignInPath = '/users/sign_in.xml'
        MyPlexURL = 'https://' + MyPlexHost + MyPlexSignInPath

        # create POST request
        xargs = getXArgsDeviceInfo()
        username = self.__username
        password = self.__password

        request = urllib2.Request(MyPlexURL, None, xargs)
        request.get_method = lambda: 'POST'  # turn into 'POST' - done automatically with data!=None. But we don't have data.

        passmanager = urllib2.HTTPPasswordMgr()
        passmanager.add_password(MyPlexHost, MyPlexURL, username, password)  # realm = 'plex.tv'
        authhandler = urllib2.HTTPBasicAuthHandler(passmanager)
        urlopener = urllib2.build_opener(authhandler)

        # sign in, get MyPlex response
        try:
            response = urlopener.open(request).read()
        except urllib2.HTTPError, e:
            if e.code==401:
                print 'Authentication failed'
                return ('', '')
            else:
                raise

        if debug:
            print "====== MyPlex sign in XML ======"
            print response
            print "====== MyPlex sign in XML finished ======"

        # analyse response
        XMLTree = etree.ElementTree(etree.fromstring(response))

        el_username = XMLTree.find('username')
        el_authtoken = XMLTree.find('authentication-token')
        if el_username is None or \
           el_authtoken is None:
            username = ''
            authtoken = ''
            print 'MyPlex Sign In failed'
        else:
            username = el_username.text
            authtoken = el_authtoken.text
            self.__token = authtoken
            if debug:
                print 'MyPlex Sign In successfull'

        return (username, authtoken)

    def MyPlexSignOut(self):

        if self.__token is None:
            if debug:
                print 'WARNING: No auhttoken, not signed in'
            return False

        # MyPlex web address
        MyPlexHost = 'plex.tv'
        MyPlexSignOutPath = '/users/sign_out.xml'
        MyPlexURL = 'http://' + MyPlexHost + MyPlexSignOutPath

        # create POST request
        xargs = { 'X-Plex-Token': self.__token }
        request = urllib2.Request(MyPlexURL, None, xargs)
        request.get_method = lambda: 'POST'  # turn into 'POST' - done automatically with data!=None. But we don't have data.

        response = urllib2.urlopen(request).read()

        if debug:
            print "====== MyPlex sign out XML ======"
            print response
            print "====== MyPlex sign out XML finished ======"
            print 'MyPlex Sign Out done'

        return response

    def __getServersFromPlex(self):
        if self.__token is None:
            print 'WARNING: Empty token, please sign in first.'
            return False

        XML = getXMLFromPMS('https://plex.tv', '/pms/servers', None, self.__token)
        if not XML:
            return False
        else:
            servers = []
            for server in XML.findall('Server'):
                serverToAdd = dict()
                for attr in server.attrib:
                    serverToAdd[str(attr)] = server.attrib[attr].encode('ascii', 'ignore')

                servers.append(serverToAdd)

            self.__servers = servers
        return servers
