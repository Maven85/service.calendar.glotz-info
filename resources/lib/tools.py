# -*- encoding: utf-8 -*-
from __future__ import unicode_literals
import xbmc
import xbmcgui
import xbmcaddon
import xbmcvfs
import json
import platform
import re
import os
from datetime import datetime


# Constants
def STRING():
    return 0


def BOOL():
    return 1


def NUM():
    return 2


def writeLog(message, level=xbmc.LOGDEBUG):
    xbmc.log('[{0}] {1}'.format(xbmcaddon.Addon().getAddonInfo('id'), message), level)


class Notify(object):


    def __init__(self):
        self.prev_header = ''
        self.prev_message = ''


    def notify(self, header, message, icon=xbmcgui.NOTIFICATION_INFO, dispTime=5000, repeat=False):
        if repeat or (header != self.prev_header or message != self.prev_message):
            xbmcgui.Dialog().notification(header, message, icon, dispTime)
        else:
            writeLog('Message content is same as before, don\'t show notification')
        self.prev_header = header
        self.prev_message = message


class release(object):


    def __init__(self):
        self.platform = platform.system()
        self.hostname = platform.node()
        item = {}
        if self.platform == 'Linux':

            try:
                with open('/etc/os-release', 'r') as _file:
                    for _line in _file:
                        parameter, value = _line.split('=')
                        item[parameter] = value
            except IOError as e:
                writeLog(e.message, xbmc.LOGERROR)

        self.osname = item.get('NAME', 'unknown')
        self.osid = item.get('ID', 'unknown')
        self.osversion = item.get('VERSION_ID', 'unknown')


def lastmodified(path):
    if (datetime.now().date() - datetime.fromtimestamp(xbmcvfs.Stat(path).st_mtime()).date()).days > 0:
        return False
    else:
        return True


def dialogOK(header, message):
    xbmcgui.Dialog().ok(header, message)


def dialogYesNo(header, message):
    return xbmcgui.Dialog().yesno(header, message)


def dialogKeyboard(header, type=xbmcgui.INPUT_ALPHANUM):
    return xbmcgui.Dialog().input(header, type=type)


def dialogFile(header, type=1):
    _file = xbmcgui.Dialog().browse(type, header, 'files', '', False, False, '', False)
    if _file:
        with open(_file, 'r') as filehandle: return filehandle.read().rstrip()
    return ''


def jsonrpc(query):
    querystring = {"jsonrpc": "2.0", "id": 1}
    querystring.update(query)
    return json.loads(xbmc.executeJSONRPC(json.dumps(querystring)))


def getAddonSetting(setting, sType=STRING, multiplicator=1):
    if sType == BOOL:
        return  True if xbmcaddon.Addon().getSetting(setting).upper() == 'TRUE' else False
    elif sType == NUM:
        try:
            return int(re.match('\d+', xbmcaddon.Addon().getSetting(setting)).group()) * multiplicator
        except AttributeError:
            return 0
    else:
        return xbmcaddon.Addon().getSetting(setting)


def setAddonSetting(setting, value):
    xbmcaddon.Addon().setSetting(setting, value)


def ParamsToDict(args):
    p_Dict = {}
    if args:
        pairs = args.split("&")
        for pair in pairs:
            par, value = pair.split('=')
            p_Dict[par] = value
    return p_Dict