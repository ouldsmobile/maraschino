from flask import render_template
from maraschino import app, logger
from maraschino.tools import get_setting_value
from maraschino.models import PlexServer as dbserver

from plexLib import PlexLibrary, PlexServer
from xmltodict import xmltodict


def safeAddress(ip):
    return "http://%s:32400" % (ip)


def error(e):
    global plex
    return render_template('plex.html',
        error=True,
        exception=e
    )


def plex_log(msg, level):
    logger.log(msg, level)


@app.route('/xhr/plex/')
def plex():
    try:
        s = dbserver.query.filter(dbserver.owned == 1).first()
        if s is not None:     
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
        sections = p.sections()
        return render_template('plex/on_deck.html',
            machineId=s.machineIdentifier,
            video=onDeck['MediaContainer'],
            address=safeAddress(s.ip),
            sections=sections['MediaContainer'],
        )
    except Exception as e:
        return error(e)


@app.route('/xhr/plex/recentlyAdded/')
def xhr_recently_added():
    try:
        s = dbserver.query.order_by(dbserver.id).first()
        p = PlexLibrary(s.ip)
        recentlyAdded = p.recentlyAdded()
        return render_template('plex/on_deck.html',
            machineId=s.machineIdentifier,
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
        sections = p.sections()
        return render_template('plex/library_section.html',
            machineId=s.machineIdentifier,
            video=items['MediaContainer'],
            address=safeAddress(s.ip),
            sections=sections['MediaContainer'],
        )
    except Exception as e:
        return error(e)
