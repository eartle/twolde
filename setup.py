#!/usr/bin/env python

from distutils.core import setup

setup(name='twolde',
      version='0.1.0',
      description='Tweets from a year ago!',
      author='Michael Coffey',
      author_email='eartle@github.com',
      url='https://github.com/eartle/twolde',
      scripts=['scripts/twolde'],
      install_requires=[
          'Tweepy'
      ])
