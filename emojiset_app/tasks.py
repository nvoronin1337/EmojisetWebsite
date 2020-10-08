from stream_tweets import Tweet_Streamer

def stream_task(keywords, tweets_amount, discard):
    streamer = Tweet_Streamer(keywords, tweets_amount, discard)
    streamer.stream()
    return streamer.result
