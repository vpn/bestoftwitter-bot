# -*- coding: utf-8 -*-

'''
Copyright 2015 Randal S. Olson

This file is part of the reddit Twitter Bot library.

The reddit Twitter Bot library is free software: you can redistribute it and/or
modify it under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your option)
any later version.

The reddit Twitter Bot library is distributed in the hope that it will be
useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public
License for more details. You should have received a copy of the GNU General
Public License along with the reddit Twitter Bot library.
If not, see http://www.gnu.org/licenses/.
'''

import praw
import json
import requests
import tweepy
import time
import os
import re
import urllib.parse
from glob import glob
from imgurpython import ImgurClient

#Place your Reddit API keys here
REDDIT_AGENT = ''
REDDIT_CLIENT_SECRET = ''

# Place your Twitter API keys here
ACCESS_TOKEN = ''
ACCESS_TOKEN_SECRET = ''
CONSUMER_KEY = ''
CONSUMER_SECRET = ''

# Place your alt Twitter API keys here (for credit tweets)
ALT_ACCESS_TOKEN = ''
ALT_ACCESS_TOKEN_SECRET = ''
ALT_CONSUMER_KEY = ''
ALT_CONSUMER_SECRET = ''

# Place your Imgur API keys here
IMGUR_CLIENT_ID = ''
IMGUR_CLIENT_SECRET = ''
imgur = ImgurClient(IMGUR_CLIENT_ID, IMGUR_CLIENT_SECRET)

# Place the subreddit you want to look up posts from here
SUBREDDIT_TO_MONITOR = 'me_irl'

# Place the name of the folder where the images are downloaded
IMAGE_DIR = 'img'

# Place the name of the file to store the IDs of posts that have been posted
POSTED_CACHE = 'posted_posts.txt'

# Place the string you want to add at the end of your tweets (can be empty)
TWEET_SUFFIX = ' '

# Place the maximum length for a tweet
TWEET_MAX_LEN = 140

# Place the time you want to wait between each tweets (in seconds)
DELAY_BETWEEN_TWEETS = 600

# Place the lengths of t.co links (cf https://dev.twitter.com/overview/t.co)
T_CO_LINKS_LEN = 24

def setup_connection_reddit(subreddit):
  ''' Creates a connection to the reddit API. '''
  print('[bot] Setting up connection with reddit')
  # API fix thanks to https://github.com/rhiever/reddit-twitter-bot/issues/11
  reddit_api = praw.Reddit(
    user_agent='reddit Twitter tool monitoring {}'.format(subreddit),
    client_id=REDDIT_AGENT,
    client_secret=REDDIT_CLIENT_SECRET)
  return reddit_api.subreddit(subreddit)
  #reddit_api = praw.Reddit('reddit Twitter tool monitoring {}'.format(subreddit))
  #return reddit_api.get_subreddit(subreddit)


def tweet_creator(subreddit_info):
  ''' Looks up posts from reddit and shortens the URLs to them. '''
  post_dict = {}
  post_ids = []

  print('[bot] Getting posts from reddit')

  # You can use the following "get" functions to get posts from reddit:
  #   - get_top(): gets the most-upvoted posts (ignoring post age)
  #   - get_hot(): gets the most-upvoted posts (taking post age into account)
  #   - get_new(): gets the newest posts
  #
  # "limit" tells the API the maximum number of posts to look up

  for submission in subreddit_info.hot(limit=25):
    if not already_tweeted(submission.id):
      # This stores a link to the reddit post itself
      # If you want to link to what the post is linking to instead, use
      # "submission.url" instead of "submission.permalink"
      post_dict[submission.title] = {}
      post = post_dict[submission.title]
      post['link'] = submission.url

      # Store the url the post points to (if any)
      # If it's an imgur URL, it will later be downloaded and uploaded alongside the tweet
      post['img_path'] = get_image(submission.url)

      post_ids.append(submission.id)
    else:
      print('[bot] Already tweeted: {}'.format(str(submission)))

  return post_dict, post_ids


def already_tweeted(post_id):
  ''' Checks if the reddit Twitter bot has already tweeted a post. '''
  found = False
  with open(POSTED_CACHE, 'r') as in_file:
    for line in in_file:
      if post_id in line:
        found = True
        break
  return found


def strip_title(title, num_characters):
  ''' Shortens the title of the post to the 140 character limit. '''

  # How much you strip from the title depends on how much extra text
  # (URLs, hashtags, etc.) that you add to the tweet
  # Note: it is annoying but some short urls like "data.gov" will be
  # replaced by longer URLs by twitter. Long term solution could be to
  # use urllib.parse to detect those.
  if len(title) <= num_characters:
    return title
  else:
    return title[:num_characters - 1] + '…'


def get_image(img_url):
  ''' Downloads images that reddit posts may point to. '''
  if any(s in img_url for s in ('i.imgur.com', 'i.redd.it', 'i.reddituploads.com')):
    # This adds support for all imgur links (including galleries), but I need to make a new regex
    #if ('i.imgur.com' not in img_url) and ('imgur.com' in img_url):
      #print('[bot] Attempting to retrieve image URL for', img_url, 'from imgur...')
      #regex = r"(https?:\/\/imgur\.com\/a\/(.*?)(?:\/.*|$))"
      #m = re.search(regex, img_url, flags=0)
      #print(m.group(0))
      #img_url = imgur.get_image(img_url)
    file_name = os.path.basename(urllib.parse.urlsplit(img_url).path)
    file_extension = os.path.splitext(img_url)[-1].lower();
    # Fix for issue with i.reddituploads.com links not having a file extension in the URL
    if not file_extension:
      file_extension += '.jpg'
      file_name += '.jpg'
      img_url += '.jpg'
    img_path = IMAGE_DIR + '/' + file_name
    print('[bot] Downloading image at URL ' + img_url + ' to ' + img_path + ', file type identified as ' + file_extension)
    if ('gif' not in img_url) and ('gifv' not in img_url):
      resp = requests.get(img_url, stream=True)
      if resp.status_code == 200:
        with open(img_path, 'wb') as image_file:
          for chunk in resp:
            image_file.write(chunk)
        # Return the path of the image, which is always the same since we just overwrite images
        return img_path
        print('path:', img_path)
      else:
        print('[bot] Image failed to download. Status code: ' + resp.status_code)
  else:
    print('[bot] Post doesn\'t point to an image: ', img_url)
  return ''

# This replies to the primary tweet with credit to the reddit post
def alt_tweeter(post_id):
  ''' Tweets all of the selected reddit posts. '''
  auth = tweepy.OAuthHandler(ALT_CONSUMER_KEY, ALT_CONSUMER_SECRET)
  auth.set_access_token(ALT_ACCESS_TOKEN, ALT_ACCESS_TOKEN_SECRET)
  api = tweepy.API(auth)

  # There's probably a better way to do this, but it works
  latestTweets = api.user_timeline(screen_name = 'ItMeIRL', count = 1, include_rts = False)
  newestTweet = latestTweets[0].id

  # Get more submission info
  reddit = praw.Reddit(
    user_agent='me irl bot',
    client_id=REDDIT_AGENT,
    client_secret=REDDIT_CLIENT_SECRET)

  submission = reddit.submission(id=post_id)
  thread = submission.permalink
  if not submission.author.name:
    op = 'deleted user'
  else:
    op = submission.author.name

  # Compose the tweet
  tweetText = '@ItMeIRL Originally posted by /u/' + op + '. https://reddit.com' + thread
  print('[bot] Posting this on alt Twitter account: ', tweetText)
  api.update_status(tweetText, newestTweet)


def tweeter(post_dict, post_ids):
  ''' Tweets all of the selected reddit posts. '''
  auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
  auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
  api = tweepy.API(auth)

  for post, post_id in zip(post_dict, post_ids):
    img_path = post_dict[post]['img_path']

    extra_text = ' ' + post_dict[post]['link'] + TWEET_SUFFIX
    extra_text_len = 1 + T_CO_LINKS_LEN + len(TWEET_SUFFIX)
    if img_path:  # Image counts as a link
      extra_text_len += T_CO_LINKS_LEN
    post_text = strip_title(post, TWEET_MAX_LEN - extra_text_len)
    # Only send a tweet if there is a valid image, and the title contains both "me" and "irl"
    if (img_path) and ('me' in post_text) and ('irl' in post_text):
      print('[bot] Posting this on main Twitter account: ', post_text, img_path)
      api.update_with_media(filename=img_path, status=post_text)
      alt_tweeter(post_id)
    log_tweet(post_id)
    time.sleep(DELAY_BETWEEN_TWEETS)


def log_tweet(post_id):
  ''' Takes note of when the reddit Twitter bot tweeted a post. '''
  with open(POSTED_CACHE, 'a') as out_file:
    out_file.write(str(post_id) + '\n')


def main():
  ''' Runs through the bot posting routine once. '''
  # If the tweet tracking file does not already exist, create it
  if not os.path.exists(POSTED_CACHE):
    with open(POSTED_CACHE, 'w'):
      pass
  if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR)

  subreddit = setup_connection_reddit(SUBREDDIT_TO_MONITOR)
  post_dict, post_ids = tweet_creator(subreddit)
  tweeter(post_dict, post_ids)

  # Clean out the image cache
  for filename in glob(IMAGE_DIR + '/*'):
    os.remove(filename)

if __name__ == '__main__':
  while True:
    main()
    print('[bot] sleeping for', DELAY_BETWEEN_TWEETS, 'seconds')
    time.sleep(DELAY_BETWEEN_TWEETS)
    print('[bot] restarting main()...')