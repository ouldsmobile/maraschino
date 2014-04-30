from flask import render_template, jsonify, send_file
from jinja2.filters import FILTERS
from maraschino import app, logger, RUNDIR, WEBROOT
from maraschino.tools import requires_auth, get_setting_value
from maraschino.models import PlexServer
from plexLib import Server, Client
import StringIO


def error(e, module='plex'):
    return render_template('plex/error.html',
        error=True,
        msg=e,
        module=module,
    )


def plex_log(msg, level='INFO'):
    logger.log('Plex :: %s'%(msg), level)


def plex_image(path):
    return '%s/xhr/plex/img%s' % (WEBROOT, path)

FILTERS['plex_img'] = plex_image


def miliseconds(ms):
    hours, minutes = divmod(int(ms)/60000, 60)
    if hours is 0:
        return '%i min' % (minutes)
    if hours is 1 and minutes is 0:
        return '60 mins'
    return '%i hr %i min' % (hours, minutes)

FILTERS['miliseconds'] = miliseconds


@app.route('/xhr/plex/')
def plex():
    return xhr_on_deck()


@app.route('/xhr/plex/onDeck/')
def xhr_on_deck():
    try:
        server = PlexServer.query.filter(PlexServer.id == get_setting_value('active_server')).first()
        p = Server(ip=server.localAddresses, token=server.token)
        onDeck = p.onDeck()

        return render_template('plex/on_deck.html',
            server=server,
            video=onDeck,
        )
    except Exception as e:
        return error(e)


@app.route('/xhr/plex_recent_<title>/')
@app.route('/xhr/plex_recent_<title>/<int:start>/<int:size>/')
@app.route('/xhr/plex_recent_<title>/<int:id>/')
@app.route('/xhr/plex_recent_<title>/<int:id>/<int:start>/<int:size>/')
def xhr_recent_movies(title, id=None, start=0, size=5):
    if 'movies' in title:
        type = 'movie'
    elif 'episodes' in title:
        type = 'show'
    elif 'albums' in title:
        type = 'artist'
    elif 'photos' in title:
        type = 'photo'

    try:
        server = PlexServer.query.filter(PlexServer.id == get_setting_value('active_server')).first()
        p = Server(ip=server.localAddresses, token=server.token)
        preferred = server.sections[type]['preferred']
        if id is None:
            # if no explicit id, try to get preferred id
            id = preferred
            # if preferred id is 0 there is no preferred, select the first one in db
            if id is 0:
                for section in server.sections:
                    if type in section:
                        id=server.sections[section]['sections'][0]['key']
                        break

        # this might fail if preffered section id no longer exists so default back to one in db
        try:
            recentlyAdded = p.recentlyAdded(id=id, start=start, size=size)
        except:
            for section in server.sections:
                if type in section:
                    id=server.sections[section]['sections'][0]['key']
                    break
            recentlyAdded = p.recentlyAdded(id=id, start=start, size=size)

        # perform rounding of rating to one decimal place for movies template
        if 'movies' in title:
            for movie in recentlyAdded['Video']:
                try:
                    movie['rating'] = round(float(movie['rating']), 1)
                except:
                    pass
    except Exception, e:
        return error(e, module="plex_recent_%s" % title)


    return render_template('plex/recent.html',
        type=type,
        id=int(id),
        start=start,
        title=title,
        server=server,
        items=recentlyAdded,
        preferred=preferred,
    )


@app.route('/xhr/plex/section/<int:id>/')
def xhr_plex_section(id):
    server = PlexServer.query.filter(PlexServer.id == get_setting_value('active_server')).first()
    p = Server(ip=server.localAddresses, token=server.token)
    items = p.section(id)
    return render_template('plex/library_section.html',
        server=server,
        media=items,
    )


@app.route('/xhr/plex/sections/<label>/')
def xhr_plex_sections(label):
    try:
        server = PlexServer.query.filter(PlexServer.id == get_setting_value('active_server')).first()
        sections = server.sections[label]
        return render_template('plex/library_list.html',
            server=server,
            sections=sections,
        )
    except Exception as e:
        return error(e)


@app.route('/xhr/plex/refresh/<int:id>/')
def xhr_plex_refresh(id):
    try:
        server = PlexServer.query.filter(PlexServer.id == get_setting_value('active_server')).first()
        p = Server(ip=server.localAddresses, token=server.token)
        p = p.refreshSection(id)
        return jsonify({'success': p})
    except:
        return jsonify({'success': False})


@app.route('/xhr/plex/img/')
@app.route('/xhr/plex/img/<path:path>/')
@app.route('/xhr/plex/img/<path:path>/<int:width>/<int:height>/')
@requires_auth
def xhr_plex_image(path='', width=0, height=0):
    if path is '':
        img = RUNDIR + 'static/images/applications/Plex.png'
        return send_file(img, mimetype='image/jpeg')

    server = PlexServer.query.filter(PlexServer.id == get_setting_value('active_server')).first()
    p = Server(ip=server.localAddresses, token=server.token)
    if width == 0 or height == 0:
        image = p.image(path)
    else:
        image = p.image(path, width=width, height=height)

    try:
        img = StringIO.StringIO(image)
        return send_file(img, mimetype='image/jpeg')
    except:
        img = RUNDIR + 'static/images/applications/Plex.png'
        return send_file(img, mimetype='image/jpeg')


@app.route('/xhr/plex/now_playing/')
def xhr_plex_now_playing():
    try:
        server = PlexServer.query.filter(PlexServer.id == get_setting_value('active_server')).first()
        p = Server(ip=server.localAddresses, token=server.token)
        clients = p.nowPlaying()
        if int(clients['size']) == 0:
            return jsonify(playing=False)

        videos = None
        songs = None
        photos = None
        try:
            videos = clients['Video']
        except:
            pass

        try:
            songs = clients['Track']
        except:
            pass

        try:
            photos = clients['Photo']
        except:
            pass

        return render_template('plex/now_playing.html',
            server=server,
            videos=videos,
            songs=songs,
            photos=photos,
        )
    except:
        return jsonify(playing=False, reason='Error')


@app.route('/xhr/plex/client/<machineIdentifier>/<command>/')
def xhr_plex_client(machineIdentifier, command):
    try:
        server = PlexServer.query.filter(PlexServer.id == get_setting_value('active_server')).first()
        p = Server(ip=server.localAddresses, token=server.token)
        clients = p.clients()
        for client in clients:
            if client['machineIdentifier'] == machineIdentifier:
                player = Client(ip=client['address'], port=client['port'], token=get_setting_value('myPlex_token'))
                break


        response = player.play()
        if 'OK' in response:
            return jsonify(success=True)
    except:
        return jsonify(success=False)

@app.route('/xhr/plex/metadata/<int:id>/')
@app.route('/xhr/plex/metadata/<path:id>/')
def plex_metadata(id):
    server = PlexServer.query.filter(PlexServer.id == get_setting_value('active_server')).first()
    p = Server(ip=server.localAddresses, token=server.token)
    item=p.metadata(id)
    return render_template('plex/metadata.html',
        server=server,
        item=item
    )
