from stream_tweets import Tweet_Streamer

def stream_task(keywords, tweets_amount, discard, twarc_method, languages, result_type, follow, geo):
    streamer = Tweet_Streamer(keywords, tweets_amount, discard, twarc_method, languages, result_type, follow, geo)
    streamer.stream()
    return streamer.result
