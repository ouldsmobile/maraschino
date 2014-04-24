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
    # save login and password on db
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
    except:
        return jsonify({ 'success': False, 'msg': 'Failed to save plex credentials to db' })

    # Delete info for previous accounts
    try:
        PlexServer.query.delete()
    except:
        logger.log('Plex :: Failed to delete old server info', 'WARNING')

    # Update servers to db
    try:
        populatePlexServers()
        return listServers()
    except HTTPError as e:
        if e.code == 401:
            return jsonify({'success': False, 'msg': 'Wrong Username/Password: %s' % e.msg })
        else:
            return jsonify({'success': False, 'msg': 'HTTP Error: %s' % e })
    except:
        return jsonify({'success': False, 'msg': 'Servers not populated Successfully'})


def getServers(token=False):
    logger.log('Plex :: Getting servers from myPlex servers.xml', 'INFO')
    try:
        p = connect(
            username=get_setting_value('myPlex_username'),
            password=get_setting_value('myPlex_password')
        )
        if token:
            try:
                token = p.getToken()
            except:
                logger.log('Plex :: Failed to retrieve token, if "local authentication" is necessary Maraschino may not work with Plex', 'WARNING')
                token = None
        return p.getServers(), token # get servers from plex.tv server.xml
    except HTTPError as e:
        if e.code == 401:
            logger.log("Plex :: Wrong Username/Password: %s" % e.msg, 'ERROR')
        else:
            logger.log("Plex :: HTTP Error: %s" % e, 'ERROR')
        raise
    except Exception, e:
        logger.log('Plex :: Failed to retrieve server information from myPlex account', 'ERROR')
        raise
    return None


def populatePlexServers():
    if not get_setting_value('myPlex_username') or not get_setting_value('myPlex_password'):
        logger.log('Plex :: missing myPlex username or password', 'INFO')
        return

    updated=[]
    servers, token = getServers(True)

    # Storing server information into db
    try:
        if servers['@size'] == '1':
            addServer(servers['Server']['@name'], servers['Server']['@address'], servers['Server']['@port'], servers['Server']['@scheme'], servers['Server']['@host'], servers['Server']['@localAddresses'], servers['Server']['@machineIdentifier'], servers['Server']['@createdAt'], servers['Server']['@updatedAt'], servers['Server']['@synced'], servers['Server']['@version'], servers['Server']['@owned'], token)
            updated.append(servers['Server']['@machineIdentifier'])
        else:
            for server in servers['Server']:
                addServer(server['@name'], server['@address'], server['@port'], server['@scheme'], server['@host'], server['@localAddresses'], server['@machineIdentifier'], server['@createdAt'], server['@updatedAt'], server['@synced'], server['@version'], server['@owned'], token)
                updated.append(server['@machineIdentifier'])
    except:
        logger.log('Plex :: Failed to store server information in database', 'ERROR')
        return jsonify({'success': False, 'msg': 'Failed to store Plex server information in database'})

    # Removing Old Servers from db
    try:
        removeStaleServers(updated)
    except:
        logger.log('Plex :: Failed to remove stale servers from db', 'DEBUG')

    return jsonify({'success': True})


def addServer(name, address, port, scheme, host, localAddresses, machineIdentifier, createdAt, updatedAt, synced, version, owned, token):
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


@app.route('/xhr/switch_server/<server_id>/')
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

        server = PlexServer.query.filter(PlexServer.id == server_id).first()
        if server:
            active_server.value = server_id
            db_session.add(active_server)
            db_session.commit()
            logger.log('Switched active server to ID %s' % server_id , 'INFO')
            try:
                plexUpdateSections(server_id, exceptions=True)
            except Exception as e:
                return jsonify(success=False, msg='Failed to reach server, please check log for details.')
        else:
            logger.log('Switching server prevented, server ID %s does not exist in db' % server_id, 'INFO')

    except Exception as e:
        logger.log('Error setting active server to ID %s: %s' % (server_id, e) , 'WARNING')
        return jsonify({ 'success': False })

    return jsonify({ 'success': True })


@app.route('/xhr/plex/updateSection/<int:id>/')
def plexUpdateSections(id, exceptions=False):
    db_section = {
        'movie': {'size': 0, 'sections': {}, 'label': 'movie', 'preferred': 0},
        'home': {'size': 0, 'sections': {}, 'label': 'home', 'preferred': 0},
        'photo': {'size': 0, 'sections': {}, 'label': 'photo', 'preferred': 0},
        'artist': {'size': 0, 'sections': {}, 'label': 'artist', 'preferred': 0},
        'show': {'size': 0, 'sections': {}, 'label': 'show', 'preferred': 0},
    }

    # get server from db
    try:
        plex = PlexServer.query.filter(PlexServer.id == id).first()
    except Exception, e:
        logger.log('Plex :: Failed to retrieve server with id %i from database' % (id), 'ERROR')
        if exceptions:
            raise
        return jsonify({'success': False, 'msg': 'Failed to retrieve server from database'})

    # keeping old preferred section
    try:
        db_section['movie']['preferred'] = plex.sections['movie']['preferred']
        db_section['home']['preferred'] = plex.sections['home']['preferred']
        db_section['photo']['preferred'] = plex.sections['photo']['preferred']
        db_section['artist']['preferred'] = plex.sections['artist']['preferred']
        db_section['show']['preferred'] = plex.sections['show']['preferred']
    except:
        pass

    # attempt to get sections from server
    try:
        p = connect(ip=plex.localAddresses, token=plex.token)
        sections = p.sections()
    except URLError, e:
        logger.log('Plex :: Failed to reach server: %s' % (e.reason), 'ERROR')
        if exceptions:
            raise
        return jsonify({'success': False, 'msg': 'Failed to reach server: %s' % (e.reason)})
    except Exception, e:
        logger.log('Plex :: Failed to reach server for uknowkn reasons', 'ERROR')
        if exceptions:
            raise
        return jsonify({'success': False, 'msg': 'Unknowkn error when trying to reach the server'})

    # Go through each section and add it to new section dictionary
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
        if exceptions:
            raise
        return jsonify({'success': False, 'msg': 'Failed to update sections for server'})

    return jsonify({'success': True})


@app.route('/xhr/plex/listServers/')
def listServers(owned=True):
    servers = []

    if owned:
        dbServers = PlexServer.query.filter(PlexServer.owned == '1').all()
    else:
        dbServers = PlexServer.query.order_by(PlexServer.id).all()

    for server in dbServers:
        servers.append([server.name, server.id])

    return jsonify({'success': True, 'servers': servers })


@app.route('/xhr/plex/saveSection/<type>/<int:id>/')
@requires_auth
def savePreferredSection(type, id):
    try:
        server = PlexServer.query.filter(PlexServer.id == get_setting_value('active_server')).first()
        server.sections[type]['preferred'] = int(id)
        db_session.add(server)
        db_session.commit()
        logger.log('Plex :: Changed preferred %s section to %i' %(type, id), 'INFO')
        return jsonify({'success': True})
    except:
        return jsonify({'success': False, 'msg': 'Failed to set preferred category'})

