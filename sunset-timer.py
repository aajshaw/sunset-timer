from configparser import ConfigParser, ExtendedInterpolation
import requests
import json
import datetime
from datetime import timedelta
import time
import subprocess
from dateutil import tz

# 0. get config location
# 1. get sunset time and sleep until then
# 2. get config switches
# 3. turn on all switches
# 4. sleep until midnight
# 5. turn off all switches
# 6. forget all switch data
# 7. sleep until 03:00 to allow for daylight saving time changovers
# 7. loop to 1

class Switch():
    def __init__(self, id):
        self.id = id

    def getId(self):
        return self.id
    
    def action(self, command, toggle):
        if 'on' == toggle.lower():
            say('Turning', self.id, 'on')
            status = subprocess.run([command, self.id, 'on'])
            say('Status', status)
            if status.returncode != 0:
                say('Switch', self.id, 'returned code', status.returncode)
        else:
            say('Turning', self.id, 'off')
            status = subprocess.run([command, self.id, 'off'])
            say('Status', status)
            if status.returncode != 0:
                say('Switch', self.id, 'returned code', status.returncode)

class Switches():
    def __init__(self):
        self.command = '~/rfoutlet'
        self.switches = []

def getConfigDebug():
    config = ConfigParser()
    config.read('sunset-timer.ini')
    debugOptions = {'fast-time': False, 'verbose': False}
    if 'Debug' in config:
        debug = config['Debug']
        debugOptions['fast-time'] = debug.get('fast-time', False)
        debugOptions['verbose'] = debug.get('verbose', False)
    return debugOptions

def getConfigLocation():
    config = ConfigParser()
    config.read('sunset-timer.ini')
    location = {}
    if 'Location' in config:
        location = config['Location']
        if not 'lat' in location:
            location['lat'] = '51.508050'
        if not 'lng' in location:
            location['lng'] = '-0.128010'
    else:
        # default location Trafalgar Square London
        location = {'lat': '51.508050', 'lng': '-0.128010'}
        
    return {'lat': location['lat'], 'lng': location['lng']}

def getConfigSwitches():
    config = ConfigParser(interpolation = ExtendedInterpolation())
    config.read('sunset-timer.ini')
    switches = Switches()
    if 'Command' in config:
        command = config['Command']
        switches.command = command.get('run', '~/rfoutlet')
    if 'Switches' in config:
        for switch in config['Switches']:
            newSwitch = Switch(config['Switches'][switch])
            switches.switches.append(newSwitch)
            say('Loaded switch', newSwitch.getId())
    
    return switches
    
def getSunsetTime(location):
    request = requests.get('https://api.sunrise-sunset.org/json?lat={0}&lng={1}'.format(location['lat'], location['lng']))
    sunsetTimeUTC = request.json()['results']['sunset']
    sunsetDatetimeUTC = datetime.datetime.combine(datetime.datetime.date(datetime.datetime.today()),
                                                  datetime.datetime.strptime(sunsetTimeUTC, '%I:%M:%S %p').time())
    say('sunsetDatetimeUTC', sunsetDatetimeUTC)
    sunsetDatetimeUTC = sunsetDatetimeUTC.replace(tzinfo = tz.tzutc())
    sunsetLocal = sunsetDatetimeUTC.astimezone(tz.tzlocal())
    say('sunsetLocal', sunsetLocal)
    
    return sunsetLocal.time()

def processSwitches(switches, toggle):
    for switch in switches.switches:
        switch.action(switches.command, toggle)

def sleepFor(seconds):
    if 'fast-time' in debug and debug['fast-time']:
        say('Sleeping for', seconds / 1000, 'seconds')
        time.sleep(seconds / 1000)
    else:
        say('Sleeping for', seconds, 'seconds')
        time.sleep(seconds)

def say(*args):
    if 'verbose' in debug and debug['verbose']:
        print('Log:', datetime.datetime.now().time(), end = ' ')
        for arg in args:
            print(arg, end = ' ')
        print()

while True:
    debug = getConfigDebug()
    say('debug', debug)
    
    location = getConfigLocation()
    say(location)
    
    sunset = getSunsetTime(location)
    say('Sunset', sunset)
    
    now = datetime.datetime.now().time()
    say('Now', now)
    
    nowDelta = timedelta(hours = now.hour, minutes = now.minute, seconds = now.second)
    say('nowDelta', nowDelta)
    
    sunsetDelta = timedelta(hours = sunset.hour, minutes = sunset.minute, seconds = sunset.second)
    say('sunsetDelta', sunsetDelta)
    
    # Sleep until sunset
    sleepTime = sunsetDelta - nowDelta
    say('Sleep until sunset')
    sleepFor(sleepTime.seconds)
    say('Waking up')
    
    # Load the switch control configuration and turn all switches on
    switches = getConfigSwitches()
    processSwitches(switches, 'on')
    
    # Sleep until midnight
    now = datetime.datetime.now().time()
    nowDelta = timedelta(hours = now.hour, minutes = now.minute, seconds = now.second)
    midnightDelta = timedelta(hours = 0, minutes = 0, seconds = 0)
    sleepTime = midnightDelta - nowDelta
    say('Sleep until midnight')
    sleepFor(sleepTime.seconds)
    
    # Turn all switches off
    processSwitches(switches, 'off')
    switches = None
    
    # Sleep until about 03:00 just in case DST kicks in
    sleepFor(3 * 60 * 60)