#!/usr/bin/python
# -*- coding: utf-8 -*-

# Licensed under the MIT license
# http://opensource.org/licenses/mit-license.php

# Copyright 2008 Frank Scholz <coherence@beebits.net>
# Copyright 2014 Soeren Beye	<soeren@soerenbeye.de>

""" Coherence and Caja bridge to play a file with a DLNA/UPnP MediaRenderer

    usable as Caja Extension

    for use an extension, copy it to ~/.local/share/caja-python/extensions

    connection to Coherence is established via DBus

"""
import os
import time

import pygtk
pygtk.require("2.0")

from urllib import unquote

from gi.repository import Caja, GObject, Gio, Gtk

import dbus
from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop(set_as_default=True)
import dbus.service

# dbus defines
BUS_NAME = 'org.Coherence'
OBJECT_PATH = '/org/Coherence'

class DLNAControllerWindow(Gtk.Window,):

    def __init__(self, svc):
        Gtk.Window.__init__(self, title=svc)
        
        #the "s" device
        self.svc = svc


        #Gtk.Box in GTK3
        self.box = Gtk.HBox(spacing=6)
        self.add(self.box)

        self.button1 = Gtk.Button(label="Play")
        self.button1.connect("clicked", self.on_button1_clicked)
        self.box.pack_start(self.button1, True, True, 0)

        self.button2 = Gtk.Button(label="Pause")
        self.button2.connect("clicked", self.on_button2_clicked)
        self.box.pack_start(self.button2, True, True, 0)

        self.button3 = Gtk.Button(label="Stop")
        self.button3.connect("clicked", self.on_button3_clicked)
        self.box.pack_start(self.button3, True, True, 0)

    def on_button1_clicked(self, widget):
        self.svc.action('play','')

    def on_button2_clicked(self, widget):
        self.svc.action('pause','')

    def on_button3_clicked(self, widget):
        self.svc.action('stop','')


class CoherencePlayExtension(Caja.MenuProvider, GObject.GObject):

    def __init__(self):
        print "CoherencePlayExtension", os.getpid()
        self.coherence = None
        try:
            self.init_controlpoint()
        except:
            print "can't setup Coherence connection"

    def init_controlpoint(self):
        self.bus = dbus.SessionBus()
        self.coherence = self.bus.get_object(BUS_NAME,OBJECT_PATH)

    def get_file_items(self, window, files):
        if self.coherence == None:
            return
        if len(files) == 0:
            return

        for file in files:
            if file.is_directory() or file.get_uri_scheme() != 'file':
                return

        #pin = self.coherence.get_pin('Caja::MediaServer::%d'%os.getpid())
        #print 'Pin:',pin
        #if pin == 'Coherence::Pin::None':
        #    return
        devices = self.coherence.get_devices(dbus_interface=BUS_NAME)
        i=0
        menuitem = None
        for device in devices:
            print device['friendly_name'],device['device_type']
            if device['device_type'].split(':')[3] == 'MediaRenderer':
                if i == 0:
                    menuitem = Caja.MenuItem(name='CoherencePlayExtension::Play', label='Play on MediaRenderer', tip='Play the selected file(s) on a DLNA/UPnP MediaRenderer')
                    submenu = Caja.Menu()
                    menuitem.set_submenu(submenu)

                item = Caja.MenuItem(name='CoherencePlayExtension::Play%d' %i, label=device['friendly_name'], tip='')
                for service in device['services']:
                    service_type = service.split('/')[-1]
                    if service_type == 'AVTransport':
                        item.connect('activate', self.play,service, device['path'], files)
                        break
                submenu.append_item(item)
                i += 1

        if i == 0:
            return

        return menuitem,

    def play(self,menu,service,uuid,files):
        print "play",uuid,service,files
        #pin = self.coherence.get_pin('Caja::MediaServer::%d'%os.getpid())
        #if pin == 'Coherence::Pin::None':
        #    return
        file = unquote(files[0].get_uri()[7:])
        file = os.path.abspath(file)

        uri = self.coherence.create_oob(file)

        #result = self.coherence.call_plugin(pin,'get_url_by_name',{'name':file})
        #print 'result', result
        print uri

        s = self.bus.get_object(BUS_NAME+'.service',service)
        print s
        
        s.action('stop','')
        s.action('set_av_transport_uri',{'current_uri':uri})
        s.action('play','')
        win = DLNAControllerWindow(s)
        win.connect("delete-event", Gtk.main_quit)
        win.show_all()
        Gtk.main()
