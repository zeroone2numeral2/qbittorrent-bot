## qBittorrent Telegram interface

Extremely simple Telegram bot I made to get some basic info about the currently active torrents on my home Raspberry, using the [qBittorrent WebUI APIs (v4.1+)](https://github.com/qbittorrent/qBittorrent/wiki/WebUI-API-(qBittorrent-4.1)) through the [python-qBittorrent](https://github.com/v1k45/python-qBittorrent) library.

### Features

Only a small set of features of the qBittorrent web API has been implemented:

- see a list of torrents based on their downloading status
- add torrents by magnet link/torrent file
- manage a torrent (pause/resume, set force-start, increase priority, force re-check, delete)
- enable/disable/change your alternative speed limits
- see your qBittorrent settings
- see a pretty overview of your speed, queueing and share rateo settings
- export your torrents list as a json file

For a list of commands, use `/help`

### Setup

Requires Python >= 3.6.2

1. [enable qBittorrent's Web UI](https://github.com/lgallard/qBittorrent-Controller/wiki/How-to-enable-the-qBittorrent-Web-UI)
2. rename `config.example.toml` to `config.toml`
3. edit `config.toml` in the following way:
  - `[telegram]` section: place your API token in `token` and your user ID in `admins`
  - `[qbitttorrent]` section: fill the `url`, `login` and `secret` values according to your qBittorrent WebUI settings
  - all the other values in the config file are optional, and their function is described in `config.example.toml`. 
Make sure your config file contains all the keys in the example file (the bot won't start if some are missing, but it will tell you which), and that their type is correct
4. install the rquirements via `pip install -r requirements.txt`

### Permissions

By default, only _admins_ are allowed to use the bot (users listed under `telegram.admins` in `config.toml`), but there's a couple of values in the `permissions.json` file (`default_permissions.json` if you have not started the bot yet) that can be toggled to set who can use the bot:

- `free_read`: when `true`, anyone can use read-only commands (viewing the torrents list, the torrents info and the current settings)
- `free_write`: when `true`, anyone can add torrents by magnet link and file. Only works if `free_read` is `true`
- `free_edit`: when `true`, anyone can manage torrents' settings and qbittorrent's setting. Only works if `free_read` is `true`
- `admins_only`: nobody can use the bot except for the users listed as `admins`, which can do anything. When `true`, this setting has the priority over the `free_*` settings

You can see and change the current permissions configuration from the bot's chat, using the `/permissions` and `/pset` commands

### Use in Docker

Docker function is only tested on Linux, I guess it will work on macOS too but not Windows, because Docker in Windows does not create docker0 network interface

#### Build your own image

1. clone the source code
2. rename `config.example.toml` to `config.toml`
3. edit `config.toml` in the following way:
  - `[telegram]` section: place your API token in `token` and your user ID in `admins`
  - `[qbitttorrent]` section: fill the three values according to your qBittorrent WebUI settings. IMPORTANT read the config file comment about docker0 network!
4. build your image use `docker build . -t {YOUR_TAG}`
5. run docker `docker run -d -v ${PWD}/config.toml:/app/config.toml {YOUR_TAG}`

#### Use prebuild Image
1. Download `config.example.toml` to dir you prefer, etc: "/etc/qbbot/config.toml"
2. edit `config.toml` in the following way:
  - `[telegram]` section: place your API token in `token` and your user ID in `admins`
  - `[qbitttorrent]` section: fill the three values according to your qBittorrent WebUI settings. IMPORTANT read the config file comment about docker0 network!
3. Pull image: `docker pull 0one2/qbittorrent-bot`
5. run docker `docker run -d -v ${PWD}/config.toml:/app/config.toml 0one2/qbittorrent-bot`

### Tested on...

I made this bot to be able to manage what I'm downloading on my Raspberry running Raspbian (using qBittorrent's [headless version](https://github.com/qbittorrent/qBittorrent/wiki/Setting-up-qBittorrent-on-Ubuntu-server-as-daemon-with-Web-interface-(15.04-and-newer))), and that's the only environment I've tested this thing in. There's also the systemd file I'm using, `qbtbot.service` (which assumes you're going to run the bot in a python3 virtual environment)
