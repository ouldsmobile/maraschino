from flask import render_template
from maraschino import app, logger
from maraschino.tools import get_setting_value
from jinja2.filters import FILTERS

from plex import PlexLibrary
from xmltodict import xmltodict


def plex_address():
    return 'http://%s:%s' %(get_setting_value('plex_ip'), get_setting_value('plex_port'))


def formatEpisode(value):
    print "%d" % (value)


FILTERS['formatNumber'] = formatEpisode

@app.route('/xhr/plex_on_deck/')
@app.route('/xhr/plex/onDeck/')
def xhr_on_deck():
    try:
        p = PlexLibrary(get_setting_value('plex_ip'), get_setting_value('plex_port'))
        onDeck = p.onDeck()
        return render_template('plex_on_deck.html',
            machineId=p.machineId(get_setting_value('myPlex_username'), get_setting_value('myPlex_password')),
            video=onDeck['MediaContainer'],
            address=plex_address(),
        )
    except Exception as e:
        return render_template('plex_on_deck.html',
            error=True,
            address=plex_address(),
            exception=e
        )