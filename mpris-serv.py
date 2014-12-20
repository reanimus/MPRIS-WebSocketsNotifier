# Copyright © 2014 Alex Guzman <daniel@guzman.io>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston MA 02110-1301, USA.
#


import json
import sys
import dbus
import os
import time
from gi.repository import GObject
from gi.repository import GLib
from gwebsockets import server as websocketsserver
import requests
import traceback
import collections
import threading


global properties
global bus
global sessions
sessions = []

MPRIS_PREFIX='org.mpris.MediaPlayer2'

# Utility to quickly get property from media data
def GetProperty(Property):
    global properties
    return properties.Get(MPRIS_PREFIX + '.Player', Property)

# Connects to a new player when changed
def NameOwnerChanged(Name, New, Old):
    if MPRIS_PREFIX in Name and Old != '':
        SetSource(Name)

# Notifies clients of changes in media player state
def PropertiesChanged(interface, changed_props, invalidated_props):
    for prop in changed_props:
        print(str(prop))
    if "Metadata" in changed_props:
        metadata = changed_props.get("Metadata", {})
        if metadata:
            TrackChange(metadata)
    if "PlaybackStatus" in changed_props:
        GetPlayStatus()

# Notify a session (or all sessions) of current state
def Notify(Session = None):
    GetPlayStatus(Session)
    if GetProperty('PlaybackStatus') == 'Playing' or GetProperty('PlaybackStatus') == 'Paused':
        Track = GetProperty('Metadata')
        TrackChange(Track, Session)

# Track has changed, notify a session (or all of them)
def TrackChange(Track, OutboundSession = None):
    global sessions
    # Try-catch in case the metadata ain't there
    try:
        artist = Track['xesam:artist']
    except:
        artist = ''
    try:
        track = Track['xesam:title']
    except:
        track = Track['xesam:url']
    try:
        album = Track['xesam:album']
    except:
        album = Track['xesam:album']
    try:
        length = Track['mpris:length']
    except:
        length = 0
    try:
        trackid = Track['mpris:trackid']
    except:
        trackid = ''

    # To get cover image, we use a special one for spotify (cause the web API is rad)
    if 'spotify' in trackid:
        spotify_id = trackid.replace('spotify:track:', '')
        try:
            metadata = requests.get('https://api.spotify.com/v1/tracks/' + spotify_id)
            metadata_json = metadata.json()
            coverart_value = metadata_json['album']['images']
            max_size = 0
            if isinstance(coverart_value, collections.Sequence):
                for cover in coverart_value:
                    if cover['height'] > max_size:
                        max_size = cover['height']
                        coverart = cover['url']
            else:
                coverart = cover['url']
        except:
            print("WARN: Failed to fetch spotify data: " + str(sys.exc_info()[0]))
            traceback.print_exc()
            try:
                coverart = Track['mpris:artUrl']
            except:
                coverart = ''
    else:
        try:
            coverart = Track['mpris:artUrl']
        except:
            coverart = ''

    # Print info
    print("Artist: " + ', '.join(str(x) for x in artist))
    print("Track: " + track)
    print("Album: " + album)
    print("Length: " + str(length/1000000) + " seconds")
    print("Cover Art: " + coverart)
    print("ID: " + trackid)
    tosend = json.dumps({ 'updateType' : 'track', 'artist' : ', '.join(str(x) for x in artist), 'album' : album, 'track' : track, 'length' : length/1000000, 'albumart' : coverart })
    print("JSON: " + tosend)
    
    # Send JSON info to client(s)
    if OutboundSession is None:
        toremove = []
        for session in sessions:
            try:
                session.send_message(tosend)
            except:
                toremove.append(session)
        for session in toremove:
            sessions.remove(session)
    else:
        OutboundSession.send_message(tosend)

# Gets current playback status (playing + shuffle)
def GetPlayStatus(Session = None):
    playing = GetProperty('PlaybackStatus')
    shuffle = GetProperty('Shuffle')
    print("Playing: " + str(playing))
    print("Shuffle: " + str(shuffle))
    tosend = json.dumps({ 'updateType' : 'playStatus', 'playing' : playing, 'shuffle': shuffle })
    print("JSON: " + tosend)
    
    # send info
    if Session is None:
        toremove = []
        for session in sessions:
            try:
                session.send_message(tosend)
            except:
                toremove.append(session)
        for session in toremove:
            sessions.remove(session)
    else:
        Session.send_message(tosend)

# Set media player source
def SetSource(Name):
    global properties

    media_root = bus.get_object(Name, '/org/mpris/MediaPlayer2')
    properties = dbus.Interface(media_root, dbus.PROPERTIES_IFACE)

    media_root.connect_to_signal('PropertiesChanged', PropertiesChanged)

    # If something's playing, send info on it!
    Notify()

# The actual program is here
# Set the glib main loop as the one for DBUS
from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop(set_as_default=True)

# Get session bus
bus = dbus.SessionBus()

# Subscribe to owner change notifications (so we can switch players)
dbus_object = bus.get_object( 'org.freedesktop.DBus', '/org/freedesktop/DBus' )
dbus_object.connect_to_signal('NameOwnerChanged', NameOwnerChanged, dbus_interface='org.freedesktop.DBus')

# Grab the DBUS root object
dbus_root_object = bus.get_object('org.freedesktop.DBus', '/')
dbus_root_iface = dbus.Interface(dbus_root_object, 'org.freedesktop.DBus')

# Look for a player
for n in dbus_root_iface.ListNames():
    if MPRIS_PREFIX in n:
        print("Connecting...")
        SetSource(n)
        break

# Callback for received websockets messages (currently does nothing but display/log it)
def message_received_cb(session, message):
    print("Got message: " + message.data);

# Session start callback (new client has connected)
def session_started_cb(server, session):
    # Append it to session list + add the message receive callback
    sessions.append(session)
    session.connect("message-received", message_received_cb)

    # In 1 second, send first update (the wait is to allow the handshake to complete)
    # TODO: there's probably a better way to do this than a fixed wait time
    threading.Timer(1, Notify, [session]).start()

# Spawn the server object and add our callback
server = websocketsserver.Server()
server.connect("session-started", session_started_cb)
if not server.start():
    print("The server failed to start. :(")
    sys.exit(1)

# Run the loop!
loop = GLib.MainLoop()
loop.run()