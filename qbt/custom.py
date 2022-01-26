import datetime
import logging
import math
from typing import Optional, List

# noinspection PyPackageRequirements
from qbittorrent import Client

from utils import u
from utils import kb
from config import config

logger = logging.getLogger(__name__)


# https://github.com/qbittorrent/qBittorrent/wiki/WebUI-API-(qBittorrent-4.1)#get-torrent-list
TORRENTS_CATEGORIES = (
    'all',
    'downloading',
    'seeding',
    'completed',
    'paused',
    'active',
    'inactive',
    'resumed',
    'stalled',
    'stalled_uploading',
    'stalled_downloading',
    'errored',
)

STATES_DICT = {
    'error': 'error',
    'missingFiles': 'missing files',
    'uploading': 'uploading',
    'pausedUP': 'paused (download finished)',
    'queuedUP': 'queued for upload',
    'stalledUP': 'stalled (uploading)',
    'checkingUP': 'checking file (download completed)',
    'forcedUP': 'forced upload',
    'allocating': 'allocating disk space',
    'downloading': 'downloading',
    'metaDL': 'fetching metadata',
    'pausedDL': 'paused (download not finished)',
    'queuedDL': 'queued for download',
    'stalledDL': 'stalled (downloading)',
    'checkingDL': 'checking file (downloading)',
    'forcedDL': 'forced download',
    'checkingResumeData': 'startup: checking data',
    'moving': 'moving',
    'unknown': 'unknown status'
}

# https://github.com/qbittorrent/qBittorrent/wiki/WebUI-API-(qBittorrent-4.1)#get-torrent-list
# https://github.com/qbittorrent/qBittorrent/wiki/WebUI-API-(qBittorrent-4.1)#get-torrent-generic-properties
NEW_ATTRS = {
    'state_pretty': lambda t: STATES_DICT.get(t['state'], t['state']),
    'size_pretty': lambda t: u.get_human_readable(t['total_size']),  # already a string apparently
    'dl_speed_pretty': lambda t: u.get_human_readable(t['dl_speed']),
    'up_speed_pretty': lambda t: u.get_human_readable(t['up_speed']),
    'dlspeed_pretty': lambda t: u.get_human_readable(t['dlspeed']),
    'upspeed_pretty': lambda t: u.get_human_readable(t['upspeed']),
    'name_escaped': lambda t: u.html_escape(t['name']),
    'generic_speed_pretty': lambda t: u.get_human_readable(t['generic_speed']),
    'progress_pretty': lambda t: math.floor(t['progress'] * 100),  # eg. 99.9% should be rounded to 99%
    'eta_pretty': lambda t: str(datetime.timedelta(seconds=t['eta'])),  # apparently it's already a string?
    'time_elapsed_pretty': lambda t: str(datetime.timedelta(seconds=t['time_elapsed'])),
    'force_start_pretty': lambda t: 'yes' if t['force_start'] else 'no',
    'share_ratio_rounded': lambda t: round(t['ratio'], 2),
    'dl_limit_pretty': lambda t: 'no limit' if t['dl_limit'] == -1 else u.get_human_readable(t['dl_limit']),
    'auto_tmm_string': lambda t: 'yes' if t['auto_tmm'] else 'no',
}

TORRENT_STRING = """<code>{name_escaped}</code>
  {progress_bar} {progress_pretty}%
  <b>state</b>: {state_pretty}
  <b>size</b>: {size_pretty}
  <b>dl/up speed</b>: {dl_speed_pretty}/s, {up_speed_pretty}/s
  <b>dl speed limit</b>: {dl_limit_pretty}
  <b>peers</b>: {peers} connected ({peers_total} in the swarm)
  <b>seeds</b>: {seeds} connected ({seeds_total} in the swarm)
  <b>seeds (alternative values)</b>: {num_seeds} connected ({num_complete} in the swarm)
  <b>leechers</b>: {num_leechs} connected ({num_incomplete} in the swarm)
  <b>connections</b>: {nb_connections}
  <b>share ratio</b>: {share_ratio_rounded} (max: {max_ratio})
  <b>eta</b>: {eta_pretty}
  <b>elapsed</b>: {time_elapsed_pretty}
  <b>category</b>: {category}
  <b>force start</b>: {force_start_pretty}
  <b>tags</b>: <code>{tags}</code>
  <b>auto torrent management</b>: {auto_tmm_string}
  
  <code>infohash:{hash}</code>
  [<a href="{info_deeplink}">info</a>]"""


class Torrent:
    def __init__(self, qbt, torrent_dict: dict, get_torrent_generic_properties: bool = False):
        self._torrent_dict: dict = torrent_dict
        self._qbt: CustomClient = qbt
        self.hash = self._torrent_dict['hash']

        self.refresh(
            get_torrent_generic_properties=get_torrent_generic_properties,
            refresh_torrent_dict=False
        )

        self.actions_keyboard = kb.actions_markup(self.hash)

    def refresh(self, refresh_torrent_dict: bool = True, get_torrent_generic_properties: bool = False):
        if refresh_torrent_dict:
            self._torrent_dict = self._qbt.torrent(self.hash, get_torrent_generic_properties=False).dict()

        if get_torrent_generic_properties:
            self.get_additional_torrent_properties()

        self._enrich_torrent_dict()

    def get_additional_torrent_properties(self):
        additional_properties = self._qbt.get_torrent(self.hash)
        if additional_properties:
            for key, val in additional_properties.items():
                if key in self._torrent_dict:
                    continue

                self._torrent_dict[key] = val

    def _enrich_torrent_dict(self):
        if 'progress' in self._torrent_dict:
            self._torrent_dict['eta'] = 0 if self._torrent_dict['progress'] == 1 else self._torrent_dict['eta']  # set eta = 0 for completed torrents
            self._torrent_dict['progress_bar'] = u.build_progress_bar(self._torrent_dict['progress'])
        if 'hash' in self._torrent_dict:
            self._torrent_dict['manage_deeplink'] = 'https://t.me/{}?start=manage{}'.format(
                self._qbt._bot_username,
                self._torrent_dict['hash']
            )
            self._torrent_dict['info_deeplink'] = 'https://t.me/{}?start=info{}'.format(
                self._qbt._bot_username,
                self._torrent_dict['hash']
            )

        self._torrent_dict['short_name'] = self._torrent_dict['name']
        if len(self._torrent_dict['name']) > 51:
            self._torrent_dict['short_name'] = self._torrent_dict['name'][:51].strip() + '...'
        self._torrent_dict['short_name_escaped'] = u.html_escape(self._torrent_dict['short_name'])

        self._torrent_dict['generic_speed'] = self._torrent_dict['dlspeed']
        icon = '▼'
        if self._torrent_dict['state'] in ('uploading', 'forcedUP', 'stalledUP'):
            self._torrent_dict['generic_speed'] = self._torrent_dict['upspeed']
            icon = '▲'
        generic_speed_human_readable = u.get_human_readable(self._torrent_dict['generic_speed'])
        self._torrent_dict['traffic_direction_icon'] = f"{icon}"

        for k, v in NEW_ATTRS.items():
            try:
                self._torrent_dict[k] = v(self._torrent_dict)
            except KeyError:
                # it might be that one of the lambdas uses a key that is not available in the torrent dict,
                # eg. when get_additional_torrent_properties is not True
                continue

    def short_markup(self, *args, **kwargs):
        return kb.short_markup(self.hash, *args, **kwargs)
    
    def dict(self):
        return self._torrent_dict

    def __getitem__(self, item):
        return self._torrent_dict[item]

    def __getattr__(self, item):
        return self._torrent_dict[item]

    def tags_list(self, lower=False):
        if not self.tags:
            return []

        tags_list = self.tags.split(",")
        return tags_list if not lower else [tag.lower() for tag in tags_list]

    def string(self, refresh=False, base_string: Optional[str] = None):
        if refresh:
            # always get all the available properties when getting the torrent string
            self.refresh(refresh_torrent_dict=True, get_torrent_generic_properties=True)

        base_string = base_string or TORRENT_STRING
        
        return base_string.format(**self._torrent_dict)

    def pause(self):
        return self._qbt.pause(self.hash)

    def resume(self):
        return self._qbt.resume(self.hash)

    def toggle_force_start(self, value=True):
        # 'force_start' method name cannot be used because it is already a property
        return self._qbt.force_start([self.hash], value=value)

    def toggle_atm(self, value: bool):
        return self._qbt.set_automatic_torrent_management(self.hash, enable=value)

    def recheck(self):
        return self._qbt.recheck([self.hash])

    def trackers(self) -> List:
        return self._qbt.get_torrent_trackers(self.hash)

    def remove_trackers(self, urls: [str, List]) -> List:
        return self._qbt.remove_trackers(self.hash, urls)

    def add_tags(self, tags: [str, List]):
        return self._qbt.add_tags(self.hash, tags)

    def remove_tags(self, tags: [str, List] = None):
        return self._qbt.remove_tags(self.hash, tags)

    def delete(self, with_files=False):
        if with_files:
            return self._qbt.delete_permanently([self.hash])
        else:
            return self._qbt.delete([self.hash])


class CustomClient(Client):
    def __init__(self, url, bot_username):
        self._bot_username = bot_username
        super(CustomClient, self).__init__(url=url)
        self.online = True

    @property
    def save_path(self):
        return self.preferences()['save_path']

    def _set_torrents_queueing(self, value):
        value = bool(value)

        return self.set_preferences(**{'queueing_enabled': value})

    def enable_torrents_queueing(self):
        return self._set_torrents_queueing(True)

    def disable_torrents_queueing(self):
        return self._set_torrents_queueing(False)

    @property
    def torrents_queueing(self):
        return self.preferences()['queueing_enabled']

    def torrents(self, get_torrent_generic_properties=True, **kwargs):
        torrents = super(CustomClient, self).torrents(**kwargs) or []

        return [Torrent(self, torrent_dict, get_torrent_generic_properties) for torrent_dict in torrents]

    # noinspection PyUnresolvedReferences
    def torrent(self, torrent_hash, get_torrent_generic_properties=True):
        # always set get_additional_torrent_properties to False in the following request,
        # we will get the additional properties later, just for the correct torrent
        torrents = super(CustomClient, self).torrents(filter='all') or []

        for torrent_dict in torrents:
            if torrent_dict['hash'].lower() == torrent_hash.lower():
                return Torrent(self, torrent_dict, get_torrent_generic_properties)

    # noinspection PyUnresolvedReferences
    def filter(self, query):
        filtered = list()
        query = query.lower()

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

    def get_alt_speed(self, human_readable=True):
        p = self.preferences()

        result = dict()

        if human_readable:
            result['status'] = 'on' if self.get_alternative_speed_status() else 'off'
            result['alt_dl_limit'] = u.get_human_readable(p['alt_dl_limit'], 0) if p['alt_dl_limit'] > -1 else 'none'
            result['alt_up_limit'] = u.get_human_readable(p['alt_up_limit'], 0) if p['alt_up_limit'] > -1 else 'none'
        else:
            result['status'] = bool(self.get_alternative_speed_status())
            result['alt_dl_limit'] = p['alt_dl_limit'] if p['alt_dl_limit'] > -1 else None
            result['alt_up_limit'] = p['alt_up_limit'] if p['alt_up_limit'] > -1 else None

        return result

    def get_speed(self):
        tinfo = self.global_transfer_info

        return (
            u.get_human_readable(tinfo['dl_info_speed']),
            u.get_human_readable(tinfo['up_info_speed'])
        )

    def get_global_speed_limit(self):
        p = self.preferences()

        return (
            u.get_human_readable(p['dl_limit']) if p['dl_limit'] else None,
            u.get_human_readable(p['up_limit']) if p['up_limit'] else None
        )

    def create_tags(self, tags):
        if isinstance(tags, str):
            tags = [tags]

        tags_str = ",".join(tags)

        return self._post('torrents/createTags', data={'tags': tags_str})

    def add_tags(self, torrent_hash, tags: [str, List]):
        if isinstance(tags, str):
            tags = [tags]

        tags_str = ",".join(tags)
        return self._post('torrents/addTags', data={'hashes': torrent_hash, 'tags': tags_str})

    def remove_tags(self, torrent_hash, tags: [str, List] = None):
        if isinstance(tags, str):
            tags_str = tags
        elif isinstance(tags, list):
            tags_str = ",".join(tags)
        else:
            tags_str = ""

        return self._post('torrents/removeTags', data={'hashes': torrent_hash, 'tags': tags_str})

    def remove_trackers(self, torrent_hash, urls: [str, List]):
        if isinstance(urls, str):
            urls = [urls]

        urls_str = "|".join(urls)
        return self._post('torrents/removeTrackers', data={'hash': torrent_hash, 'urls': urls_str})

    def build_info(self):
        return self._get('app/buildInfo')


class OfflineClient:
    """
    We use this calss when we can't connect to qbittorrent, so the bot would still run and let us
    use all the other methods that do not require to be connected to qbittoreent's webAPI
    """

    def __init__(self):
        self.online = False

    def __getattr__(self, name):
        def internal(*args, **kwargs):
            logger.debug('OfflineClient method called: %s', name)
            self._raise()

        return internal()

    def _raise(self):
        raise ConnectionError('cannot connect to qbittorrent ({})'.format(config.qbittorrent.url))
