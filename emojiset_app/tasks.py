from stream_tweets import Tweet_Streamer
from emojiset_app.utils import debug

# --- uses TweetStreamer and returns result (dictionaty ==> index:(tweet_text, emojiset))
def stream_task(keys, keywords, discard, twarc_method, languages, result_type, follow, geo, tweet_amount=None, finish_time=None):
    streamer = Tweet_Streamer(keys, keywords, discard, twarc_method, languages, result_type, follow, geo, tweet_amount, finish_time)
    streamer.stream()
    return streamer.result
