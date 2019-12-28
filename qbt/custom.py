import datetime
import logging

# noinspection PyPackageRequirements
from qbittorrent import Client

from utils import u
from utils import kb
from config import config

logger = logging.getLogger(__name__)


STATES_DICT = {
    'error': 'error',
    'pausedUP': 'paused - download finished',
    'pausedDL': 'paused - download not finished',
    'queuedUP': 'queued for upload',
    'queuedDL': 'queued for download',
    'forcedDL': 'forced download',
    'forcedUP': 'forced upload',
    'uploading': 'uploading',
    'stalledUP': 'stalled (uploading)',
    'checkingUP': 'checking file (download completed)',
    'checkingDL': 'checking file (downloading)',
    'downloading': 'downloading',
    'stalledDL': 'stalled (downloading)',
    'metaDL': 'fetching metadata'
}

ATTR_FORMATTING = {
    'state': lambda state: STATES_DICT.get(state, state),
    'size': lambda size: u.get_human_readable(size),  # already a string apparently
    'total_size': lambda size: u.get_human_readable(size),
    'dlspeed': lambda size: u.get_human_readable(size),  # no need for this, it's already a string
    'dl_speed': lambda size: u.get_human_readable(size),
    'upspeed': lambda size: u.get_human_readable(size),  # no need for this, it's already a string
    'up_speed': lambda size: u.get_human_readable(size),
    'progress': lambda decimal_progress: round(decimal_progress * 100),
    'eta': lambda seconds: str(datetime.timedelta(seconds=seconds)), # apparently it's already a string?
    'force_start': lambda f_start: 'yes' if f_start else 'no'
}

TORRENT_STRING = """• <code>{name}</code>
  {progress_bar} {progress}%
  <b>state</b>: {state}
  <b>size</b>: {size}
  <b>dl/up speed</b>: {dlspeed}/s, {upspeed}/s
  <b>leechs/seeds</b> {num_leechs}/{num_seeds}
  <b>eta</b>: {eta}
  <b>priority</b>: {priority}
  <b>force start</b>: {force_start}"""


# noinspection PyUnresolvedReferences
class Torrent:
    def __init__(self, qbt, torrent_dict):
        self._torrent_dict = torrent_dict
        self._qbt = qbt

        self.refresh_properties(refresh_torrent_dict=False)

        self.actions_keyboard = kb.actions_markup(self.hash)

    def short_markup(self, *args, **kwargs):
        return kb.short_markup(self.hash, *args, **kwargs)
    
    def dict(self):
        return self._torrent_dict

    def refresh_properties(self, refresh_torrent_dict=True):
        if refresh_torrent_dict:
            logger.debug('refreshing torrent dict')
            self._torrent_dict = self._qbt.torrent(self.hash).dict()
        
        for key, val in self._torrent_dict.items():
            setattr(self, key, val)

    def __getitem__(self, item):
        return getattr(self, item)

    def string(self, refresh_properties=False):
        if refresh_properties:
            self.refresh_properties(refresh_torrent_dict=True)
        
        return TORRENT_STRING.format(**self._torrent_dict)

    def pause(self):
        return self._qbt.pause(self.hash)

    def resume(self):
        return self._qbt.resume(self.hash)

    def toggle_force_start(self, value=True):
        # 'force_start' method name cannot be used because it is already a property
        return self._qbt.force_start([self.hash], value=value)

    def increase_priority(self):
        return self._qbt.increase_priority([self.hash])

    def max_priority(self):
        return self._qbt.set_max_priority([self.hash])

    def recheck(self):
        return self._qbt.recheck([self.hash])

    def trackers(self):
        return self._qbt.get_torrent_trackers(self.hash)

    def delete(self, with_files=False):
        if with_files:
            return self._qbt.delete_permanently([self.hash])
        else:
            return self._qbt.delete([self.hash])


class CustomClient(Client):
    def __init__(self, url, bot_username):
        self._bot_username = bot_username
        super(CustomClient, self).__init__(url=url)

    def _polish_torrent(self, torrent):
        if 'progress' in torrent:
            torrent['eta'] = 0 if torrent['progress'] == 1 else torrent['eta']  # set eta = 0 for completed torrents
            torrent['progress_bar'] = u.build_progress_bar(torrent['progress'])
        if 'hash' in torrent:
            # torrent['resume_deeplink'] = 'https://t.me/{}?start=resume{}'.format(self._bot_username, torrent['hash'])
            # torrent['pause_deeplink'] = 'https://t.me/{}?start=pause{}'.format(self._bot_username, torrent['hash'])
            torrent['manage_deeplink'] = 'https://t.me/{}?start=manage{}'.format(self._bot_username, torrent['hash'])
            torrent['info_deeplink'] = 'https://t.me/{}?start=info{}'.format(self._bot_username, torrent['hash'])

        torrent['short_name'] = torrent['name'] if len(torrent['name']) < 81 else torrent['name'][:81] + '...'

        return {k: ATTR_FORMATTING.get(k, lambda x: x)(v) for k, v in torrent.items()}

    def torrents(self, **kwargs):
        torrents = super(CustomClient, self).torrents(**kwargs) or []
        return [Torrent(self, self._polish_torrent(torrent)) for torrent in torrents]

    # noinspection PyUnresolvedReferences
    def torrent(self, torrent_hash):
        torrents = self.torrents(filter='all')

        for torrent in torrents:
            if torrent.hash == torrent_hash:
                return torrent

    # noinspection PyUnresolvedReferences
    def filter(self, query):
        filtered = list()

        for torrent in self.torrents(filter='all'):
            if query in torrent.name.lower():
                filtered.append(torrent)

        return filtered

    def get_schedule(self):
        p = self.preferences()

        if not p['scheduler_enabled']:
            return None

        return dict(
            from_hour='{:0>2}:{:0>2}'.format(p['schedule_from_hour'], p['schedule_from_min']),
            to_hour='{:0>2}:{:0>2}'.format(p['schedule_to_hour'], p['schedule_to_min']),
            days=str(p['scheduler_days'])
        )

    def get_alt_speed(self):
        p = self.preferences()

        return dict(
            status=bool(self.get_alternative_speed_status()),
            alt_dl_limit=p['alt_dl_limit'] if p['alt_dl_limit'] > -1 else None,
            alt_up_limit=p['alt_up_limit'] if p['alt_up_limit'] > -1 else None
        )

    def get_speed(self):
        tinfo = self.global_transfer_info

        return (
            u.get_human_readable(tinfo['dl_info_speed']),
            u.get_human_readable(tinfo['up_info_speed'])
        )



class OfflineClient:
    """
    We use this calss when we can't connect to qbittorrent, so the bot would still run and let us
    use all the other methods that do not require to be connected to qbittoreent's webAPI
    """

    def __init__(self):
        pass

    def __getattr__(self, name):
        def internal(*args, **kwargs):
            logger.debug('OfflineClient method called: %s', name)
            self._raise()

        return internal()

    def _raise(self):
        raise ConnectionError('cannot connect to qbittorrent ({})'.format(config.qbittorrent.url))
