from helper import *

class Client(object):

    def __init__(self, ip, port=32400, token=None):
        self.__ip = ip
        self.__port = port
        self.__token = token

    def __str__(self):
        return "<Plex Client: %s:%s (%s)/>" % (self.__ip, self.__port, self.__token)

    def __repr__(self):
        return "<Plex Client: %s:%s (%s)/>" % (self.__ip, self.__port, self.__token)

    def setToken(self, token):
        self.__token = token

    def __playback(self, command):
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
        baseURL = "http://%s:%s" % (self.__ip, self.__port)
        path = "/player/playback/%s" % command

        if debug:
            print baseURL, path, self.__token

        XML = getXMLFromPMS(baseURL, path, None, self.__token)
        if not XML:
            return False

        root = XML.getroot()
        if int(root.attrib['code']) is 200:
            return root.attrib['status']

        return False

    def play(self):
        return self.__playback('play')

    def pause(self):
        return self.__playback('pause')

    def stop(self):
        return self.__playback('stop')

    def skipNext(self):
        return self.__playback('skipNext')

    def skipPrevious(self):
        return self.__playback('skipPrevious')

    def stepBack(self):
        return self.__playback('stepBack')

    def stepForward(self):
        return self.__playback('stepForward')
