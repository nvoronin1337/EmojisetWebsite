from stream_tweets import Tweet_Streamer

def stream_task(keywords, tweets_amount, discard, twarc_method, languages):
    streamer = Tweet_Streamer(keywords, tweets_amount, discard, twarc_method, languages)
    streamer.stream()
    return streamer.result
