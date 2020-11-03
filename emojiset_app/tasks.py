from stream_tweets import Tweet_Streamer
from emojiset_app.utils import debug

# --- uses TweetStreamer and returns result (dictionaty ==> index:(tweet_text, emojiset))
def stream_task(keys, keywords, tweets_amount, discard, twarc_method, languages, result_type, follow, geo):
    streamer = Tweet_Streamer(keys, keywords, tweets_amount, discard, twarc_method, languages, result_type, follow, geo)
    streamer.stream()
    return streamer.result
