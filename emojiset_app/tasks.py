from stream_tweets import Tweet_Streamer

def stream_task(keywords, tweets_amount, discard, twarc_method, languages, result_type):
    streamer = Tweet_Streamer(keywords, tweets_amount, discard, twarc_method, languages, result_type)
    streamer.stream()
    return streamer.result
