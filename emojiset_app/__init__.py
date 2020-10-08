# coding=UTF-8
from flask import Flask
import redis
from rq import Queue, Worker
from flask_bootstrap import Bootstrap
import emoji
import rq_dashboard


app = Flask(__name__)
app.config.from_object(rq_dashboard.default_settings)
app.register_blueprint(rq_dashboard.blueprint, url_prefix="/rq")
bootstrap = Bootstrap(app)


r = redis.Redis()
q = Queue(connection=r, default_timeout=600)
EMOJI_SET = set()

# populate EMOJI_DICT
def pop_emoji_dict():
    for emoji_char in emoji.UNICODE_EMOJI:
        EMOJI_SET.add(emoji_char)


pop_emoji_dict()


from emojiset_app import views
from emojiset_app import tasks
