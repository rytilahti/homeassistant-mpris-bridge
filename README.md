# Control your Home Assistant media players from your desktop using MPRIS!

## What?

This project bridges your Home Assistant instance and your desktop to control media players known to your Home Assistant instance.

It works by by communicating with Home Assistant using its websocket API, and exposes media players to your desktop using widely-implemented MPRIS ("Media Player Remote Interfacing Specification") interfaces.

### Features

* Shows information about what's currently being played (artist, album, title, cover art)
* Basic playback controls (play, pause, previous, next)
* Volume controlling
* Seeking forwards/backwards
* Minimal configuration needed, autodetects players as they come!


## tl;dr:

![Demo](hassbridge_demo.gif)

## I want it right now, but how?!

1. Install from PyPI, the simplest way is to use [pipx](https://github.com/pypa/pipx). Alternatively, simple clone this repository and run `poetry install`

```
pipx install homeassistant-mpris-bridge
```

2. Launch `hassbridge`

```
hassbridge --endpoint http://192.168.123.123:8123 --token <long lived token>
```

Instead of using `--endpoint` and `--token` you can also define the following environment variables to achieve the same:

```
export HASSBRIDGE_ENDPOINT="http://192.168.123.123:8123"
export HASSBRIDGE_TOKEN="<long lived token>"
```

### Running as systemd service

The simplest way to make sure the bridge is started alongside your desktop session is to create a systemd user service for it:

1. Create a service file `~/.config/systemd/user/hassbridge.service` with the following content:

```
[Unit]
Description=hassbridge

[Service]
ExecStart=<PATH TO HASSBRIDGE>
Environment="HASSBRIDGE_TOKEN=<YOUR TOKEN>"
Environment="HASSBRIDGE_ENDPOINT=<URL TO HOMEASSISTANT>"

[Install]
WantedBy=multi-user.target
```

You have to do the following substitutions:
* Replace `<PATH TO HASSBRIDGE>` with the location of the `hassbridge` script (use `which hassbridge`)
* Replace `<YOUR TOKEN>` with your long-lived token (https://www.home-assistant.io/docs/authentication/#your-account-profile)
* Replace `<URL TO HOMEASSISTANT>` with the URL to your instance (e.g., http://192.168.123.123:8123).

2. Start the service and verify that it is running correctly

```
systemctl --user start hassbridge
systemctl --user status hassbridge
```

3. Enable the service so that it starts automatically when you log in

```
systemctl --user enable hassbridge
```

### hassbridge --help

```
$ hassbridge --help
Usage: hassbridge [OPTIONS] COMMAND [ARGS]...

  hass-mpris bridge.

Options:
  --endpoint TEXT
  --token TEXT
  -d, --debug
  --help           Show this message and exit.

Commands:
  connect

```

## How does it work?

Homeassistant connectivity is achived with [homeassistant's websockets API](https://developers.home-assistant.io/docs/api/websocket/).
Every `media_player` entity in the homeassistant instance will then be exposed over D-Bus to other applications to use, implementing two MPRIS interfaces:

* org.mpris.MediaPlayer2
* org.mpris.MediaPlayer2.Player

Each time homeassistant informs over websocket API about a state change,
the details for known entities are signaled over the D-Bus interfaces to clients.

### Specs

* https://developers.home-assistant.io/docs/api/websocket/
* https://specifications.freedesktop.org/mpris-spec/2.2/


## Contributing

Contributions in form of pull requests are more than welcome.
Before submitting a PR, verify that the code is correctly formatted by calling `tox -e lint`.
Alternatively, you can use `pre-commit` to enforce the checks:

```
$ pre-commit install
```
