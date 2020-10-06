from flask import Flask
import redis
from rq import Queue, Worker
from flask_bootstrap import Bootstrap
import emoji


app = Flask(__name__)
bootstrap = Bootstrap(app)

r = redis.Redis()

q = Queue(connection=r, default_timeout=600)
'''
worker = Worker([q], connection=r, name='main_worker')
worker.work()
'''

EMOJI_SET = set()

# populate EMOJI_DICT
def pop_emoji_dict():
    for emoji_char in emoji.UNICODE_EMOJI:
        EMOJI_SET.add(emoji_char)

pop_emoji_dict()

from emojiset_app import views
from emojiset_app import tasks

if __name__ == "__main__":
	app.run()
