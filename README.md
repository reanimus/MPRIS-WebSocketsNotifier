# MPRIS-WebSocketsNotifier

A simple Python webserver to notify WebSockets clients of MPRIS client notifications.

Makes use of a modified version of [dnarvaez/gwebsockets](https://github.com/dnarvaez/gwebsockets) updated to support Python 3 and handle some edge cases better.

## Dependencies
- Python 3
- PyGObject
- python-dbus

(Maybe others, this was definitely hacked together in a rush)

## Current Status
- Connects to DBUS to get media player updates
- Fetches track data and now playing info
- Notifies connected clients over WebSockets and sends JSON data for data that's changed

## TODO
- Maybe add a frontend?
- Code could probably be cleaned up
