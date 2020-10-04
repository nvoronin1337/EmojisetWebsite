from stream_tweets import Tweet_Streamer

def stream_task(keywords, tweets_amount):
    streamer = Tweet_Streamer(keywords, tweets_amount)
    streamer.stream()
    return streamer.result