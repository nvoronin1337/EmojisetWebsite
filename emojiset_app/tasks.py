from stream_tweets import Tweet_Streamer
from emojiset_app.utils import debug

# --- uses TweetStreamer and returns result (dictionaty ==> index:(tweet_text, emojiset))
def stream_task(keys, keywords, discard, twarc_method, languages, result_type, follow, geo, tweet_amount=None, finish_time=None, file_size=10, email=""):
    streamer = Tweet_Streamer(keys, keywords, discard, twarc_method, languages, result_type, follow, geo, tweet_amount, finish_time, file_size, email)
    streamer.stream()
    # only passing email for large tasks
    if(streamer.email):
        streamer.result_to_csv(clean=False)
    return streamer.result
