# Twolde – It's like Twitshift, but for people who prefer Twolde

This a tool that will tweet your tweets from one year ago to another account.

## Install

To install Twolde you'll need Python and then you can run `pip install git+git://github.com/eartle/twolde.git` which will install twolde as a Python package. You can then run `twolde install` which will ask you to authenticate with Twitter and then enter the verification code that Twitter presents to you, first with your main account and then with the account that you want your year old tweets to go to. This will store the Twitter access details for both accounts in a config file located here `~/.twolde/config.ini`. 

To run Twolde you'll need to do this `twolde run`. You'll probably want to run this in a screen session on a server, or something, as it'll run until you haven't tweeted for a year.

If you decide you don't want Twolde to run anymore you can uninstall like this `twolde rm` which will delete the config file where all your details are stored and then `pip uninstall twolde` to remove the script itself.

## Tech notes

* Your year old account will only be updated while the machine you've got twolde installed on is running
* Won't work if you tweet more than 3200 times a year

## TODO

* Have a configurable number of years in the past
* Deal with leap years nicely (It's march so we should be okay for a while)
