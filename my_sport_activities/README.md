# my_sport_activities

## Introduction
This python script has been written to get training data from Strava and upload training hours and kilometers of current year to Zabbix.

Zabbix sender utility is not needed. Sender function is implemented into script.
#
## Zabbix

Import "my_sport_activies.yaml" host to Zabbix.

#
## Strava

You must have Strava account and some device which collects data to Strava (mobile phone, sport watch). I have been using Suunto 9 Baro watch. Suunto account can be linked to Strava, so my activies ends up to Strava automatically.

By default you won't see API menu at Strava profile page (https://www.strava.com/settings/profile).

API menu can be accessed from (https://www.strava.com/settings/api). Fill in your information to and click create. 

    Application Name: <some name>
    Category: <select some>
    Club: <select some or leave empty>
    Website: https://www.strava.com/athletes/<REPLACE_WITH_USERNAME>
    Application Description: <some description>
    Authorization Callback Domain: localhost

Once the application is created, save your Client ID and Client secret for upcoming step.

Next step is to authorize your account to view detailed training data. 

Open https://www.strava.com/oauth/authorize?client_id=<REPLACE_WIHT_CLIENT_ID>&redirect_uri=http://localhost&response_type=code&scope=activity:read_all with webbrowser.

Make sure that "View data about your private activities" is selected and click Authorize.

Then grab your CODE from address bar (http://localhost/?state=&code=<CODE_IS_HERE>&scope=read,activity:read_all). Save the code for upcoming step.


Now it's time to run the my_sport_activities.py for the 1st time.

    $ python3 my_sport_activities.py
    Keyfile (strava_api_keys.txt) created, please add your Client ID and Client secret into keyfile.

Add your ID and secret as told. 

Run the script with -c argument

    $ python3 my_sport_activities.py -c <CODE>
    Authorization failed.

    Trying to reauthorize tokens.

    {"response":"success","info":"processed: 2; failed: 0; total: 2; seconds spent: 0.000072"}


Now keyfile should contain access and refresh tokens.

Run the script again

    $ python3 my_sport_activities.py
    
    {"response":"success","info":"processed: 2; failed: 0; total: 2; seconds spent: 0.000085"}

Looking good. Now the script could be run by cron once in an hour. 









