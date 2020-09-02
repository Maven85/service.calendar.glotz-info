# -*- encoding: utf-8 -*-
from __future__ import unicode_literals
from datetime import datetime
from dateutil import relativedelta
import os

import xbmc
import xbmcaddon
import xbmcgui

from resources.lib.googleCalendar import Calendar
import resources.lib.tools as t
import resources.lib.notification as DKT

__addon__ = xbmcaddon.Addon()
__path__ = __addon__.getAddonInfo('path')
__icon__ = os.path.join(xbmc.translatePath(__path__), 'resources', 'skins', 'Default', 'media', 'icon.png')
__icon2__ = os.path.join(xbmc.translatePath(__path__), 'resources', 'skins', 'Default', 'media', 'icon_alert.png')
__profiles__ = __addon__.getAddonInfo('profile')
__LS__ = __addon__.getLocalizedString

TEMP_STORAGE_NOTIFICATIONS = os.path.join(xbmc.translatePath(__profiles__), 'notifications.json')

if t.getAddonSetting('show_onstart', sType=t.BOOL):
    xbmcgui.Window(10000).setProperty('reminders', '1')
else:
    xbmcgui.Window(10000).setProperty('reminders', '0')

_cycle = 0

googlecal = Calendar()
monitor = xbmc.Monitor()
while xbmcgui.Window(10000).getProperty('reminders') == '1' and not monitor.abortRequested():
    now = datetime.utcnow().isoformat() + 'Z'
    timemax = (datetime.utcnow() + relativedelta.relativedelta(months=t.getAddonSetting('timemax', sType=t.NUM))).isoformat() + 'Z'
    events = googlecal.get_events(TEMP_STORAGE_NOTIFICATIONS, now, timemax, maxResult=30)

    _ev_count = 1
    for event in events:
        event = googlecal.prepareForAddon(event)
        t.Notify().notify('%s %s %s' % (event['timestamps'], __LS__(30145), event['shortdate']), event['description'] or event['summary'], icon=__icon__)
        _ev_count += 1
        monitor.waitForAbort(7)
        if _ev_count > t.getAddonSetting('numreminders', sType=t.NUM) or xbmcgui.Window(10000).getProperty('reminders') != '1' or monitor.abortRequested(): break

    if events and _cycle > 0 and not monitor.abortRequested():
        DialogKT = DKT.DialogKaiToast.createDialogKaiToast()
        DialogKT.label_1 = __LS__(30019)
        DialogKT.label_2 = __LS__(30018)
        DialogKT.icon = __icon2__
        DialogKT.show()
        xbmc.Monitor().waitForAbort(t.getAddonSetting('lastnoticeduration', sType=t.NUM))
        DialogKT.close()

    monitor.waitForAbort(t.getAddonSetting('interval', sType=t.NUM, multiplicator=60))
    _cycle += 1

t.writeLog('Notification service finished', xbmc.LOGINFO)
