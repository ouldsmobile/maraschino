from flask import render_template
from maraschino import app, logger
from maraschino.tools import get_setting_value
from plex import PlexLibrary


def plex_address():
    return 'http://%s:%s' %(get_setting_value('plex_ip'), get_setting_value('plex_port'))


@app.route('/xhr/plex_on_deck/')
@app.route('/xhr/plex/onDeck/')
def xhr_on_deck():
    try:
        p = PlexLibrary(get_setting_value('plex_ip'), get_setting_value('plex_port'))
        p = p.onDeck()
        return render_template('plex_on_deck.html',
            p=p['_children'],
            address=plex_address()
        )
    except:
        return render_template('plex_on_deck.html',
            error=True,
            address=plex_address
        )