from flask import Flask
import redis
from rq import Queue
from flask_bootstrap import Bootstrap


app = Flask(__name__)
bootstrap = Bootstrap(app)

r = redis.Redis()

q = Queue(connection=r, default_timeout=360)

from emojiset_app import views
from emojiset_app import tasks
