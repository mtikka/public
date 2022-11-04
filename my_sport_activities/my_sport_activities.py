#!/bin/python3

# filename:         my_sport_activities.py
# purpose:          Get data from Strava and send it to Zabbix
# date/version:     4.11.2022
# author:           mtikka
# usage:            $ python3 my_sport_activities.py -h
# compatibility:    Tested with Zabbix 6.2.4 and Python 3.9.2
# notes:            

# Imports
import argparse
import csv
import datetime
import json
import requests
import sys
import struct
import socket

# constants
DATA_URL = 'https://www.strava.com/api/v3/athlete/activities'
OAUTH_URL = 'https://www.strava.com/api/v3/oauth/token'

# Variables
strava_api_keys = {'client_id':'', 'client_secret':'', 'access_token':'', 'refresh_token':''}
this_year = datetime.datetime.now().year
this_month = datetime.datetime.now().month
elapsed_time = 0
distance = 0.0
args = []

# Functions 

def argument_parser():
    parser = argparse.ArgumentParser(description='Read sports information from strava API and send then to Zabbix.')

    parser.add_argument('-v', '--verbose', action='store_true', help='enable verbose mode')
    parser.add_argument('-c', '--code', help='reauthorization code')
    parser.add_argument('-f', '--file', help='file to load and save secrets', \
        default="strava_api_keys.txt")
    parser.add_argument('-z', '--zbx', help='ip-address or hostname of Zabbix server', \
        default="127.0.0.1")
    parser.add_argument('-p', '--port', help='port listened by Zabbix server', type=int, \
        default=10051)

    args = parser.parse_args()

    if args.verbose:
        print()
        print('Argparse arguments:\n' + str(args))
        print('')

    return args

def get_training_data():
    all_activities = []
    elapsed_time = 0
    distance = 0.0

    for i in range(1, this_month+1):

        # Calculate timestamps for each month
        if i == 1:
            begin = str(int(datetime.datetime(this_year, 1, 1, 0, 0).timestamp()))
        else:
            begin = str(int(datetime.datetime(this_year, i, 1, 0, 0).timestamp()))
            
        if i < 12:
            end = str(int(datetime.datetime(this_year, i+1, 1, 0, 0).timestamp()))
        else:
            end = str(int(datetime.datetime(this_year+1, 1, 1, 0, 0).timestamp()))


        # Try to get data of past month from file
        try: 
            tmp_sport_data = {}
            tmp_sport_data = json.load( open('/tmp/strava_' + str(strava_api_keys['client_id']) + \
                '_' + str(this_year) + '_' + str(i) + '.tmp'))
            all_activities = all_activities + tmp_sport_data

        # Get data from strava if tmp file is not found
        except:
            
            r = requests.get(DATA_URL + \
                '?access_token=' + strava_api_keys['access_token'] + \
                '&after=' + begin + \
                '&before=' + end + \
                '&per_page=200')

            if i < this_month:
                json.dump( json.loads(r.text), open('/tmp/strava_' + str(strava_api_keys['client_id']) + \
                '_' + str(this_year) + '_' + str(i) + '.tmp', 'w'))

            all_activities = all_activities + json.loads(r.text)

    for i in all_activities:
        elapsed_time = elapsed_time + i['elapsed_time']
        distance = distance + i['distance']
        

    return(elapsed_time/3600, distance/1000)

def keyfile_read():
    try:
        # check existence of keyfile
        with open (args.file) as csvfile:
            pass
    except:
        # create keyfile if it does not exist
        with open (args.file, 'w') as datafile:
            datafile.write('client_id;\n' + 'client_secret;\n' + 'refresh_token;\n' + 'access_token;\n')

        print('Keyfile (' + args.file + ') created, please add your Client ID and Client secret into keyfile.')
        sys.exit(1)


    # read content of keyfile
    with open (args.file) as csvfile:
        for line in csv.reader(csvfile, delimiter=';'):
            if line:
                strava_api_keys[line[0]]=line[1]

    for i in strava_api_keys.keys():
        if (i == 'client_id' or i == 'client_secret') and not strava_api_keys[i]:
            print('Credentials file (' + args.file + ') is not complete, please add your credentials into that file and try again.')
            sys.exit(1)

        # elif i == ('access_token' or i == 'refresh_token') and not strava_api_keys[i]:
        #     strava_api_keys['refresh_token'], strava_api_keys['access_token'] = reauthorize()

    if args.verbose:
        print("Content of keyfile:\n" + json.dumps(strava_api_keys, indent=4))
        print('')

    return strava_api_keys

def keyfile_write():
    with open (args.file, 'w') as datafile:
        for i in strava_api_keys:
            datafile.write(i + ';' + strava_api_keys[i] + '\n')

def reauthorize():
    print('Trying to reauthorize tokens.')
    r = requests.post(OAUTH_URL + \
        '?client_id=' + strava_api_keys['client_id'] + \
        '&client_secret=' + strava_api_keys['client_secret'] + \
        '&code=' + args.code + \
        '&grant_type=authorization_code' )

    response = json.loads(r.text)

    if args.verbose:
        print(json.dumps(response, indent=4))

    if '200' in str(r):
        return(response['refresh_token'], response['access_token'])

    else:
        return 'failed', 'failed'

def refresh_access_token():
    if args.verbose:
        print('Trying to refresh tokens.')

    r = requests.post(OAUTH_URL + \
        '?client_id=' + strava_api_keys['client_id'] + \
        '&client_secret=' + strava_api_keys['client_secret'] + \
        '&grant_type=refresh_token' + \
        '&refresh_token=' + strava_api_keys['refresh_token'])

    response = json.loads(r.text)

    if args.verbose:

        print(json.dumps(response, indent=4))

    if '200' in str(r):
        return(response['refresh_token'], response['access_token'])

    else:
        return 'failed', 'failed'

def test_keys():
    r = requests.get(DATA_URL + '?access_token=' + strava_api_keys['access_token'] + '&per_page=1')
    response = json.loads(r.text)
    
    if '200' in str(r):
        if args.verbose:
            print('Authorization ok, can continue')
            print('')
        return True
    else:
        print('Authorization failed.')
        print('')
        return False

def zabbix_sender():
    header = 'ZBXD\1'
    data = {
        'request':'sender data',
        'data':[
            {
                'host':'My sport activities',
                'key':'my.sport.hours',
                'value': elapsed_time
            },
            {
                'host':'My sport activities',
                'key':'my.sport.kilometers',
                'value': distance
            },
        ]
    }

    if args.verbose:
        print('Data to be send to Zabbix:')
        print(json.dumps(data, indent=4))
        print('')

    payload = 'ZBXD\1' + struct.pack('<Q', len(json.dumps(data))).decode('latin-1') + json.dumps(data)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((args.zbx, args.port))
    sock.send(payload.encode('latin-1'))

    response = sock.recv(6)
    response = sock.recv(1024)
    print('')
    print(response.decode())
    print('')
    sock.close()
  

## Main script ##

# Parse arguments
args = argument_parser()

# Read content of keyfile to variable
strava_api_keys = keyfile_read()

# Make backup to avoid rewrite of the file
strava_api_keys_bu = strava_api_keys.copy()

# Test keys
keys_ok = test_keys()

# Try to refresh the keys
if not keys_ok:
    strava_api_keys['refresh_token'], strava_api_keys['access_token'] = refresh_access_token()

    if not 'failed' in strava_api_keys['refresh_token']:
        keys_ok = test_keys()

# Try to reauthorize if refresh didn't help
if not keys_ok:
    strava_api_keys['refresh_token'], strava_api_keys['access_token'] = reauthorize()

    if not 'failed' in strava_api_keys['refresh_token']:
        keys_ok = test_keys()

# Give up
if not keys_ok:
    print("Token refresh and reauthorization failed, get new code and check your id and secret.")
    sys.exit(1)

# Write keys back to the file
if strava_api_keys != strava_api_keys_bu:
    keyfile_write()

elapsed_time, distance = get_training_data()
 
zabbix_sender()

# EOF