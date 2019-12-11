## qBittorrent Telegram interface

Extremely simple Telegram bot I made to get some basic info about the currently active torrents on my home Raspberry, using the [qBittorrent WebUI APIs (v3.1.x)](https://github.com/qbittorrent/qBittorrent/wiki/WebUI-API-Documentation-(qBittorrent-v3.1.x)) through the [python-qBittorrent](https://github.com/v1k45/python-qBittorrent) library

### Features

Only a small set of features of the qBittorrent web API has been implemented:

- see a list of torrents based on their downloading status
- add torrents by magnet link/torrent file
- manage a torrent (pause/resume, set force-start, increase priority, force re-check, delete)
- enable/disable/change your alternative speed limits
- see your qBittorrent settings
- export your torrents list as a json file

For a list of commands, use `/help`

### Setup

1. [enable qBittorrent's Web UI](https://github.com/lgallard/qBittorrent-Controller/wiki/How-to-enable-the-qBittorrent-Web-UI)
2. rename `config.example.toml` to `config.toml`
3. edit `config.toml` in the following way:
  - `[telegram]` section: place your API token in `token` and your user ID in `admins`
  - `[qbitttorrent]` section: fill the three values according to your qBittorrent WebUI settings
4. install the rquirements via `pip install -r requirements.txt`

### Permissions

By default, read-only commands (viewing the torrents list, filtering torrents, viewing the settings) are available to anyone, but there's a couple of values in the `permissions.json` file (`default_permissions.json` if you have not started the bot yet) that can be toggled to set who can use the bot:

- `free_read`: when `true`, anyone can use read-only commands (viewing the torrents list, the torrents info and the current settings)
- `free_write`: when `true`, anyone can add torrents by magnet link and file. Only works if `free_read` is `true`
- `free_edit`: when `true`, anyone can manage torrents' settings and qbittorrent's setting. Only works if `free_read` is `true`
- `admins_only`: nobody can use the bot except for the users listed as `admins`, which can do anything. When `true`, this setting has the priority over the `free_*` settings

You can see and change the current permissions configuration from the bot's chat, using the `/permissions` and `/pset` commands

### Tested on...

I made this bot to be able to manage what I'm downloading on my Raspberry running Raspbian (using qBittorrent's [headless version](https://github.com/qbittorrent/qBittorrent/wiki/Setting-up-qBittorrent-on-Ubuntu-server-as-daemon-with-Web-interface-(15.04-and-newer))), and that's the only environment I've tested this thing in. There's also the systemd file I'm using, `qbtbot.service` (which assumes you're going to run the bot in a python3 virtual environment)

### BotFather commands

Use the text below to set your bot's commands suggestions through [@BotFather](https://t.me/botfather)

```
quick - get an overview of what we're downloading
fast - disable alternative speed limits
slow - enable alternative speed limits
active - list active torrents
tostart - show torrents that are not active or completed
help - see the help message
altoff - disable alternative speed limits
alton - enable alternative speed limits
completed - list completed torrents
all - list all torrents
downloading - list downloading torrents
paused - list paused torrents
inactive - list inactive torrents
set - change a setting
filter - filter torrents by name
log - get the log file
settings - get the settings list
altdown - set the alternative download speed (in kb/s)
altup - set the alternative upload speed (in kb/s)
json - export the list of torrents
permissions - get the current permissions configuration
pset - change the value of a permission setting
pauseall - pause all torrents
resumeall - resume all torrents
config - get the qbittorrent's section of the config file
rmkb - remove the keyboard
```
