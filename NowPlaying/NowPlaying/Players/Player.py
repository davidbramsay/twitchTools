import abc
from abc import ABC
from dataclasses import dataclass


@dataclass
class Track:
    author: str = ''
    song: str = ''


class BasePlayer(ABC):
    is_playing: bool = False
    track: Track = Track
    exit: bool = False

    def get_string(self) -> str:
        t = self.track

        if self.is_playing is False:
            return ''

        return '{0} - {1}'.format(t.author, t.song)

    @abc.abstractmethod
    def update(self) -> None:
        pass


