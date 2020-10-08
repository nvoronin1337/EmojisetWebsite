from twarc import Twarc
import traceback
import time
import emoji
from emojiset_app import EMOJI_SET
import regex
import twitter_credentials
from rq import get_current_job


class Tweet_Streamer():
    def __init__(self, keywords, max_tweets, discard):
        # Configuring Twarc API
        self.consumer_key = twitter_credentials.CONSUMER_KEY
        self.consumer_secret = twitter_credentials.CONSUMER_SECRET
        self.access_token = twitter_credentials.ACCESS_TOKEN
        self.access_token_secret = twitter_credentials.ACCESS_TOKEN_SECRET
        
        self.twarc = Twarc(self.consumer_key, self.consumer_secret, self.access_token, self.access_token_secret)

        self.keywords = keywords
        self.max_tweets = max_tweets
        self.discard = discard

        self.job = get_current_job()
        self.keep_streaming = True
        self.current_tweets = 0
        self.discarded = 0

        # dicrionaty in the format {tweet: emojiset}
        self.result = {}

    # Main streaming loop 
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

    # Begin streaming tweets 
    def get_tweet_stream(self):
        if len(self.keywords) > 0:
            query = self.keywords
            for tweet in self.twarc.search(query):
                self.process_tweet(tweet)
                if self.current_tweets >= self.max_tweets:
                    self.keep_streaming = False
                    break
        else:
            print("Getting 1% sample.")
            for tweet in self.twarc.sample():
                self.process_tweet(tweet)
                if self.current_tweets >= self.max_tweets:
                    self.keep_streaming = False
                    break

    def process_tweet(self, tweet):
        if self.discard:
            if self.contains_emoji(tweet):
                self.map_tweet_to_emojiset(tweet)
                self.current_tweets += 1
                self.job.refresh()
                self.job.meta['progress'] = (self.current_tweets / self.max_tweets) * 100
                self.job.save_meta()
            else:
                self.discarded += 1
                self.job.refresh()
                self.job.meta['discarded_tweets'] = self.discarded
                self.job.save_meta()
        else:
            self.map_tweet_to_emojiset(tweet)
            self.current_tweets += 1
            self.job.refresh()
            self.job.meta['progress'] = (self.current_tweets / self.max_tweets) * 100
            self.job.save_meta()

    def contains_emoji(self, tweet):
        if "full_text" in tweet:
            grapheme_clusters = regex.findall(r"\X", tweet["full_text"])
            for cluster in grapheme_clusters:
                if cluster in EMOJI_SET:
                    return True
        return False

    def map_tweet_to_emojiset(self, tweet):
        if "full_text" in tweet:
            emojiset = self.extract_emoji_sequences(tweet["full_text"])
            self.result[tweet["full_text"]] = emojiset

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
