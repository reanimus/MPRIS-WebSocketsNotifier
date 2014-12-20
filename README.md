# MPRIS-WebSocketsNotifier

A simple Python webserver to notify WebSockets clients of MPRIS client notifications.

Makes use of a modified version of [dnarvaez/gwebsockets](https://github.com/dnarvaez/gwebsockets) updated to support Python 3 and handle some edge cases better. A lot of the DBUS-related code uses the [MPRIS example from VLC](https://www.videolan.org/developers/vlc/extras/misc/mpris.py) as a reference.

## Dependencies

For the websockets server:

- Python 3
- PyGObject
- python-dbus

For the client, running it only requires a modern web browser (specifically, one with support for CSS3 and WebSockets). Building it requires compass and bower (essentially, the Foundation SCSS build requirements)

(Maybe others, this was definitely hacked together in a rush)

## Current Status
- Connects to DBUS to get media player updates
- Fetches track data and now playing info
- Notifies connected clients over WebSockets and sends JSON data for data that's changed

## TODO
- Code could probably be cleaned up

## License Info
- gwebsockets related stuff is under the Apache License
- the rest is under GPL
