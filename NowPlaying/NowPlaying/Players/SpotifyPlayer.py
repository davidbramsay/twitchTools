from .Player import BasePlayer
import spotipy
from spotipy.oauth2 import SpotifyOAuth


class SpotifyPlayer(BasePlayer):
    spotify = None
    cfg = dict()

    def __init__(self, cfg):
        self.cfg = cfg['spotify']

        client_id = self.cfg['client_id']
        client_secret = self.cfg['client_secret']

        scope = 'user-read-currently-playing'
        self.spotify = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                scope=scope,
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri='http://localhost:8088'
            )
        )

    def update(self) -> None:
        t = self.spotify.current_user_playing_track()  # None if no spotify session

        if not t or not t['is_playing']:  # get_string depends on whether or not the song is playing
            self.is_playing = False
            return
        else:
            self.is_playing = True

        # Artists is an array, but we're only interested in the name property,
        # so we loop through them and add it to an array
        artists = []
        for artist in t['item']['artists']:
            artists.append(artist['name'])

        self.track.author = ', '.join(artists)
        self.track.song = t['item']['name']
