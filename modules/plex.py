from flask import render_template
from maraschino import app, logger
from maraschino.tools import get_setting_value, requires_auth
from maraschino.models import PlexServer as dbserver

from plexLib import PlexLibrary, PlexServer
from xmltodict import xmltodict


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
        s = dbserver.query.filter(dbserver.owned == 1).first()
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
        s = dbserver.query.filter(dbserver.owned == 1).first()
        p = PlexLibrary(s.ip)
        onDeck = p.onDeck()
        return render_template('plex/on_deck.html',
            server=s,
            video=onDeck['MediaContainer'],
            address=safeAddress(s.ip),
        )
    except Exception as e:
        return error(e)


@app.route('/xhr/plex/recentlyAdded/')
def xhr_recently_added():
    try:
        s = dbserver.query.order_by(dbserver.id).first()
        p = PlexLibrary(s.ip)
        recentlyAdded = p.recentlyAdded()
        return render_template('plex/recently_added.html',
            server=s,
            video=recentlyAdded['MediaContainer'],
            address=safeAddress(s.ip),
        )
    except Exception as e:
        return error(e)


@app.route('/xhr/plex/section/<int:id>/')
def xhr_plex_section(id):
    try:
        s = dbserver.query.order_by(dbserver.id).first()
        p = PlexLibrary(s.ip)
        items = p.getSection(id)
        return render_template('plex/library_section.html',
            server=s,
            video=items['MediaContainer'],
            address=safeAddress(s.ip),
        )
    except Exception as e:
        return error(e)
