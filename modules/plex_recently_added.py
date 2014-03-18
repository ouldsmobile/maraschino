from flask import render_template
from maraschino import app, logger
from maraschino.tools import get_setting_value

from plex import PlexLibrary
from xmltodict import xmltodict


def plex_address():
    return 'http://%s:%s' %(get_setting_value('plex_ip'), get_setting_value('plex_port'))


@app.route('/xhr/plex_on_deck/')
@app.route('/xhr/plex/onDeck/')
def xhr_on_deck():
    try:
        p = PlexLibrary(get_setting_value('plex_ip'), get_setting_value('plex_port'))
        onDeck = p.onDeck()
        sections = p.sections()
        return render_template('plex_on_deck.html',
            machineId=p.machineId(get_setting_value('myPlex_username'), get_setting_value('myPlex_password')),
            video=onDeck['MediaContainer'],
            address=plex_address(),
            sections=sections['MediaContainer'],
        )
    except Exception as e:
        return render_template('plex_on_deck.html',
            error=True,
            address=plex_address(),
            exception=e
        )


@app.route('/xhr/plex/recentlyAdded/')
def xhr_recently_added():
    try:
        p = PlexLibrary(get_setting_value('plex_ip'), get_setting_value('plex_port'))
        recentlyAdded = p.recentlyAdded()
        return render_template('plex_on_deck.html',
            machineId=p.machineId(get_setting_value('myPlex_username'), get_setting_value('myPlex_password')),
            video=recentlyAdded['MediaContainer'],
            address=plex_address(),
        )
    except Exception as e:
        return render_template('plex_on_deck.html',
            error=True,
            address=plex_address(),
            exception=e
        )


@app.route('/xhr/plex/section/<int:id>/')
def xhr_plex_section(id):
    try:
        p = PlexLibrary(get_setting_value('plex_ip'), get_setting_value('plex_port'))
        items = p.getSection(id)
        sections = p.sections()
        return render_template('plex/plex_section.html',
            machineId=p.machineId(get_setting_value('myPlex_username'), get_setting_value('myPlex_password')),
            video=items['MediaContainer'],
            address=plex_address(),
            sections=sections['MediaContainer'],
        )
    except Exception as e:
        return render_template('plex_on_deck.html',
            error=True,
            address=plex_address(),
            exception=e,
        )
