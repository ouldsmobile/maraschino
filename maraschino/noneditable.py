# -*- coding: utf-8 -*-
"""Util funtions for Plex server settings."""

from maraschino.tools import get_setting_value, get_setting, requires_auth
from maraschino.models import PlexServer, Setting
from maraschino.database import db_session
from plexLib import PlexServer as connect
from maraschino import logger, app
from flask import jsonify, request
from urllib2 import HTTPError, URLError
try:
    import json
except ImportError:
    import simplejson as json


@app.route('/xhr/plex/tutorial_save/', methods=['POST'])
def tutorial_save():
    try:
        settings = json.JSONDecoder().decode(request.form['settings'])
        for s in settings:
            setting = get_setting(s['name'])

            if not setting:
                setting = Setting(s['name'])

            setting.value = s['value']
            db_session.add(setting)
        db_session.commit()
        logger.log('Plex :: Successfully saved Plex credentials', 'INFO')
        return updatePlexInfo()
    except:
        return jsonify({ 'success': False, 'msg': 'Failed to save plex credentials to db' })


def updatePlexInfo():
    if not get_setting_value('myPlex_username') or not get_setting_value('myPlex_password'):
        logger.log('Plex :: missing myPlex username or password', 'INFO')
        try:
            return jsonify({'success': False, 'msg': 'Missing plex credentials'})
        except:
            return

    logger.log('Plex :: Updating plex server information', 'INFO')
    updated=[]
    # Fetching servers.xml from plex.tv
    try:
        p = connect(username=get_setting_value('myPlex_username'),
            password=get_setting_value('myPlex_password')
        )
        servers = p.getServers() # get servers from plex.tv server.xml
    except HTTPError as e:
        if e.code == 401:
            logger.log("Plex :: Wrong Username/Password: %s" % e.msg, 'ERROR')
        else:
            logger.log("Plex :: HTTP Error: %s" % e, 'ERROR')
        return jsonify({'success': False, 'msg': 'Wrong Username/Password: %s' % e.msg})
    except Exception, e:
        logger.log('Plex :: Failed to retrieve server information from myPlex account', 'ERROR')
        return jsonify({'success': False, 'msg': 'Failed to retrieve server information from myPlex account'})

    # Fetching token from plex.tv for local authentication
    try:
        token = p.getToken()
    except:
        logger.log('Plex :: Failed to retrieve token, if "local authentication" is necessary Maraschino may not work with Plex', 'WARNING')
        token = None

    # Storing server information into db
    try:
        if servers['@size'] == '1':
            addPlexServer(servers['Server']['@name'], servers['Server']['@address'], servers['Server']['@port'], servers['Server']['@scheme'], servers['Server']['@host'], servers['Server']['@localAddresses'], servers['Server']['@machineIdentifier'], servers['Server']['@createdAt'], servers['Server']['@updatedAt'], servers['Server']['@synced'], servers['Server']['@version'], servers['Server']['@owned'], token)
            updated.append(servers['Server']['@machineIdentifier'])
        else:
            for server in servers['Server']:
                addPlexServer(server['@name'], server['@address'], server['@port'], server['@scheme'], server['@host'], server['@localAddresses'], server['@machineIdentifier'], server['@createdAt'], server['@updatedAt'], server['@synced'], server['@version'], server['@owned'], token)
                updated.append(server['@machineIdentifier'])
    except:
        logger.log('Plex :: Failed to store server information in database', 'ERROR')
        return jsonify({'success': False, 'msg': 'Failed to store Plex server information in database'})

    # Removing Old Servers from db
    try:
        removeStaleServers(updated)
    except:
        logger.log('Plex :: Failed to remove stale servers from db', 'DEBUG')

    try:
        # if no server has been selected try one by one ordered by last updated and first owned
        if get_setting_value('active_server') is None:
            server = PlexServer.query.filter(PlexServer.owned == 1).order_by(PlexServer.updatedAt).first()
            if server:
                switch_server(server.id)
            else:
                switch_server(1)

        plexUpdateSections(get_setting_value('active_server'))
    except Exception as e:
        logger.log('Plex :: Problem updating server sections: %s' %e, 'ERROR')
        try:
            return jsonify({'success': False, 'msg': 'Problem updating server sections'})
        except:
            return

    try:
        return jsonify({'success': True})
    except:
        return

def addPlexServer(name, address, port, scheme, host, localAddresses, machineIdentifier, createdAt, updatedAt, synced, version, owned, token):
    s = PlexServer.query.filter(PlexServer.machineIdentifier == machineIdentifier).first()
    if s:
        logger.log('Plex :: Updating PlexServer %s in db' %(name), 'INFO')
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
        logger.log('Plex :: Adding PlexServer %s to db' %(name), 'INFO')
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
        else:
            logger.log('Switching server prevented, server ID %s does not exist in db' % server_id, 'INFO')

    except Exception as e:
        logger.log('Error setting active server to ID %s: %s' % (server_id, e) , 'WARNING')
        return jsonify({ 'status': 'error' })

    return jsonify({ 'status': 'success' })

@app.route('/xhr/plex/updateSection/<int:id>/force/')
def plexUpdateSections(id):
    db_section = {
        'movie': {'size': 0, 'sections': {}, 'label': 'movie', 'lastViewed': 0},
        'home': {'size': 0, 'sections': {}, 'label': 'home', 'lastViewed': 0},
        'photo': {'size': 0, 'sections': {}, 'label': 'photo', 'lastViewed': 0},
        'artist': {'size': 0, 'sections': {}, 'label': 'artist', 'lastViewed': 0},
        'show': {'size': 0, 'sections': {}, 'label': 'show', 'lastViewed': 0},
    }

    try:
        plex = PlexServer.query.filter(PlexServer.id == id).first()
    except Exception, e:
        logger.log('Plex :: Failed to retrieve server with id %i from database', 'ERROR')
        try:
            return jsonify({'success': False, 'msg': 'Failed to retrieve server from database'})
        except:
            return

    try:
        p = connect(ip=plex.localAddresses, token=plex.token)
        sections = p.sections()
    except URLError, e:
        logger.log('Plex :: Failed to reach server: %s' % (e.reason), 'ERROR')
        return jsonify({'success': False, 'msg': 'Failed to reach server: %s' % (e.reason)})
    except Exception, e:
        logger.log('Plex :: Failed to reach server for uknowkn reasons', 'ERROR')
        try:
            return jsonify({'success': False, 'msg': 'Unknowkn error when trying to reach the server'})
        except:
            return

    try:
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
    except Exception, e:
        logger.log('Plex :: Failed to update sections for server', 'ERROR')
        try:
            return jsonify({'success': False, 'msg': 'Failed to update sections for server'})
        except:
            return

    try:
        return jsonify({'success': True})
    except:
        return


@app.route('/xhr/plex/listServers/')
def listDbServer():
    servers = []
    for server in PlexServer.query.order_by(PlexServer.id).all():
        servers.append([server.name, server.id])

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
