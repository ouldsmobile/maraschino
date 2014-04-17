from flask import render_template, jsonify, send_file
from jinja2.filters import FILTERS
from maraschino import app, logger, RUNDIR, WEBROOT
from maraschino.tools import requires_auth, get_setting_value
from maraschino.models import PlexServer as dbserver
from plexLib import PlexServer
import StringIO


def error(e, module='plex'):
    return render_template('plex/error.html',
        error=True,
        msg=e,
        module=module,
    )


def plex_log(msg, level='INFO'):
    logger.log('Plex :: %s'%(msg), level)


def getActiveServer():
    selected_server = get_setting_value('active_server')
    server = dbserver.query.filter(dbserver.id == selected_server).first()
    return PlexServer(ip=server.localAddresses, token=server.token), server


def plex_image(path):
    return '%s/xhr/plex/img%s' % (WEBROOT, path)

FILTERS['plex_img'] = plex_image


@app.route('/xhr/plex/')
def plex():
    return xhr_on_deck()


@app.route('/xhr/plex/onDeck/')
def xhr_on_deck():
    try:
        p, s = getActiveServer()
        onDeck = p.onDeck()

        return render_template('plex/on_deck.html',
            server=s,
            video=onDeck['MediaContainer'],
        )
    except Exception as e:
        return error(e)


@app.route('/xhr/plex_recent_<title>/')
@app.route('/xhr/plex_recent_<title>/<int:id>/')
def xhr_recent_movies(title, id=None):
    if 'movies' in title:
        type = 'movie'
    elif 'episodes' in title:
        type = 'show'
    elif 'albums' in title:
        type = 'artist'
    elif 'photos' in title:
        type = 'photo'

    try:
        p, s = getActiveServer()
        if id is None:
            for section in s.sections:
                if type in section:
                    id=s.sections[section]['sections'][0]['key']
                    break


        recentlyAdded = p.recentlyAdded(section=id, params="X-Plex-Container-Start=0&X-Plex-Container-Size=5")

        if 'movies' in title:
            for movie in recentlyAdded['MediaContainer']['Video']:
                try:
                    movie['@rating'] = round(float(movie['@rating']), 1)
                except:
                    pass

        return render_template('plex/recent.html',
            type=type,
            id=int(id),
            title=title,
            server=s,
            items=recentlyAdded['MediaContainer'],
        )
    except Exception as e:
        plex_log(e, 'ERROR')
        return error(e, module="plex_recent_movies")


@app.route('/xhr/plex/section/<int:id>/')
def xhr_plex_section(id):
    try:
        p, s = getActiveServer()
        items = p.getSection(id)
        return render_template('plex/library_section.html',
            server=s,
            media=items['MediaContainer'],
        )
    except Exception as e:
        return error(e)


@app.route('/xhr/plex/sections/<label>/')
def xhr_plex_sections(label):
    try:
        p, s = getActiveServer()
        sections = s.sections[label]
        return render_template('plex/library_list.html',
            server=s,
            sections=sections,
        )
    except Exception as e:
        return error(e)


@app.route('/xhr/plex/refresh/<int:id>/')
def xhr_plex_refresh(id):
    try:
        p, server = getActiveServer()
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

    p, server = getActiveServer()

    try:
        img = StringIO.StringIO(p.image(path))
        return send_file(img, mimetype='image/jpeg')
    except:
        img = RUNDIR + 'static/images/applications/Plex.png'
        return send_file(img, mimetype='image/jpeg')


@app.route('/xhr/plex/now_playing/')
def xhr_plex_now_playing():
    try:
        p, s = getActiveServer()
        clients = p.nowPlaying()
        if int(clients['MediaContainer']['@size']) == 0:
            return jsonify({ 'playing': False })

        videos = None
        songs = None
        photos = None
        try:
            videos = clients['MediaContainer']['Video']
        except:
            pass

        try:
            songs = clients['MediaContainer']['Track']
        except:
            pass

        try:
            photos = clients['MediaContainer']['Photo']
        except:
            pass

        return render_template('plex/now_playing.html',
            server=s,
            videos=videos,
            songs=songs,
            photos=photos,
        )
    except:
        return jsonify({'playing': False})


