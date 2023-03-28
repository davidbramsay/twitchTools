import atexit
import yaml
import codecs
from .Players.SpotifyPlayer import SpotifyPlayer
from .Players.GooglePlayMusicDesktopPlayer import GooglePlayMusicDesktopPlayer
from wx import adv
import wx
from .threaded import InfiniteTimer
from os import path
import sys


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # noinspection PyUnresolvedReferences
        base_path = sys._MEIPASS
    except:
        base_path = path.abspath(".")

    return path.join(base_path, relative_path)


try:
    with open('config.yml', 'r') as yml_file:
        cfg = yaml.load(yml_file, Loader=yaml.SafeLoader)
except (OSError, yaml.YAMLError):
    print('Error opening or loading config.yml')
    with open('error.log', 'w+') as error_file:
        error_file.write('Error opening or loading config.yml\n')
    quit()

output_file = cfg['settings']['output_file']


@atexit.register
def clear_track_file() -> None:
    with open(output_file, 'w') as f:
        f.write('')


def create_menu_item(menu, label, func):
    """ Helper function """
    item = wx.MenuItem(menu, -1, label)
    menu.Bind(wx.EVT_MENU, func, id=item.GetId())
    menu.Append(item)
    return item


class TaskBarIcon(wx.adv.TaskBarIcon):
    TRAY_TOOLTIP = 'Now Playing'
    TRAY_ICON = resource_path('icon.png')  # 'icon.png'

    players: dict
    mapping: dict = dict()
    spotify_menu_item = None
    google_menu_item = None

    def __init__(self, frame, player_app):
        self.frame = frame
        self.app = player_app
        super(TaskBarIcon, self).__init__()
        self.set_icon(self.TRAY_ICON)
        self.Bind(wx.adv.EVT_TASKBAR_LEFT_DOWN, self.on_left_down)  # Icon doesn't show without it ?
        self.players = {
            'spotify': {'label': 'Spotify'},
            'google_play': {'label': 'Google Play Music'}
        }

    def CreatePopupMenu(self):
        menu = wx.Menu()

        player_menu = wx.Menu()

        for name, ply in self.players.items():
            p = player_menu.AppendRadioItem(-1, ply['label'])
            if name == self.app.current_player:
                player_menu.Check(p.GetId(), True)
            self.mapping[p.GetId()] = name

        menu.AppendSubMenu(player_menu, 'Player')
        self.Bind(wx.EVT_MENU, self.set_player)

        menu.AppendSeparator()
        create_menu_item(menu, 'Exit', self.on_exit)
        return menu

    def on_left_down(self, event):
        pass

    def set_player(self, event):
        if event.GetId() in self.mapping:
            self.app.current_player = self.mapping[event.GetId()]
            self.app.update_player(self.app.current_player)

    def set_icon(self, icon_path):
        icon = wx.Icon(icon_path)
        self.SetIcon(icon, self.TRAY_TOOLTIP)

    def on_exit(self, event):
        wx.CallAfter(self.Destroy)
        self.frame.Close()


class App(wx.App):
    player_timer = None
    player = None
    current_player = 'spotify'

    def OnInit(self):
        self.player = SpotifyPlayer(cfg)

        frame = wx.Frame(None)
        self.SetTopWindow(frame)
        TaskBarIcon(frame, self)

        self.player_loop()
        interval = cfg['settings']['refresh_rate']  # seconds
        self.player_timer = InfiniteTimer(interval, self.player_loop)
        self.player_timer.start()

        return True

    def update_player(self, new_player) -> None:
        if new_player == 'spotify':
            self.player = SpotifyPlayer(cfg)
            self.current_player = new_player
        elif new_player == 'google_play':
            self.player = GooglePlayMusicDesktopPlayer()
            self.current_player = new_player

    def player_loop(self) -> None:
        self.player.update()

        # Close thread and exit application
        if self.player.exit:
            self.player_timer.cancel()
            self.ExitMainLoop()
            return

        track_string = self.player.get_string()
        with codecs.open(output_file, 'w', 'utf-8') as f:
            f.write(track_string)

    def OnExit(self):
        # Double checking, not sure if it helps
        if self.player_timer is not None:
            self.player_timer.cancel()

        return super().OnExit()


def main():
    app = App()
    app.MainLoop()
