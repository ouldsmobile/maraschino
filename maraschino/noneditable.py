# -*- coding: utf-8 -*-
"""Util funtions for Plex server settings."""

from maraschino.tools import get_setting_value, get_setting, requires_auth
from maraschino.models import PlexServer, Setting
from maraschino.database import db_session
from plexLib import PlexServer as connect
from maraschino import logger, app
from flask import jsonify
from urllib2 import HTTPError


def updatePlexInfo():
    if not get_setting_value('myPlex_username') or not get_setting_value('myPlex_password'):
        logger.log('Plex :: missing myPlex username or password', 'INFO')
        return

    logger.log('Plex :: Updating plex server information', 'INFO')
    p = connect(username=get_setting_value('myPlex_username'),
        password=get_setting_value('myPlex_password')
    )

    if not p:
        logger.log('Plex :: Failed to get Plex server.xml info', 'WARNING')
        return

    updated=[]
    try:
        servers = p.getServers() # get servers from plex.tv server.xml
        token = p.getToken()
        if servers['@size'] == '1':
            addPlexServer(servers['Server']['@name'], servers['Server']['@address'], servers['Server']['@port'], servers['Server']['@scheme'], servers['Server']['@host'], servers['Server']['@localAddresses'], servers['Server']['@machineIdentifier'], servers['Server']['@createdAt'], servers['Server']['@updatedAt'], servers['Server']['@synced'], servers['Server']['@version'], servers['Server']['@owned'], token)
            updated.append(servers['Server']['@machineIdentifier'])
        else:
            for server in servers['Server']:
                addPlexServer(servers['@name'], servers['@address'], servers['@port'], servers['@scheme'], servers['@host'], servers['@localAddresses'], servers['@machineIdentifier'], servers['@createdAt'], servers['@updatedAt'], servers['@synced'], servers['@version'], servers['@owned'], token)
                updated.append(server['@machineIdentifier'])

        removeStaleServers(updated)
    except HTTPError as e:
        if e.code == 401:
            logger.log("Plex :: Wrong Username/Password: %s" % e.msg, 'ERROR')
        else:
            logger.log("Plex :: HTTP Error: %s" % e, 'ERROR')
        return jsonify({'success': False, 'msg': e})
    except Exception as e:
        logger.log("Plex :: Failed to update plex servers in db: %s" % e, 'ERROR')
        return jsonify({'success': False, 'msg': e})
    except Exception, e:
        raise e

    try:
        selected_server = get_setting_value('active_server')
        if selected_server is None:
            first = PlexServer.query.filter(PlexServer.owned == 1).first()
            switch_server(first.id)
            selected_server = get_setting_value('active_server')
            logger.log('Plex :: Server automatically selected by "owned" attribute', 'DEBUG')
    except Exception as e:
        logger.log('Plex :: Failed to automatically set active server, please do it manually!', 'ERROR')

    try:
        server = PlexServer.query.filter(PlexServer.id == selected_server).first()
        if server is not None:
            plexUpdateSections(server.id)
    except Exception as e:
        logger.log('Plex :: %s' %e, 'ERROR')

    return

def addPlexServer(name, address, port, scheme, host, localAddresses, machineIdentifier, createdAt, updatedAt, synced, version, owned, token):
    s = PlexServer.query.filter(PlexServer.machineIdentifier == machineIdentifier).first()
    if s:
        logger.log('Plex :: Updating PlexServer %s in db' %(name), 'DEBUG')
        s.name = name
        s.address = address
        s.port = port
        s.scheme = scheme
        s.host = host
        s.localAddresses = localAddresses
        s.machineIdentifier = machineIdentifier
        s.createdAt = createdAt
        s.updatedAt = updatedAt
        s.synced = synced
        s.version = version
        s.owned = owned
        s.token = token

    else:
        logger.log('Plex :: Adding PlexServer %s to db' %(name), 'DEBUG')
        s = PlexServer(
                name,
                address,
                port,
                scheme,
                host,
                localAddresses,
                machineIdentifier,
                createdAt,
                updatedAt,
                synced,
                version,
                owned,
                token,
            )

    db_session.add(s)
    db_session.commit()


def removeStaleServers(current):
    servers = PlexServer.query.order_by(PlexServer.id).all()
    for server in servers:
        if server.machineIdentifier not in current:
            db_session.delete(server)
            logger.log("Plex :: Removed %s from db as it is stale" % server, 'DEBUG')

    db_session.commit()


@app.route('/xhr/switch_server/<server_id>')
@requires_auth
def switch_server(server_id=None):
    """
    Switches Plex servers manually.
    """

    try:
        active_server = get_setting('active_server')

        if not active_server:
            active_server = Setting('active_server', 0)
            db_session.add(active_server)
            db_session.commit()

        if PlexServer.query.get(server_id):
            active_server.value = server_id
            db_session.add(active_server)
            db_session.commit()
            logger.log('Switched active server to ID %s' % server_id , 'INFO')
            plexUpdateSections(server_id)
        else:
            logger.log('Switching server prevented, server ID %s does not exist in db' % server_id, 'INFO')

    except Exception as e:
        logger.log('Error setting active server to ID %s: %s' % (server_id, e) , 'WARNING')
        return jsonify({ 'status': 'error' })

    return jsonify({ 'status': 'success' })

@app.route('/xhr/plex/updateSection/<int:id>/force/')
def plexUpdateSections(id):
    db_section = {
        'movie': {'size': 0, 'sections': {}, 'label': 'movie'},
        'home': {'size': 0, 'sections': {}, 'label': 'home'},
        'photo': {'size': 0, 'sections': {}, 'label': 'photo'},
        'artist': {'size': 0, 'sections': {}, 'label': 'artist'},
        'show': {'size': 0, 'sections': {}, 'label': 'show'},
    }
    try:
        plex = PlexServer.query.filter(PlexServer.id == id).first()
        p = connect(ip=plex.localAddresses, token=plex.token)
        sections = p.sections()
        for section in sections['MediaContainer']['Directory']:
            if 'video' in section['@thumb']:
                section['@type'] = u'home'

            db_section[section['@type']]['sections'].update(
                {
                    db_section[section['@type']]['size']:
                    {
                        'key': section['@key'],
                        'type': section['@type'],
                        'title': section['@title'],
                        'uuid': section['@uuid']
                    }
                }
            )
            db_section[section['@type']]['size'] += 1
        plex.sections = db_section
        db_session.add(plex)
        db_session.commit()
        logger.log('Plex :: Successfully updated %s sections' % plex, 'INFO')
        return True
    except Exception, e:
        logger.log(e, 'ERROR')

    return False


@app.route('/xhr/plex/listServers/')
def listDbServer():
    servers = []
    for s in PlexServer.query.order_by(PlexServer.id).all():
        servers.append([s.name, s.id])

    return jsonify({'success': True, 'servers': servers })


@app.route('/xhr/plex/listSections/<int:id>/')
@requires_auth
def plexListSection(id):
    try:
        plex = PlexServer.query.filter(PlexServer.id == id).first()
        for item in plex.sections:
            print item
            for k in plex.sections[item]:
                print "\t%s - %s" % (k, plex.sections[item][k])

        return 'Check terminal'
    except Exception, e:
        raise e

