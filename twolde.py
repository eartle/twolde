#!/usr/bin/env python

import os
import sys
import tweepy
import platform
import time
import sched
from datetime import datetime
import ConfigParser

config_filename = 'config.ini'

consumer_key = 'i4VfqFLIY7E08Ros9AhA'
consumer_secret = 'XP0JjlMMPtaC0IOvHv6VXzE31izdiUy1rXcoPeYg'

plist = 'uk.co.mobbler.twolde.plist'

def get_times():
    now = datetime.utcnow()
    last_year = datetime( now.year - 1, now.month, now.day, now.hour, now.minute, now.second, now.microsecond, now.tzinfo )
    return now, last_year

def authenticate_user(user, message):
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    authorization_url = auth.get_authorization_url()
    authorization_url += '&force_login=true'
    raw_input(message)
    print authorization_url
    verifier = raw_input("Please enter the PIN from Twitter to complete the authorization process: ")

    try:
        key, secret = auth.get_access_token(verifier)
    except tweepy.TweepError:
        sys.exit('Authentication Error\n')

    return auth.get_username(), key, secret

def get_details():
    if platform.system() is not "Darwin":
        Config = ConfigParser.ConfigParser()
        Config.read(config_filename)
        return Config.get("current", "username"), Config.get("current", "key"), Config.get("current", "secret"), Config.get("olde", "username"), Config.get("olde", "key"), Config.get("olde", "secret")
    else:
        return sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6], sys.argv[7]

def install():
    username, key, secret = authenticate_user('user', 'Press Enter to authenticate your current account with Twitter...')
    olde_username, olde_key, olde_secret = authenticate_user('olde_user', 'Press Enter to authenticate the year olde account with Twitter...')

    if platform.system() is not "Darwin":
        Config = ConfigParser.ConfigParser()
        # write the olde details
        Config.add_section("olde")
        Config.set("olde", "username", olde_username)
        Config.set("olde", "key", olde_key)
        Config.set("olde", "secret", olde_secret)
        #write the current details
        Config.add_section("current")
        Config.set("current", "username", username)
        Config.set("current", "key", key)
        Config.set("current", "secret", secret)
        # save the config file
        cfgfile = open(config_filename, 'w')
        Config.write(cfgfile)
        cfgfile.close()
    else:
        string = ""

        # read from the plist
        with open(os.path.realpath(plist), 'r') as f:
            string = f.read()

        # replace the plist strings
        string = string.replace("%PYTHON%", os.popen('which python').read().strip())
        string = string.replace("%SCRIPT%", os.path.realpath('twolde.py'))
        string = string.replace("%LOG_FILE%", os.path.expanduser('~/Library/Logs/twolde.log'))
        string = string.replace("%USER_USERNAME%", username)
        string = string.replace("%USER_TOKEN_KEY%", key)
        string = string.replace("%USER_TOKEN_KEY_SECRET%", secret)
        string = string.replace("%OLDE_USER_USERNAME%", olde_username)
        string = string.replace("%OLDE_USER_TOKEN_KEY%", olde_key)
        string = string.replace("%OLDE_USER_TOKEN_KEY_SECRET%", olde_secret)

        if os.path.isfile(os.path.expanduser('~/Library/LaunchAgents/' + plist)):
            os.popen('launchctl unload -w ' + os.path.expanduser('~/Library/LaunchAgents/' + plist))

        # write the plist
        with open(os.path.expanduser('~/Library/LaunchAgents/' + plist), 'w') as f:
            string = f.write(string)

        # don't wait for a restart for launchd to notice this
        os.system('chmod a+x twolde.py')
        os.popen('launchctl load -w ' + os.path.expanduser('~/Library/LaunchAgents/' + plist))

def uninstall():
    if os.path.isfile(os.path.expanduser('~/Library/LaunchAgents/' + plist)):
        os.popen('launchctl unload -w ' + os.path.expanduser('~/Library/LaunchAgents/' + plist))
        os.popen('rm ' + os.path.expanduser('~/Library/LaunchAgents/' + plist))


def run():
    print '\n\n===Twolde==='

    try:
        username, key, secret, olde_username, olde_key, olde_secret = get_details()
    except ConfigParser.NoSectionError:
        sys.exit('Error: did you remember to python twolde.py install?\n')

    new_auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    new_auth.set_access_token(key, secret)
    new_api = tweepy.API(new_auth)

    olde_auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    olde_auth.set_access_token(olde_key, olde_secret)
    olde_api = tweepy.API(olde_auth)

    s = sched.scheduler(time.time, time.sleep)

    now, last_year = get_times()
    best = now

    max_id = None
    user_timeline = tweepy.models.ResultSet()
    index = 0

    # iterate back through pages of 200 tweets until
    # the last tweet is more than a year ago
    while best > last_year:
        if max_id:
            user_timeline += new_api.user_timeline(
                screen_name=username, count=200, include_rts=1,
                max_id=(max_id - 1))
        else:
            user_timeline += new_api.user_timeline(
                screen_name=username, count=200, include_rts=1)

        index = len(user_timeline) - 1

        best = user_timeline[index].created_at
        max_id = user_timeline[index].id

        if best < last_year:
            # go forward through the tweets until
            # we find the first one since a year ago
            while best < last_year:
                index -= 1
                best = user_timeline[index].created_at

            while index >= 0:
                next_tweet = user_timeline[index]

                now, last_year = get_times()
                sleep_seconds = (
                    next_tweet.created_at - last_year).total_seconds()

                print 'Next tweet: "{}"'.format(
                    next_tweet.text.encode('utf-8'))
                print 'Next tweet time: {} (in {} seconds)'.format(
                    next_tweet.created_at.ctime(), sleep_seconds)

                # do retweets properly
                if next_tweet.retweeted:
                    s.enter(max(1, sleep_seconds), 1, do_retweet,
                            [olde_api, next_tweet.retweeted_status.id])
                else:
                    s.enter(max(1, sleep_seconds), 1, do_tweet,
                            [olde_api, next_tweet.text,
                             next_tweet.in_reply_to_user_id])

                s.run()

                index -= 1

            # we've run out of tweets since we started so start again
            user_timeline = tweepy.models.ResultSet()
            max_id = None
            best, last_year = get_times()

    print "I'm finished!"


def usage():
    sys.exit('Usage:\nInstall: twolde.py install\nUninstall: twolde.py rm\n')


def do_retweet(api, id):
    api.retweet(id=id)


def do_tweet(api, text, in_reply_to_user_id):
    api.update_status(status=text, in_reply_to_user_id=in_reply_to_user_id)


if __name__ == '__main__':
    # very basic argument parsing
    if len(sys.argv) < 2:
        usage()
    elif sys.argv[1] == "install":
        install()
    elif sys.argv[1] == "rm":
        uninstall()
    elif sys.argv[1] == "run":
        run()
    else:
        usage()
