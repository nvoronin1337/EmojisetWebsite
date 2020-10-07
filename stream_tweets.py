# coding=UTF-8
from twarc import Twarc
import traceback
import time
import emoji
from emojiset_app import EMOJI_SET
import regex
import twitter_credentials
from rq import get_current_job


class Tweet_Streamer():
    def __init__(self, target_list, max_tweets):
        self.consumer_key = twitter_credentials.CONSUMER_KEY
        self.consumer_secret = twitter_credentials.CONSUMER_SECRET
        self.access_token = twitter_credentials.ACCESS_TOKEN
        self.access_token_secret = twitter_credentials.ACCESS_TOKEN_SECRET
        self.twarc = Twarc(self.consumer_key, self.consumer_secret, self.access_token, self.access_token_secret)

        self.target_list = target_list
        self.keep_streaming = True
        self.max_tweets = max_tweets
        self.job = get_current_job()
        self.current_tweets = 0
        
        self.result = {}

    def stream(self):
        while self.keep_streaming:
            try:
                self.get_tweet_stream()
            except KeyboardInterrupt:
                print("Keyboard interrupt...")
                # Handle cleanup (save data, etc)
                return
            except Exception:
                print("Error. Restarting...")
                traceback.print_exc()
                time.sleep(5)
                pass
            
    def get_tweet_stream(self):
        discarded = 0
        if len(self.target_list) > 0:
            query = self.target_list
            for tweet in self.twarc.filter(track = query):
                if self.contains_emoji(tweet):
                    self.process_tweet(tweet)
                    self.current_tweets += 1
                    self.job.meta['progress'] = (self.current_tweets / self.max_tweets) * 100
                    self.job.save_meta()
                    if self.current_tweets >= self.max_tweets:
                        self.keep_streaming = False
                        return     
                else:
                    discarded += 1
                    self.job.meta['discarded_tweets'] = discarded
                    self.job.save_meta()
        else:
            print("Getting 1% sample.")
            for tweet in self.twarc.sample():
                if self.contains_emoji(tweet):
                    self.process_tweet(tweet)    
                    self.current_tweets += 1
                    self.job.meta['progress'] = (self.current_tweets / self.max_tweets) * 100
                    self.job.save_meta()
                    if self.current_tweets >= self.max_tweets:
                        self.keep_streaming = False
                        return     
                else:
                    discarded += 1
                    self.job.meta['discarded_tweets'] = discarded
                    self.job.save_meta()

    def contains_emoji(self, tweet):
        if "text" in tweet:
            grapheme_clusters = regex.findall(r"\X", tweet["text"])
            for cluster in grapheme_clusters:
                if cluster in EMOJI_SET:
                    return True
        return False

    def process_tweet(self, tweet):
        if "text" in tweet:
            emojiset = self.extract_emoji_sequences(tweet["text"])
            self.result[tweet["text"]] = emojiset

    #function returns emojiset list consisting of emoji sequences
    def extract_emoji_sequences(self, text):
        emoji_sequence = []
        emojiset_str = '['

        grapheme_clusters = regex.findall(r"\X", text)
        
        for cluster in grapheme_clusters:
            if cluster in EMOJI_SET:
                emoji_sequence.append(cluster)
            else:
                if(len(emoji_sequence) > 0):
                    emojiset_str += "[" + ", ".join(emoji_sequence) + "], "
                    emoji_sequence = []

        if(len(emoji_sequence) > 0):
            emojiset_str += "[" + ", ".join(emoji_sequence) + "]"
        else:
            if(len(emojiset_str) > 1):
                emojiset_str = emojiset_str[:-2]
        
        emojiset_str += ']'

        return emojiset_str
