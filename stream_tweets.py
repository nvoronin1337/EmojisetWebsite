from twarc import Twarc
import traceback
import time
import emoji
from emojiset_app import EMOJI_SET
import regex
import twitter_credentials
from rq import get_current_job  


# ---converts error to txt file and immediately outputs---*
def debug(var):
    with open('out.txt', 'w') as f:
        print(var, file=f)


class Tweet_Streamer():
    def __init__(self, keywords, max_tweets, discard, twarc_method, lang, result_type, follow, geo):
        # ---Configuring Twarc API---*
        self.consumer_key = twitter_credentials.CONSUMER_KEY
        self.consumer_secret = twitter_credentials.CONSUMER_SECRET
        self.access_token = twitter_credentials.ACCESS_TOKEN
        self.access_token_secret = twitter_credentials.ACCESS_TOKEN_SECRET
        self.twarc = Twarc(self.consumer_key, self.consumer_secret, self.access_token, self.access_token_secret, http_errors=1, connection_errors=3)

        # ---Save paramaeters passed to the constructor
        self.keywords = keywords
        self.max_tweets = max_tweets
        self.discard = discard
        self.twarc_method = twarc_method
        self.lang = lang
        self.result_type = result_type
        self.follow = follow
        if self.follow:
            self.follow = self.follow.replace('@', '').replace(' ', "").split(',')
        self.geo = geo

        self.user_ids = []
        self.job = get_current_job()
        self.current_tweets = 0
        self.discarded = 0
        self.text = "text"

        # ---dictionaty in the format {index: (tweet, emojiset)}---*
        self.result = {}

    def stream(self):
         # ---stream tweets---*
        try:
            self.get_tweet_stream()
        # ---error handling---*
        except KeyboardInterrupt:
            print("Keyboard interrupt...")
            return
        except Exception:
            print("Error. Quitting...")
            traceback.print_exc()
            return

    def get_tweet_stream(self):
        # ---search function---*
        if self.twarc_method == "search":
            self.text = "full_text"
            query = self.keywords
            # ---process function in regards to other user-options---*
            for tweet in self.twarc.search(query, lang=self.lang, result_type=self.result_type, geocode=self.geo):
                self.process_tweet(tweet)
                if self.current_tweets >= self.max_tweets:
                    break
        # ---filter function---*
        elif self.twarc_method == "filter":
            query = self.keywords
            tweet_received = False
            search_query = query
            if self.follow:
                # ---finds user based on their user ID (must be found through user_lookup, and is the only way to track specific users)---*
                for user in self.twarc.user_lookup(ids=self.follow, id_type="screen_name"):
                    self.user_ids.append(user['id_str']) 
            elif not self.geo:
                if search_query:
                    # ---if username and location were not specified, check if the keywords are not random by trying to find one tweet matching the keyword---*
                    for tweet in self.twarc.search(search_query, lang=self.lang):
                        tweet_received = True
                        break
            if tweet_received or self.follow or self.geo:
                for tweet in self.twarc.filter(track=query, lang=self.lang, follow=",".join(self.user_ids), locations=self.geo):
                    self.process_tweet(tweet)
                    if self.current_tweets >= self.max_tweets:
                        break
        # ---sample function---*    
        elif self.twarc_method == "sample":
            for tweet in self.twarc.sample():
                self.process_tweet(tweet)
                if self.current_tweets >= self.max_tweets:
                    break

    # ---extract emojiset, update progress bar, discard tweets without emojis, output # of discarded tweets---*
    def process_tweet(self, tweet):
        if self.discard:                                                                       
            if self.contains_emoji(tweet):
                self.map_tweet_to_emojiset(tweet)
                self.current_tweets += 1                                                       # counter of tweets w/ emojis to update progress bar*
                self.job.refresh()                                                             # refreshes progress bar every 150 milliseconds (established in main.js)*
                self.job.meta['progress'] = (self.current_tweets / self.max_tweets) * 100      # updates progress bar (tweets with emojis / # of specified tweets) as a percentage*
                self.job.save_meta()                                                           # saves new update to progress bar*
            else:
                self.discarded += 1                                                            # counter of tweets w/o emojis*
                self.job.refresh()                                                             # refreshes # of discarded tweets every 150 milliseconds (established in main.js)*
                self.job.meta['discarded_tweets'] = self.discarded                             
                self.job.save_meta()                                                           # saves new update to # of discarded tweets message*
        else:                                                                                  
            self.map_tweet_to_emojiset(tweet)
            self.current_tweets += 1
            self.job.refresh()
            self.job.meta['progress'] = (self.current_tweets / self.max_tweets) * 100
            self.job.save_meta()

    # ---checks to see if any emojis are grapheme clusters and returns the emoji based on the ZWJ sequence---*
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
            self.result[self.current_tweets] = (tweet[self.text], emojiset)                  # sets current tweet to dictionary {tweet, emojiset}*
            

    # ---function returns emojiset list consisting of emoji sequences (a string looking like python list of lists)---*
    def extract_emoji_sequences_with_brackets(self, text):
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

    # ---function returns emojiset list consisting of emoji sequences (a string) ; sets are separated by any character that isn't an emoji---*
    def extract_emoji_sequences(self, text):
        emoji_sequence = []
        emojiset_str = ""

        grapheme_clusters = regex.findall(r"\X", text)         # checks to see if subsequent emojis are grapheme clusters*
        
        for cluster in grapheme_clusters:                      # appends correct grapheme for emoji based on their ZWJ sequence to emoji sequence array*
            if cluster in EMOJI_SET:
                emoji_sequence.append(cluster)
            else:
                if(len(emoji_sequence) > 0):                   # appends emojis to string and empties array*
                    emojiset_str += "".join(emoji_sequence)
                    emojiset_str += ","                                                             
                    emoji_sequence = []

        if(len(emoji_sequence) > 0):                           # appends non-grapheme emojis to string*
            emojiset_str += "".join(emoji_sequence)
            emojiset_str += ","

        if len(emojiset_str) > 1:                              # removes comma from end of string*
            emojiset_str = emojiset_str[:-1]
        

        return emojiset_str                                    # returns emoji sequence as a string*

