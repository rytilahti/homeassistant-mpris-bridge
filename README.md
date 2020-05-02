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

1. Clone this repository

```
$ git clone https://github.com/rytilahti/homeassistant-mpris-bridge
```

2. Install using poetry

```
$ poetry install
```
3. Launch it!

```
$ hassbridge --endpoint http://192.168.123.123:8123 --token <long lived token>
```

Instead of using `--endpoint` and `--token` you can also define the following environment variables to achieve the same:

```
export HASSBRIDGE_ENDPOINT="http://192.168.123.123:8123"
export HASSBRIDGE_TOKEN="<long lived token>"
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

Homeassistant connectivity is achived with homeassistant's websockets API.
Every `media_player` entity in the homeassistant instance will then be exposed over D-Bus to other applications to use, implementing two MPRIS interfaces:

* org.mpris.MediaPlayer2
* org.mpris.MediaPlayer2.Player


Each time homeassistant informs over websocket API about a state change,
the details for known entities are signaled over the D-Bus interfaces to clients.

### Specs
* https://developers.home-assistant.io/docs/external_api_websocket/
* https://specifications.freedesktop.org/mpris-spec/2.2/


## Contributing

Contributions in form of pull requests are more than welcome.
Before submitting a PR, verify that the code is correctly formatted by calling `tox -e lint`.
Alternatively, you can use `pre-commit` to enforce the checks:

```
$ pre-commit install
```
