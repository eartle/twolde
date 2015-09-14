# Twolde – It's like Twitshift, but for people who prefer Twolde

This a tool that will tweet your tweets from one year ago to another account.

To use Twolde you will first need to install its dependancy <a href="https://github.com/tweepy/tweepy">Tweepy</a>.

You will then need to clone this repository and run twolde.py in a terminal like this:

```
python twolde.py install
```

You will be asked to authenticate with Twitter and then enter the verification code that Twitter presents to you, first with your main account and then with the account that you want your year old tweets to go to.

To run Twolde you'll need to do this

```
python twolde.py run
```

You'll probably want to run this in a screen session on a server, or something, as it'll run until you haven't tweeted for a year.

If you decide you don't want Twolde to run anymore you can uninstall like this:

```
python twolde.py rm
```

## Tech notes

* Your year old account will only be updated while the machine you've got twolde installed on is running
* Won't work if you tweet more than 3200 times a year

## TODO

* Have a configurable number of years in the past
* Deal with leap years nicely (It's march so we should be okay for a while)
* add a setup.py so this can be pip installed
