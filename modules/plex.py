from flask import render_template, jsonify, send_file
from maraschino import app, logger, RUNDIR
from maraschino.tools import requires_auth, get_setting_value
from maraschino.models import PlexServer as dbserver
from plexLib import PlexLibrary
import base64, urllib2, StringIO


def safeAddress(ip, port=32400):
    return "http://%s:%s" % (ip, port)


def error(e):
    global plex
    return render_template('plex.html',
        error=True,
        exception=e
    )


def plex_log(msg, level='INFO'):
    logger.log('Plex :: %s'%(msg), level)


def getActiveServer():
    selected_server = get_setting_value('active_server')
    if selected_server is None:
        plex_log('Server automatically selected by "owned" attribute', 'DEBUG')
        return dbserver.query.filter(dbserver.owned == 1).first()

    return dbserver.query.filter(dbserver.id == selected_server).first()


@app.route('/xhr/plex/listServers/')
def listDbServer():
    servers = []
    for s in dbserver.query.order_by(dbserver.id).all():
        servers.append([s.name, s.id])

    return jsonify({'success': True, 'servers': servers })


@app.route('/xhr/plex/listSections/<int:id>/')
@requires_auth
def plexListSection(id):
    try:
        plex = dbserver.query.filter(dbserver.id == id).first()
        for item in plex.sections:
            print item
            for k in plex.sections[item]:
                print "\t%s - %s" % (k, plex.sections[item][k])

        return 'Check terminal'
    except Exception, e:
        raise e


@app.route('/xhr/plex/updateSections/<int:id>/')
@requires_auth
def plexUpdateSections(id):
    from maraschino.database import db_session
    db_section = {}
    try:
        plex = dbserver.query.filter(dbserver.id == id).first()
        p = PlexLibrary(plex.ip)
        sections = p.sections()
        for section in sections['MediaContainer']['Directory']:
            db_section.update(
                {
                    section['@uuid']:
                    {
                        'key': section['@key'],
                        'type': section['@type'],
                        'title': section['@title']
                    }
                }
            )
        plex.sections = db_section
        db_session.add(plex)
        db_session.commit()
        plex_log('Successfully updated %s sections' % plex)
        return True
    except Exception, e:
        plex_log(e, 'ERROR')

    return False


@app.route('/xhr/plex/')
def plex():
    try:
        s = getActiveServer()
        if s is not None:
            if not s.sections:
                plexUpdateSections(id=s.id)

            return xhr_on_deck()
        else:
            return error('No PlexServer in db. Please check your myPlex username and password.')
    except:
        return error('Failed to read PlexServer from db')


@app.route('/xhr/plex/onDeck/')
def xhr_on_deck():
    try:
        s = getActiveServer()
        p = PlexLibrary(s.ip)
        onDeck = p.onDeck()
        return render_template('plex/on_deck.html',
            server=s,
            video=onDeck['MediaContainer'],
            address=safeAddress(s.ip),
        )
    except Exception as e:
        return error(e)


@app.route('/xhr/plex_recent_movies/')
def xhr_recent_movies():
    try:
        s = getActiveServer()
        p = PlexLibrary(s.ip)
        query = None
        for section in s.sections:
            if 'movie' in s.sections[section]['type']:
                query=s.sections[section]['key']

        recentlyAdded = p.recentlyAdded(section=query, params="X-Plex-Container-Start=0&X-Plex-Container-Size=5")

        for movie in recentlyAdded['MediaContainer']['Video']:
            try:
                movie['@rating'] = round(float(movie['@rating']), 1)
            except:
                pass

        return render_template('plex/recent.html',
            title='movies',
            server=s,
            movies=recentlyAdded['MediaContainer'],
        )
    except Exception as e:
        return error(e)


@app.route('/xhr/plex_recent_episodes/')
def xhr_recent_episodes():
    try:
        s = getActiveServer()
        p = PlexLibrary(s.ip)
        query = None
        for section in s.sections:
            if 'show' in s.sections[section]['type']:
                query=s.sections[section]['key']
                break

        recentlyAdded = p.recentlyAdded(section=query, params="X-Plex-Container-Start=0&X-Plex-Container-Size=5")

        return render_template('plex/recent.html',
            title='episodes',
            server=s,
            episodes=recentlyAdded['MediaContainer'],
        )
    except Exception as e:
        return error(e)


@app.route('/xhr/plex_recent_albums/')
def xhr_recent_albums():
    try:
        s = getActiveServer()
        p = PlexLibrary(s.ip)
        query = None
        for section in s.sections:
            if 'artist' in s.sections[section]['type']:
                query=s.sections[section]['key']
                break

        recentlyAdded = p.recentlyAdded(section=query, params="X-Plex-Container-Start=0&X-Plex-Container-Size=5")

        return render_template('plex/recent.html',
            title='albums',
            server=s,
            albums=recentlyAdded['MediaContainer'],
        )
    except Exception as e:
        return error(e)


@app.route('/xhr/plex_recent_photos/')
def xhr_recent_photos():
    try:
        s = getActiveServer()
        p = PlexLibrary(s.ip)
        query = None
        for section in s.sections:
            if 'photo' in s.sections[section]['type']:
                query=s.sections[section]['key']
                break

        recentlyAdded = p.recentlyAdded(section=query, params="X-Plex-Container-Start=0&X-Plex-Container-Size=5")

        return render_template('plex/recent.html',
            title='photos',
            server=s,
            photos=recentlyAdded['MediaContainer'],
        )
    except Exception as e:
        return error(e)


@app.route('/xhr/plex/section/<int:id>/')
def xhr_plex_section(id):
    try:
        s = getActiveServer()
        p = PlexLibrary(s.ip)
        items = p.getSection(id)
        return render_template('plex/library_section.html',
            server=s,
            media=items['MediaContainer'],
            address=safeAddress(s.ip),
        )
    except Exception as e:
        return error(e)


@app.route('/xhr/plex/refresh/<int:id>/')
def xhr_plex_refresh(id):
    try:
        s = getActiveServer()
        p = PlexLibrary(s.ip)
        p = p.refreshSection(id)
        return jsonify({'success': True, 'response': p})
    except:
        return jsonify({'success': False})


@app.route('/xhr/plex/img/')
@app.route('/xhr/plex/img/<path:path>/')
@requires_auth
def xhr_plex_image(path=''):
    if path is '':
        img = RUNDIR + 'static/images/applications/Plex.png'
        return send_file(img, mimetype='image/jpeg')

    server = getActiveServer()

    url = 'http://%s:32400/%s' % (server.ip, path)

    username = get_setting_value('myPlex_username')
    password = get_setting_value('myPlex_password')
    try:
        request = urllib2.Request(url)
        base64string = base64.encodestring('%s:%s' % (username, password)).replace('\n', '')
        request.add_header("Authorization", "Basic %s" % base64string)

        img = StringIO.StringIO(urllib2.urlopen(request).read())
        return send_file(img, mimetype='image/jpeg')
    except:
        img = RUNDIR + 'static/images/applications/Plex.png'
        return send_file(img, mimetype='image/jpeg')


@app.route('/xhr/plex/now_playing/')
def xhr_plex_now_playing():
    try:
        s = getActiveServer()
        p = PlexLibrary(s.ip)
        clients = p.nowPlaying()
        if int(clients['MediaContainer']['@size']) == 0:
            return jsonify({ 'playing': False })

        return render_template('plex/now_playing.html',
            server=s,
            clients=clients['MediaContainer'],
        )
    except Exception as e:
        return error(e)


