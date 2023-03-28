from .Player import BasePlayer
from os import path
import json
import platform
import codecs


class GooglePlayMusicDesktopPlayer(BasePlayer):

    def read_file(self) -> None:
        store = path.expandvars(r'%APPDATA%\Google Play Music Desktop Player\json_store')
        input_file = store + r'\playback.json'

        try:
            with codecs.open(input_file, 'r', 'utf-8') as f:
                data = json.load(f, encoding='utf-8')
                self.is_playing = data['playing']
                self.track.author = data['song']['artist']
                self.track.song = data['song']['title']
        except FileNotFoundError:
            print('Google Play Music Desktop Player JSON file not found')
            self.exit = True

    def update(self) -> None:
        if platform.system() == 'Windows':
            self.read_file()
        else:
            print('Unsupported OS')  # Implement WebSocket as fallback?
            self.exit = True
