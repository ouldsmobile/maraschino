# -*- coding: utf-8 -*-
# Copyright (c) 2014 Gustavo Hoirisch <gugahoi@gmail.com>
# Licensed under the MIT license.
# Most of the credit for the code in this library should go to the PlexConnect guys. This was based mostly on their work.

from server import Server
from client import Client
from user import User
from helper import *

__author__    = u'Gustavo Hoirisch <gugahoi@gmail.com>'
__version__   = u'0.2'
__copyright__ = u'Copyright (c) 2014 Gustavo Hoirisch'
__license__   = u'MIT'

if __name__ == '__main__':
    testLocalPMS = 0
    testMyPlexXML = 0
    testMyPlexSignIn = 0
    testMyPlexSignOut = 0
    testLocalClient = 0

    username = 'abc'
    password = 'def'
    token = 'xyz'
    user = User(username, password, token)

    # test XML from local PMS
    if testLocalPMS:
        print "*** XML from local PMS"
        server = Server('127.0.0.1')
        XML = server.sections()


    # test XML from MyPlex
    if testMyPlexXML:
        print "*** XML from MyPlex"
        XML = getXMLFromPMS('https://plex.tv', '/pms/servers', None, token)
        XML = getXMLFromPMS('https://plex.tv', '/pms/system/library/sections', None, token)


    # test MyPlex Sign In
    if testMyPlexSignIn:
        print "*** MyPlex Sign In"
        options = {'PlexConnectUDID':'007'}

        (user, token) = MyPlexSignIn(username, password, options)
        if user=='' and token=='':
            print "Authentication failed"
        else:
            print "logged in: %s, %s" %(user, token)


    # test MyPlex Sign out
    if testMyPlexSignOut:
        print "*** MyPlex Sign Out"
        MyPlexSignOut(token)
        print "logged out"


    # test sending client commands
    if testLocalClient:
        client = Client('127.0.0.1')
        client.play()
