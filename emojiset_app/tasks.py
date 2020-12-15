from stream_tweets import Tweet_Streamer
from stream_large import Large_Streamer
from emojiset_app.utils import send_message
from time import gmtime, strftime
import os

# --- uses TweetStreamer and returns result (dictionaty ==> index:(tweet_text, emojiset))
def stream_task(keys, keywords, discard, twarc_method, languages, result_type, follow, geo, tweet_amount=None):
    streamer = Tweet_Streamer(keys, keywords, discard, twarc_method, languages, result_type, follow, geo, tweet_amount)
    streamer.stream()
    return streamer.result


def stream_large(keys, keywords, discard, twarc_method, languages, result_type, follow, geo, tweet_amount=None, finish_time=None, email="", extract_primary=[], extract_secondary=[], offset=0, file_name="extracted_data.csv"):
    streamer = Large_Streamer(keys, keywords, discard, twarc_method, languages, result_type, follow, geo, tweet_amount, finish_time, email, extract_primary, extract_secondary, file_name)
    streamer.stream()
    streamer.flush_results(ignore_amount=True)
    filename =  os.path.join(streamer.save_dir, 'task_info.txt')

    with open(filename, 'w', encoding="utf-8") as f:
        query = "Query: " + streamer.keywords
        started_at = 'Started at: ' + streamer.started_at
        finished_at = 'Finished at: ' + strftime("%a, %d %b %Y %X", gmtime()) 
        collected = 'Collected tweets: ' + str(streamer.tweet_count)
        discarded = 'Discarded tweets: ' + str(streamer.discarded)
        print(query, file=f)
        print(started_at, file=f)
        print(finished_at, file=f)
        print(collected, file=f)
        print(discarded, file=f)
    send_message(email)
