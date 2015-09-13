#!/usr/bin/env python

import argparse
import os
import sys
import tweepy
import time
import sched
from datetime import datetime
from HTMLParser import HTMLParser
import ConfigParser

CONFIG_FILENAME = 'config.ini'

CONSUMER_KEY = 'i4VfqFLIY7E08Ros9AhA'
CONSUMER_SECRET = 'XP0JjlMMPtaC0IOvHv6VXzE31izdiUy1rXcoPeYg'

PLIST = 'uk.co.mobbler.twolde.plist'
PLIST_PATH = '~/Library/LaunchAgents/' + PLIST


def get_times():
    now = datetime.utcnow()
    last_year = datetime(now.year - 1, now.month, now.day, now.hour,
                         now.minute, now.second, now.microsecond, now.tzinfo)
    return now, last_year


def authenticate_user(message):
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    authorization_url = auth.get_authorization_url()
    authorization_url += '&force_login=true'
    raw_input(message)
    print authorization_url
    verifier = raw_input("Please enter the PIN from Twitter to complete the "
                         "authorization process: ")

    try:
        key, secret = auth.get_access_token(verifier)
    except tweepy.TweepError:
        sys.exit('Authentication Error\n')

    return auth.get_username(), key, secret


def get_details():
    config = ConfigParser.ConfigParser()
    config.read(CONFIG_FILENAME)
    return (
        config.get("current", "username"),
        config.get("current", "key"),
        config.get("current", "secret"),
        config.get("olde", "username"),
        config.get("olde", "key"),
        config.get("olde", "secret"))


def install():
    username, key, secret = authenticate_user(
        'Press Enter to authenticate your current account with Twitter...')
    olde_username, olde_key, olde_secret = authenticate_user(
        'Press Enter to authenticate the year olde account with Twitter...')

    config = ConfigParser.ConfigParser()
    # write the olde details
    config.add_section("olde")
    config.set("olde", "username", olde_username)
    config.set("olde", "key", olde_key)
    config.set("olde", "secret", olde_secret)
    # write the current details
    config.add_section("current")
    config.set("current", "username", username)
    config.set("current", "key", key)
    config.set("current", "secret", secret)
    # save the config file
    cfgfile = open(CONFIG_FILENAME, 'w')
    config.write(cfgfile)
    cfgfile.close()


def uninstall():
    if os.path.isfile(os.path.expanduser(PLIST_PATH)):
        os.popen('launchctl unload -w ' +
                 os.path.expanduser(PLIST_PATH))
        os.popen('rm ' + os.path.expanduser(PLIST_PATH))


def run():
    print '\n\n===Twolde==='

    try:
        username, key, secret, olde_username, olde_key, olde_secret = get_details()
    except ConfigParser.NoSectionError:
        sys.exit('Error: did you remember to python twolde.py install?\n')

    new_auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    new_auth.set_access_token(key, secret)
    new_api = tweepy.API(new_auth)

    olde_auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    olde_auth.set_access_token(olde_key, olde_secret)
    olde_api = tweepy.API(olde_auth)

    scheduler = sched.scheduler(time.time, time.sleep)

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
                print 'Next tweet time: {} UTC (in {})'.format(
                    next_tweet.created_at.ctime(), nice_time(sleep_seconds))

                # do retweets properly
                if next_tweet.retweeted:
                    scheduler.enter(
                        max(1, sleep_seconds), 1, do_retweet,
                        [olde_api, next_tweet.retweeted_status.id])
                else:
                    scheduler.enter(
                        max(1, sleep_seconds), 1, do_tweet,
                        [olde_api, HTMLParser().unescape(next_tweet.text), next_tweet.in_reply_to_status_id])

                scheduler.run()

                index -= 1

            # we've run out of tweets since we started so start again
            user_timeline = tweepy.models.ResultSet()
            max_id = None
            best, last_year = get_times()

    print "I'm finished!"


def do_retweet(api, status_id):
    api.retweet(id=status_id)


def do_tweet(api, text, in_reply_to_status_id):
    api.update_status(status=text, in_reply_to_status_id=in_reply_to_status_id)


def pluralise(quantity, unit):
    """
    Assumes we can pluralise by simply appending an S.
    quantity is an integer like 2.
    unit is a string like "hour".
    """
    if quantity > 1:
        return str(quantity) + " " + unit + "s"
    else:
        return str(quantity) + " " + unit


def nice_time(seconds):
    """Seconds in a more readable format"""
    minutes, seconds = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        text = (pluralise(hours, "hour") + ", " +
                pluralise(minutes, "minute") + ", " +
                pluralise(seconds, "second"))
    elif minutes:
        text = (pluralise(minutes, "minute") + ", " +
                pluralise(seconds, "second"))
    else:
        text = (pluralise(seconds, "second"))
    return text


def main():
    """ main """
    parser = argparse.ArgumentParser(description='')
    parser.add_argument(
        dest='command',
        choices=['install', 'run', 'remove'],
        help='the twolde command to run')
    args = parser.parse_args()

    # very basic argument parsing
    if args.command == "install":
        install()
    elif args.command == "rm":
        uninstall()
    elif args.command == "run":
        run()


if __name__ == '__main__':
    main()
