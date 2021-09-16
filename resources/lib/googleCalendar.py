# -*- encoding: utf-8 -*-
from __future__ import unicode_literals
import os
import operator
from . import tools as t

import time
import calendar
from datetime import datetime, timedelta
from dateutil import parser, relativedelta
import json
import sys

import xbmc
import xbmcaddon
import xbmcplugin
import xbmcgui
import xbmcvfs

try:
    from urllib import request as urllib
except:
    import urllib

__addon__ = xbmcaddon.Addon()
__addonname__ = __addon__.getAddonInfo('id')
__addonpath__ = __addon__.getAddonInfo('path')
__profiles__ = __addon__.getAddonInfo('profile')
__LS__ = __addon__.getLocalizedString
__symbolpath__ = os.path.join(xbmcvfs.translatePath(__addonpath__), 'resources', 'skins', 'Default', 'media')


class Calendar(object):

    SHEET_ID = 30008

    GLOTZ_URL = 'https://www.glotz.info/v2/user/calendar/%s/%s/30' % (t.getAddonSetting('glotz_apikey'), datetime.now().strftime('%Y%m%d'))


    def __init__(self):
        self.addtimestamps = t.getAddonSetting('additional_timestamps', sType=t.BOOL)


    def get_events(self, storage, timeMin, timeMax, maxResult=30, evtype='default'):
        if not os.path.exists(storage) or not t.lastmodified(storage):
            events = []

            if t.getAddonSetting('glotz_apikey') != '':
                if evtype == 'default' or (evtype == 'notification' and t.getAddonSetting('glotz_notify', sType=t.BOOL)):
                    t.writeLog('getting events from glotz.info')
                    try:
                        cal_set = json.loads(urllib.urlopen(self.GLOTZ_URL).read())
                        for _record in cal_set:
                            _item = {}
                            _show = _record.get('show')
                            _time_fmt = 'dateTime'
                            if len(_show.get('airs_time', '')) == 5:
                                _hour = int(_show.get('airs_time')[0:2])
                                _minute = int(_show.get('airs_time')[3:5])
                            else:
                                _hour = 0
                                _minute = 0
                                _time_fmt = 'date'

                            _ts = datetime.fromtimestamp(int(_record.get('first_aired', '0'))).replace(hour=_hour, minute=_minute)
                            _end = _ts + timedelta(minutes=int(_show.get('runtime', '0') if _show.get('runtime') else '0')) if _time_fmt == 'dateTime' else _ts

                            _item.update({'timestamp': int(time.mktime(_ts.timetuple())),
                                          'date': datetime.isoformat(_ts),
                                          'shortdate': _ts.strftime('%d.%m.'),
                                          'start': {_time_fmt: datetime.isoformat(_ts)},
                                          'end': {_time_fmt: datetime.isoformat(_end)},
                                          'id': '%s-%s-%s' % (_record.get('first_aired', ''), _record.get('season', '0'), _record.get('number', '0')),
                                          'summary': _show.get('network', ''),
                                          'description': '%s - S%02iE%02i: %s' % (_show.get('title', ''),
                                                                                  int(_record.get('season', '0')),
                                                                                  int(_record.get('number', '0')),
                                                                                  _record.get('title', '')),
                                          'title': _record.get('title', ''),
                                          'tvshowtitle': _show.get('title', ''),
                                          'season': int(_record.get('season', '0')),
                                          'episode': int(_record.get('number', '0')),
                                          'plot': _record.get('overview', ''),
                                          'banner': _show['images'].get('banner', ''),
                                          'allday': 1 if _time_fmt == 'date' else 0})

                            events.append(_item)
                    except Exception as e:
                        t.writeLog('Error on line {}'.format(sys.exc_info()[-1].tb_lineno), level=xbmc.LOGERROR)
                        t.writeLog(type(e).__name__, level=xbmc.LOGERROR)
                        t.writeLog(e.message, level=xbmc.LOGERROR)

            events.sort(key=operator.itemgetter('timestamp'))

            with open(storage, 'w') as filehandle: json.dump(events, filehandle)
        else:
            t.writeLog('getting events from local storage')
            with open(storage, 'r') as filehandle: events = json.load(filehandle)
        return events


    @classmethod
    def get_event(cls, eventId, storage):
        with open(storage, 'r') as filehandle: events = json.load(filehandle)
        for event in events:
            if event.get('id', '') == eventId: return event
        return False


    @classmethod
    def prepareForAddon(cls, event, timebase=datetime.now(), optTimeStamps=True):

        _ts = parser.parse(event['start'].get('dateTime', event['start'].get('date', '')))
        _end = parser.parse(event['end'].get('dateTime', event['end'].get('date', '')))
        _tdelta = relativedelta.relativedelta(_end.date(), _ts.date())

        if event.get('allday', 0) > 0:
            if _tdelta.months == 0 and _tdelta.weeks == 0 and _tdelta.days == 0: event.update({'range': ''})
            elif _tdelta.months == 0 and _tdelta.weeks == 0 and _tdelta.days == 1: event.update({'range': __LS__(30111)})
            elif _tdelta.months == 0 and _tdelta.weeks == 0: event.update({'range': __LS__(30112) % (_tdelta.days)})
            elif _tdelta.months == 0 and _tdelta.weeks == 1: event.update({'range': __LS__(30113)})
            elif _tdelta.months == 0 and _tdelta.weeks > 0: event.update({'range': __LS__(30114) % (_tdelta.weeks)})
            elif _tdelta.months == 1: event.update({'range': __LS__(30115)})
            elif _tdelta.months > 1: event.update({'range': __LS__(30116) % (_tdelta.months)})
            else: event.update({'range': __LS__(30117)})
        else:
            if _ts != _end:
                event.update({'range': _ts.strftime('%H:%M') + ' - ' + _end.strftime('%H:%M')})
            else:
                event.update({'range': _ts.strftime('%H:%M')})

        if optTimeStamps:
            t.writeLog('calculate additional timestamps')

            _tdelta = relativedelta.relativedelta(_ts.date(), timebase.date())
            if _tdelta.months == 0:
                if _tdelta.days == 0: ats = __LS__(30139)
                elif _tdelta.days == 1: ats = __LS__(30140)
                elif _tdelta.days == 2: ats = __LS__(30141)
                elif 3 <= _tdelta.days <= 6: ats = __LS__(30142) % (_tdelta.days)
                elif _tdelta.weeks == 1: ats = __LS__(30143)
                elif _tdelta.weeks > 1: ats = __LS__(30144) % (_tdelta.weeks)
                else: ats = __LS__(30117)
            elif _tdelta.months == 1: ats = __LS__(30146)
            else: ats = __LS__(30147) % (_tdelta.months)
            event.update({'timestamps': ats})

        return event


    def build_sheet(self, handle, storage, content, now, timemax, maxResult):
        self.sheet = []
        dom = 1
        _today = None
        _todayCID = 0
        _now = datetime.now()

        events = self.get_events(storage, now, timemax, maxResult)

        sheet_m = int(xbmcgui.Window(10000).getProperty('calendar_month'))
        sheet_y = int(xbmcgui.Window(10000).getProperty('calendar_year'))

        if sheet_m == datetime.today().month and sheet_y == datetime.today().year:
            _today = datetime.today().day

        start, sheets = calendar.monthrange(sheet_y, sheet_m)
        prolog = (parser.parse('%s/1/%s' % (sheet_m, sheet_y)) - relativedelta.relativedelta(days=start)).day
        epilog = 1

        try:
            xrange
        except:
            xrange = range

        for cid in xrange(0, 42):
            if cid < start or cid >= start + sheets:

                # daily sheets outside of actual month, set these to valid:0
                self.sheet.append({'cid': str(cid), 'valid': '0'})
                if cid < start:
                    self.sheet[cid].update(dom=str(prolog))
                    prolog += 1
                else:
                    self.sheet[cid].update(dom=str(epilog))
                    epilog += 1
                continue

            num_events = 0
            event_ids = ''
            allday = 0
            specialicon = ''

            for event in events:
                event = self.prepareForAddon(event, _now, optTimeStamps=False)
                cur_date = parser.parse(event.get('date'))

                if cur_date.day == dom and cur_date.month == sheet_m and cur_date.year == sheet_y:
                    event_ids += ' %s' % (event['id'])
                    num_events += 1
                    if event.get('allday', 0) > allday: allday = event.get('allday')
                    if event.get('specialicon', '') != '': specialicon = event.get('specialicon')

                if allday == 0: eventicon = os.path.join(__symbolpath__, 'eventmarker_1.png')
                elif allday == 1: eventicon = os.path.join(__symbolpath__, 'eventmarker_2.png')
                else: eventicon = os.path.join(__symbolpath__, 'eventmarker_3.png')

            self.sheet.append({'cid': cid, 'valid': '1', 'dom': str(dom)})
            if num_events > 0:
                self.sheet[cid].update(num_events=str(num_events), allday=allday, event_ids=event_ids,
                                       specialicon=specialicon, eventicon=eventicon)
            if _today == int(self.sheet[cid].get('dom')):
                self.sheet[cid].update(today='1')
                _todayCID = cid
            dom += 1

        if content == 'sheet':
            for cid in range(0, 42):
                cal_sheet = xbmcgui.ListItem(label=self.sheet[cid].get('dom'), label2=self.sheet[cid].get('num_events', '0'))
                cal_sheet.setArt({'icon': self.sheet[cid].get('eventicon', '')})
                cal_sheet.setProperty('valid', self.sheet[cid].get('valid', '0'))
                cal_sheet.setProperty('allday', str(self.sheet[cid].get('allday', 0)))
                cal_sheet.setProperty('today', self.sheet[cid].get('today', '0'))
                cal_sheet.setProperty('ids', self.sheet[cid].get('event_ids', ''))
                cal_sheet.setProperty('specialicon', self.sheet[cid].get('specialicon', ''))
                xbmcplugin.addDirectoryItem(handle, url='', listitem=cal_sheet)
            # set at least focus to the current day
            xbmc.executebuiltin('Control.SetFocus(%s, %s)' % (self.SHEET_ID, _todayCID))

        elif content == 'eventlist':
            for event in events:
                event = self.prepareForAddon(event, _now, optTimeStamps=self.addtimestamps)
                cur_date = parser.parse(event.get('date'))
                if cur_date.month >= sheet_m and cur_date.year >= sheet_y:
                    if self.addtimestamps:
                        li = xbmcgui.ListItem(label=event['shortdate'] + ' - ' + event['timestamps'], label2=event['summary'])
                        if event.get('icon'): li.setArt('icon')
                    else:
                        li = xbmcgui.ListItem(label=event['shortdate'], label2=event['summary'])
                        if event.get('icon'): li.setArt('icon')
                    li.setProperty('id', event.get('id', ''))
                    li.setProperty('range', event.get('range', ''))
                    li.setProperty('allday', str(event.get('allday', 0)))
                    li.setProperty('description', event.get('description') or event.get('location'))
                    li.setProperty('banner', event.get('banner', ''))
                    xbmcplugin.addDirectoryItem(handle, url='', listitem=li)

        xbmcplugin.endOfDirectory(handle, updateListing=True)
