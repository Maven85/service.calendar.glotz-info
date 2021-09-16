# -*- encoding: utf-8 -*-
from __future__ import unicode_literals
from datetime import datetime
from dateutil import relativedelta

import sys
import os

import resources.lib.tools as tools
from resources.lib.googleCalendar import Calendar

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

__addon__ = xbmcaddon.Addon()
__path__ = __addon__.getAddonInfo('path')
__profiles__ = __addon__.getAddonInfo('profile')
__LS__ = __addon__.getLocalizedString

__xml__ = xbmcvfs.translatePath('special://skin').split(os.sep)[-2] + '.calendar.xml'

if not os.path.exists(xbmcvfs.translatePath(__profiles__)): os.makedirs(xbmcvfs.translatePath(__profiles__))

TEMP_STORAGE_EVENTS = os.path.join(xbmcvfs.translatePath(__profiles__), 'events.json')

if not (xbmcgui.Window(10000).getProperty('calendar_month') or xbmcgui.Window(10000).getProperty('calendar_year')):
    xbmcgui.Window(10000).setProperty('calendar_month', str(datetime.today().month))
    xbmcgui.Window(10000).setProperty('calendar_year', str(datetime.today().year))
    _header = '%s %s' % (__LS__(30119 + datetime.today().month), datetime.today().year)
    xbmcgui.Window(10000).setProperty('calendar_header', _header)


class FileNotFoundException(Exception):
    pass


def calc_boundaries(direction):
    sheet_m = int(xbmcgui.Window(10000).getProperty('calendar_month')) + direction
    sheet_y = int(xbmcgui.Window(10000).getProperty('calendar_year'))

    if sheet_m < 1:
        sheet_m = 12
        sheet_y -= 1
    elif sheet_m > 12:
        sheet_m = 1
        sheet_y += 1

    if sheet_y == datetime.today().year:
        if sheet_m < datetime.today().month or sheet_m > datetime.today().month + tools.getAddonSetting('timemax', sType=tools.NUM):
            tools.writeLog('prev/next month outside boundary')
            return
    else:
        if sheet_m + 12 > datetime.today().month + tools.getAddonSetting('timemax', sType=tools.NUM):
            tools.writeLog('prev/next month outside boundary')
            return

    xbmcgui.Window(10000).setProperty('calendar_month', str(sheet_m))
    xbmcgui.Window(10000).setProperty('calendar_year', str(sheet_y))
    _header = '%s %s' % (__LS__(30119 + sheet_m), sheet_y)
    xbmcgui.Window(10000).setProperty('calendar_header', _header)


def controller(mode=None, handle=None, content=None, eventId=None, actor=None):
    now = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + 'Z'
    timemax = (datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) +
               relativedelta.relativedelta(months=tools.getAddonSetting('timemax', sType=tools.NUM))).isoformat() + 'Z'

    if mode == 'load_glotz_key':
        glotz_apikey = tools.dialogFile(__LS__(30089))
        if glotz_apikey != '':
            tools.setAddonSetting('glotz_apikey', glotz_apikey)
            tools.writeLog('API key for glotz.info successfull stored')
            tools.Notify().notify(__LS__(30010), __LS__(30073))

    elif mode == 'abort_reminders':
        tools.writeLog('abort notification service by setup', xbmc.LOGINFO)
        xbmcgui.Window(10000).setProperty('reminders', '0')

    elif mode == 'getcontent':
        googlecal = Calendar()
        googlecal.build_sheet(handle, TEMP_STORAGE_EVENTS, content, now, timemax, maxResult=30)

    elif mode == 'getinfo' and eventId != '':
        googlecal = Calendar()
        events = eventId.strip(' ').split(' ')
        _header = ''
        _msg = ''
        for event in events:
            _ev = googlecal.get_event(event, TEMP_STORAGE_EVENTS)
            _mev = googlecal.prepareForAddon(_ev, optTimeStamps=True)
            _time = '' if _mev.get('range', '') == '' else '[B]%s[/B]: ' % (_mev.get('range'))
            if actor and actor == 'eventlist':
                _header = 'S%02iE%02i: %s' % (_mev.get('season'), _mev.get('episode'), _mev.get('title'))
                _msg = '%s' % (_mev.get('plot'))
            else:
                _header = '%s %s %s' % (__LS__(30109), __LS__(30145), _mev.get('shortdate', ''))
                _msg += '%s%s[CR]%s[CR][CR]' % (_time, _mev.get('summary', ''),
                                                _mev.get('description') or __LS__(30093))
        tools.dialogOK(_header, _msg)

    elif mode == 'prev':
        calc_boundaries(-1)

    elif mode == 'next':
        calc_boundaries(1)

    # this is the real controller bootstrap
    elif mode == 'gui':
        try:
            Popup = xbmcgui.WindowXMLDialog(__xml__, __path__)
            Popup.doModal()
            del Popup
        except RuntimeError as e:
            raise FileNotFoundException('%s: %s' % (e.message, __xml__))
    else:
        pass


if __name__ == '__main__':

    action = None
    content = None
    eventId = None
    actor = None
    _addonHandle = None

    arguments = sys.argv
    if len(arguments) > 1:
        if arguments[0][0:6] == 'plugin':  # calling as plugin path
            _addonHandle = int(arguments[1])
            arguments.pop(0)
            arguments[1] = arguments[1][1:]

        tools.writeLog('parameter hash: %s' % (str(arguments[1])), xbmc.LOGINFO)
        params = tools.ParamsToDict(arguments[1])
        action = params.get('action', '')
        content = params.get('content', '')
        eventId = params.get('id', '')
        actor = params.get('actor')

    # call the controller of MVC
    try:
        if action is not None:
            controller(mode=action, handle=_addonHandle, content=content, eventId=eventId, actor=actor)
        else:
            controller(mode='gui')

    except FileNotFoundException as e:
        tools.writeLog(e.message, xbmc.LOGERROR)
        tools.Notify().notify(__LS__(30010), __LS__(30079))
