#Me IRL Bot

A Python bot that looks up images from the /r/me_irl subreddit and automatically posts them on Twitter. This was created for the [@ItMeIRL](https://twitter.com/ItMeIRL) account, heavily based on [reddit-twitter-bot](https://github.com/rhiever/reddit-twitter-bot).

##Disclaimer

I hold no liability for what you do with this script or what happens to you by using this script. Abusing this script *can* get you banned from Twitter, so make sure to read up on proper usage of the Twitter API.

##Dependencies

You will need to install the [tweepy](https://github.com/tweepy/tweepy), [PRAW](https://praw.readthedocs.org/en/), and [ImgurPython](https://github.com/Imgur/imgurpython) libraries first:

    pip install tweepy
    pip install praw
    pip install imgurpython
    
You will also need to create two app accounts on Twitter. One of them is used for posting images, and the other replying to every main tweet with credit to the original poster.

1. [Sign in with your Twitter account](https://dev.twitter.com/apps)
2. Create a new app account
3. Modify the settings for that app account to allow read & write
4. Generate a new OAuth token with those permissions
5. Manually edit this script and put those tokens in the script
6. Repeat for second account

In addition, you will have to create an application on Reddit:

1. Sign in with your Reddit account
2. Go to your [app preferences](https://www.reddit.com/prefs/apps) and create a new application at the bottom
3. Select the application type as 'script'
4. Manually edit this script with the token (seen below the name of the bot after it's generated) and the secret

The bot also requires Imgur API access, for future integration with Imgur:

1. Sign in with your Imgur account
2. Go to [Register an application](https://api.imgur.com/oauth2/addclient) and fill everything out
3. Imgur will then send you the client ID/secret via email, just paste it in the Imgur variables at the top of the script

##Usage

Once you edit the bot script to provide the necessary API keys and the subreddit you want to tweet from, you can run the bot on the command line:

    python me-irl-bot.py
 
Look into the script itself for configuration options of the bot. By default, the bot will ping Reddit for new posts every 600 seconds (10 minutes) and continue running in a loop.
