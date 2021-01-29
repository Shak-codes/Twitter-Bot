import discord, tweepy, twitter_credentials, key, os, ibm_watson, matplotlib
from discord.ext import commands
import asyncio
import nest_asyncio
from tweepy import API 
from tweepy import Cursor
from tweepy import OAuthHandler
from tweepy import Stream
from tweepy import StreamListener
import pandas as pd
from ibm_watson import PersonalityInsightsV3
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
import json
from matplotlib import pyplot as plt 
import seaborn as sns

auth = tweepy.OAuthHandler(twitter_credentials.consumer_key, twitter_credentials.consumer_key_secret)
auth.set_access_token(twitter_credentials.access_token, twitter_credentials.access_token_secret)
api = tweepy.API(auth)

client = commands.Bot(command_prefix = ".")

@client.event
async def on_ready():
    print("Twitter bot is ready")  

@client.command()
async def bio(ctx, screen_name):
    user = api.get_user(screen_name)

    name = user.name 
    user_url = "https://www.twitter.com/" + screen_name
    description = user.description 
    location = user.location
    verified = user.verified
    if location == "": 
        location = "This user has not set a location" 
    else: 
        None 
    followers_count = user.followers_count
    created_at = user.created_at 
    tweet_count = user.statuses_count  
    following_count = user.friends_count
    try:
        profile_image = user.profile_image_url
    except:
        profile_image = "No image" 
    try:
        profile_banner = user.profile_banner_url
    except:
        profile_banner = "No banner" 


    embed = discord.Embed(
        title = name,
        url = user_url,
        description = description,
        colour = discord.Color.green()
    )
    if profile_image != "No image":
        embed.set_thumbnail(url=profile_image)
    embed.add_field(name='Created', value=created_at)
    embed.add_field(name='Location', value=location)
    embed.add_field(name='Verified', value=verified)
    embed.add_field(name='Followers', value=followers_count)
    embed.add_field(name='Following', value=following_count)
    embed.add_field(name='Tweets', value=tweet_count)
    if profile_banner != "No banner":
        embed.set_image(url=profile_banner)

    await ctx.send(embed=embed)

@client.command()
async def search(ctx, tag):
    users = api.search_users(tag) 
    lst = ""
    for user in users:
        lst += user.screen_name + "\n"
    lst = lst.replace("_", "\_")

    embed = discord.Embed(
        title = "A list of users related to the keyword, " + tag,
        description = str(lst),
        colour = discord.Color.green()
    )
    await ctx.send(embed=embed)

@client.command()
async def personality(ctx, handle):
    res = api.user_timeline(screen_name=handle, count = 200, include_rts=False)
    tweets = [tweet.text for tweet in res]
    text = ''.join(str(tweet) for tweet in tweets)
    api_key = "XKYbW497LMgbmz7d5mbZPo2gl0NIOy2Xt-5l2wXMdNTi"
    url = "https://api.us-east.personality-insights.watson.cloud.ibm.com/instances/ec6e8bd3-4402-4a2a-90f5-1f128c604c72"

    authenticator = IAMAuthenticator(api_key)
    personality_insights = PersonalityInsightsV3(
    version='2017-10-13',
    authenticator=authenticator
    )
    personality_insights.set_service_url(url)

    profile = personality_insights.profile(text, accept='application/json').get_result()

    needs = profile['needs']
    result = {need['name']:need['percentile'] for need in needs}
    df = pd.DataFrame.from_dict(result, orient='index')
    df.reset_index(inplace=True)
    df.columns = ['need', 'percentile']
    plt.figure(figsize=(15,5))
    sns.barplot(y='percentile', x='need', data=df).set_title('Needs')
    plt.savefig('Needs.png')
    plt.close()
    image = discord.File("Needs.png")
    await ctx.send(file=image)

@client.command()
async def latest(ctx, handle):
    user = api.get_user(handle)
    res = api.user_timeline(screen_name=handle, count = 1, include_rts=False)[0]
    tweet = res.text
    time = res.created_at
    likes = res.favorite_count
    retweets = res.retweet_count
    language = res.lang
    source = res.source
    user_url = "https://www.twitter.com/" + handle
    name = user.name 
    #sensitive = res.possibly_sensitive
    try:
        profile_image = user.profile_image_url
    except:
        profile_image = "No image" 

    embed = discord.Embed(
        title = name,
        url = user_url,
        description = str(tweet),
        colour = discord.Color.green()
    )
    if profile_image != "No image":
        embed.set_thumbnail(url=profile_image)
    embed.add_field(name='Created', value=time)
    embed.add_field(name='Language', value=language)
    embed.add_field(name='Source', value=source)
    embed.add_field(name='Replying to', value=res.in_reply_to_screen_name)
    embed.add_field(name='Likes', value=likes)
    embed.add_field(name='Rewteets', value=retweets)
    await ctx.send(embed=embed)

class StdOutListener(tweepy.StreamListener):
    """ A listener handles tweets that are received from the stream.
    This is a basic listener that just prints received tweets to stdout.
    """

    def on_status(self, status):
        self.process_status(status)
        return True

    def process_status(self, status):
        nest_asyncio.apply(asyncio.run(post(status.user.name, 743586017369653306)))

    def on_error(self, status):
        return False

@client.command()
async def follow(ctx, term):
    l = StdOutListener()
    stream = Stream(auth, l)
    stream.filter(track=[term])

async def post(msg, channel_id):
    global bot 
    channel = bot.get_channel(channel_id)
    await channel.send(msg)

client.run(key.twitter_key)