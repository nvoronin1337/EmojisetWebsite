from twarc import Twarc
import traceback
import time
import emoji
import regex
import twitter_credentials


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

    def process_tweet(self, status):
        if "text" in status:
            self.result[status["text"]] = self.emoji_split(status["text"])
            with open("Emojis.txt.", "a+", encoding="utf-8") as emoji_file:
                print("########################", file=emoji_file )
                print(self.result[status["text"]], file=emoji_file)
            

    def get_tweet_stream(self):
        if len(self.target_list) > 0:
            query = self.target_list
            print("Search: " + str(query))
            for tweet in self.twarc.filter(track = query):
                if self.contains_emoji(tweet):
                    self.process_tweet(tweet)
                    self.current_tweets += 1
                    if self.current_tweets >= self.max_tweets:
                        self.keep_streaming = False
                        return         
        else:
            print("Getting 1% sample.")
            for tweet in self.twarc.sample():
                if self.contains_emoji(tweet):
                    self.process_tweet(tweet)    
                    self.current_tweets += 1
                    if self.current_tweets >= self.max_tweets:
                        self.keep_streaming = False
                        return   

    def contains_emoji(self, tweet):
        if "text" in tweet:
            grapheme_clusters = regex.findall(r"\X", tweet["text"])
            for cluster in grapheme_clusters:
                if any(char in emoji.UNICODE_EMOJI for char in cluster):
                    return True
        return False

    def emoji_split(self, text):
        if text is None:
            return None

        emoji_list = []
        data = regex.findall(r'\X', text)

        for word in data:
            if any(char in emoji.UNICODE_EMOJI for char in word):
                emoji_list.append(word)

        if len(emoji_list) > 0:
            return emoji_list
        else:
            return None
