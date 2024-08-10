from configparser import ConfigParser, ExtendedInterpolation
import requests
import json
import datetime
from datetime import timedelta
import time
import subprocess
from dateutil import tz

# 1. get config location
# 2. get current time
# 3. if current time before 03:00
# 3a. sleep until 03:00
# 4. get current time
# 5. get sunrise time
# 6 if current time before sunrise
# 6a. sleep until sunrise
# 7. get all sunrise requests
# 8. process all sunrise requests
# 9. get sunset time
# 10. if current time before sunset
# 10a. sleep until sunset
# 11. get all sunset requests
# 12. process all sunset requests
# 13. get current time
# 14. sleep until midnight
# 15. get all midnight requests
# 16 process all midnight requests
# 17: loop to 1

def zapSwitch(command, switch_id, function):
    say('Turning', switch_id, function)
    status = subprocess.run(['sudo', 'nice', '-19', command, switch_id, function, '5'])
    say('Status', status)
    if status.returncode != 0:
        say('Switch', switch_id, 'returned code', status.returncode)

def shellyRelay(command, ip_addr, function):
    action = command.format(ip_addr, function)
    say('Action', action)
    try:
        response = requests.get(action)
        say('Response', response)
    except Exception as error:
        say('failed', error)

def processSunriseActions():
    say('Process Sunrise')

    commands = getConfigCommands()
    say('Config Commands', commands)

    config = ConfigParser()
    config.read('sunset-timer.ini')

    if 'Sunrise' in config:
        for item in config['Sunrise']:
            say('Item', item)
            detail = config['Sunrise'][item]
            say('detail', detail)
            details = detail.split(':')
            say(details)
            if details[0] == 'ShellyRelay':
                say('Processing shelly relay')
                shellyRelay(commands['shellyrelay'], details[1], details[2])
            elif details[0] == 'ZapSwitch':
                say('Processing zap switch')
                zapSwitch(commands['zapswitch'], details[1], details[2])
            else:
                say('Unknown action', details[0])

def processSunsetActions():
    say('Process sunset')

    commands = getConfigCommands()
    say('Config Commands', commands)

    config = ConfigParser()
    config.read('sunset-timer.ini')

    if 'Sunset' in config:
        for item in config['Sunset']:
            say('Item', item)
            detail = config['Sunset'][item]
            say('detail', detail)
            details = detail.split(':')
            say(details)
            if details[0] == 'ShellyRelay':
                say('Processing shelly relay')
                shellyRelay(commands['shellyrelay'], details[1], details[2])
            elif details[0] == 'ZapSwitch':
                say('Processing zap switch')
                zapSwitch(commands['zapswitch'], details[1], details[2])
            else:
                say('Unknown action', details[0])

def processMidnightActions():
    say('Process midnight')

    commands = getConfigCommands()
    say('Config Commands', commands)

    config = ConfigParser()
    config.read('sunset-timer.ini')

    if 'Midnight' in config:
        for item in config['Midnight']:
            say('Item', item)
            detail = config['Midnight'][item]
            say('detail', detail)
            details = detail.split(':')
            say(details)
            if details[0] == 'ShellyRelay':
                say('Processing shelly relay')
                shellyRelay(commands['shellyrelay'], details[1], details[2])
            elif details[0] == 'ZapSwitch':
                say('Processing zap switch')
                zapSwitch(commands['zapswitch'], details[1], details[2])
            else:
                say('Unknown action', details[0])

def getConfigCommands():
    config = ConfigParser()
    config.read('sunset-timer.ini')
    commands = {}
    if 'Commands' in config:
        for command in config['Commands']:
            say('command', command)
            commands[command] = config['Commands'][command]
    
    return commands

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

def getSunriseTime(location):
    request = requests.get('http://api.sunrisesunset.io/json?lat={0}&lng={1}&timezone=UTC'.format(location['lat'], location['lng']))
    sunriseTimeUTC = request.json()['results']['sunrise']
    sunriseDatetimeUTC = datetime.datetime.combine(datetime.datetime.date(datetime.datetime.today()),
                                                   datetime.datetime.strptime(sunriseTimeUTC, '%I:%M:%S %p').time())
    say('sunriseDatetimeUTC', sunriseDatetimeUTC)
    sunriseDatetimeUTC = sunriseDatetimeUTC.replace(tzinfo = tz.tzutc())
    sunriseLocal = sunriseDatetimeUTC.astimezone(tz.tzlocal())
    say('sunriseLocal', sunriseLocal)

    return sunriseLocal.time()
    
def getSunsetTime(location):
#    request = requests.get('https://api.sunrise-sunset.org/json?lat={0}&lng={1}'.format(location['lat'], location['lng']))
# Temp downgrade to http as security cert has expired on api.sunrise-sunset.org
# Could also use http://api.sunrisesunset.io/json?lat=xx.xxx&lng=xx.xxx
#    request = requests.get('http://api.sunrise-sunset.org/json?lat={0}&lng={1}'.format(location['lat'], location['lng']))
    request = requests.get('http://api.sunrisesunset.io/json?lat={0}&lng={1}&timezone=UTC'.format(location['lat'], location['lng']))
    sunsetTimeUTC = request.json()['results']['sunset']
    sunsetDatetimeUTC = datetime.datetime.combine(datetime.datetime.date(datetime.datetime.today()),
                                                  datetime.datetime.strptime(sunsetTimeUTC, '%I:%M:%S %p').time())
    say('sunsetDatetimeUTC', sunsetDatetimeUTC)
    sunsetDatetimeUTC = sunsetDatetimeUTC.replace(tzinfo = tz.tzutc())
    sunsetLocal = sunsetDatetimeUTC.astimezone(tz.tzlocal())
    say('sunsetLocal', sunsetLocal)
    
    return sunsetLocal.time()

def getLocalNow():
    return datetime.datetime.now().time()

def processSwitches(switches, toggle):
    for ndx in range(5):
        for switch in switches.switches:
            switch.action(switches.command, toggle)
            time.sleep(1)

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

def main():
    global debug

    while True:
        debug = getConfigDebug()
        say('debug', debug)

        location = getConfigLocation()
        say(location)

        now = getLocalNow()
        say('now', now)

        # sleep untill 03:00 if necessary, this is to allow local time to settle if sunlight saving is starting or finishing
        nowDelta = timedelta(hours = now.hour, minutes = now.minute, seconds = now.second)
        testDelta = timedelta(hours = 3)
        if nowDelta < testDelta:
            sleepTime = testDelta - nowDelta
            say('Sleep until 03:00')
            sleepFor(sleepTime.seconds)

        # sleep until sunrise if necessary
        now = getLocalNow()
        sunrise = getSunriseTime(location)
        say('Sunrise', sunrise)
        nowDelta = timedelta(hours = now.hour, minutes = now.minute, seconds = now.second)
        sunriseDelta = timedelta(hours = sunrise.hour, minutes = sunrise.minute, seconds = sunrise.second)
        if nowDelta < sunriseDelta:
            sleepTime = sunriseDelta - nowDelta
            say('Sleep until sunrise', sunrise)
            sleepFor(sleepTime.seconds)

        # Process sunrise actions
        processSunriseActions()

        # Sleep until sunset if necessary
        now = getLocalNow()
        sunset = getSunsetTime(location)
        say('Sunset', sunset)
        nowDelta = timedelta(hours = now.hour, minutes = now.minute, seconds = now.second)
        sunsetDelta = timedelta(hours = sunset.hour, minutes = sunset.minute, seconds = sunset.second)
        if nowDelta < sunsetDelta:
            sleepTime = sunsetDelta - nowDelta
            say('Sleet until sunset', sunset)
            sleepFor(sleepTime.seconds)

        # process sunset actions
        processSunsetActions()

        # sleep until midnight
        now = getLocalNow()
        nowDelta = timedelta(hours = now.hour, minutes = now.minute, seconds = now.second)
        midnightDelta = timedelta(hours = 0, minutes = 0, seconds = 0)
        sleepTime = midnightDelta - nowDelta
        say('Sleep until midnight')
        sleepFor(sleepTime.seconds)

        # process midnight actions
        processMidnightActions()

if __name__ == '__main__':
    main()
