from twarc import Twarc
import traceback
import time
import emoji
from emojiset_app import EMOJI_SET
import regex
import twitter_credentials
from rq import get_current_job


def debug(var):
    with open('out.txt', 'w') as f:
        print(var, file=f)     


class Tweet_Streamer():
    def __init__(self, keywords, max_tweets, discard, twarc_method, lang):
        # Configuring Twarc API
        self.consumer_key = twitter_credentials.CONSUMER_KEY
        self.consumer_secret = twitter_credentials.CONSUMER_SECRET
        self.access_token = twitter_credentials.ACCESS_TOKEN
        self.access_token_secret = twitter_credentials.ACCESS_TOKEN_SECRET
        
        self.twarc = Twarc(self.consumer_key, self.consumer_secret, self.access_token, self.access_token_secret)

        self.keywords = keywords
        self.max_tweets = max_tweets
        self.discard = discard
        self.twarc_method = twarc_method
        self.lang = lang

        self.job = get_current_job()
        self.keep_streaming = True
        self.current_tweets = 0
        self.discarded = 0

        self.text = "text"

        # dicrionaty in the format {index: (tweet, emojiset)}
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
        if self.twarc_method == "search":
            self.text = "full_text"
            query = self.keywords.replace(",", " OR ")
            for tweet in self.twarc.search(query, lang=self.lang):
                self.process_tweet(tweet)
                if self.current_tweets >= self.max_tweets:
                    break
        elif self.twarc_method == "filter":
            query = self.keywords
            tweet_received = False
            search_query = query.replace(",", " OR ")
            for tweet in self.twarc.search(search_query, lang=self.lang):
                tweet_received = True
                break     
            if tweet_received:
                for tweet in self.twarc.filter(track=query, lang=self.lang):
                    self.process_tweet(tweet)
                    if self.current_tweets >= self.max_tweets:
                        break
        elif self.twarc_method == "sample":
            for tweet in self.twarc.sample():
                self.process_tweet(tweet)
                if self.current_tweets >= self.max_tweets:
                    break
        self.keep_streaming = False

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
        if self.text in tweet:
            grapheme_clusters = regex.findall(r"\X", tweet[self.text])
            for cluster in grapheme_clusters:
                if cluster in EMOJI_SET:
                    return True
        return False

    def map_tweet_to_emojiset(self, tweet):
        if self.text in tweet:
            emojiset = self.extract_emoji_sequences(tweet[self.text])
            self.result[self.current_tweets] = (tweet[self.text], emojiset)
            

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
