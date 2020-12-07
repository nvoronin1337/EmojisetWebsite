from twarc import Twarc
import traceback
import time
from time import gmtime, strftime
import emoji
from emojiset_app import EMOJI_SET, small_task_q, long_task_q
import regex
from rq import get_current_job  
from collections import Counter
from itertools import combinations
import requests
import sys
import os
import shutil
import io
import re
import json
import csv
import emoji
from emojiset_app.utils import debug

# Helper functions for saving json, csv and formatted txt files
def save_json(variable, filename):
  with io.open(filename, "a+", encoding="utf-8") as f:
    f.write(str(json.dumps(variable, indent=4, ensure_ascii=False)))

def save_csv(data, filename):
  with io.open(filename, "a+", encoding="utf-8") as handle:
    handle.write(u"Source,Target,Weight\n")
    for source, targets in sorted(data.items()):
      for target, count in sorted(targets.items()):
        if source != target and source != None and target != None:
          handle.write(source + u"," + target + u"," + str(count) + u"\n")

def save_text(data, filename):
  with io.open(filename, "a+", encoding="utf-8") as handle:
    for item, count in data.most_common():
      handle.write(str(count) + "\t" + item + "\n")

# Returns the screen_name of the user retweeted, or None
def retweeted_user(status):
  if "retweeted_status" in status:
    orig_tweet = status["retweeted_status"]
    if "user" in orig_tweet and orig_tweet["user"] != None:
      user = orig_tweet["user"]
      if "screen_name" in user and user["screen_name"] != None:
        return user["screen_name"]

# Returns a list of screen_names that the user interacted with in this Tweet
def get_interactions(status):
  interactions = []
  if "in_reply_to_screen_name" in status:
    replied_to = status["in_reply_to_screen_name"]
    if replied_to != None and replied_to not in interactions:
      interactions.append(replied_to)
  if "retweeted_status" in status:
    orig_tweet = status["retweeted_status"]
    if "user" in orig_tweet and orig_tweet["user"] != None:
      user = orig_tweet["user"]
      if "screen_name" in user and user["screen_name"] != None:
        if user["screen_name"] not in interactions:
          interactions.append(user["screen_name"])
  if "quoted_status" in status:
    orig_tweet = status["quoted_status"]
    if "user" in orig_tweet and orig_tweet["user"] != None:
      user = orig_tweet["user"]
      if "screen_name" in user and user["screen_name"] != None:
        if user["screen_name"] not in interactions:
          interactions.append(user["screen_name"])
  if "entities" in status:
    entities = status["entities"]
    if "user_mentions" in entities:
      for item in entities["user_mentions"]:
        if item != None and "screen_name" in item:
          mention = item['screen_name']
          if mention != None and mention not in interactions:
            interactions.append(mention)
  return interactions

# Returns a list of hashtags found in the tweet
def get_hashtags(status):
  hashtags = []
  if "entities" in status:
    entities = status["entities"]
    if "hashtags" in entities:
      for item in entities["hashtags"]:
        if item != None and "text" in item:
          hashtag = item['text']
          if hashtag != None and hashtag not in hashtags:
            hashtags.append(hashtag)
  return hashtags

# Returns a list of URLs found in the Tweet
def get_urls(status):
  urls = []
  if "entities" in status:
    entities = status["entities"]
    if "urls" in entities:
        for item in entities["urls"]:
          if item != None and "expanded_url" in item:
            url = item['expanded_url']
            if url != None and url not in urls:
              urls.append(url)
  return urls

# Returns the URLs to any images found in the Tweet
def get_image_urls(status):
  urls = []
  if "entities" in status:
    entities = status["entities"]
    if "media" in entities:
      for item in entities["media"]:
        if item != None:
          if "media_url" in item:
            murl = item["media_url"]
            if murl not in urls:
              urls.append(murl)
  return urls


## Tweet Streamer class
#  Uses Twarc API to stream tweets from twitter
class Large_Streamer():
	def __init__(self, keys, keywords, discard, twarc_method, lang, result_type, follow, geo, max_tweets=None, finish_time=None, email="", extract_primary=[], extract_secondary=[], offset=0, file_name="extracted_data.csv"):
		# ---Configuring Twarc API---*
		self.consumer_key = keys['consumer_key']
		self.consumer_secret = keys['consumer_secret']
		self.access_token = keys['access_token']
		self.access_token_secret = keys['access_token_secret']
		if twarc_method == 'search':
			app_auth = True
		else:
			app_auth = False
		self.twarc = Twarc(self.consumer_key, self.consumer_secret, self.access_token, self.access_token_secret, http_errors=3, app_auth=app_auth)
		# ---Save paramaeters passed to the constructor
		self.keywords = keywords
		self.max_tweets = max_tweets
		self.discard = discard
		self.twarc_method = twarc_method
		self.lang = lang
		self.result_type = result_type
		self.follow = follow
		if self.follow:
			self.follow = self.follow.replace('@', '').replace(' ', "").split(',')
		self.geo = geo
		self.finish_time = finish_time
		if self.finish_time:
			self.total_time = self.finish_time - time.time()
		self.user_ids = []
		self.job = get_current_job()
		self.current_tweets = 0
		self.discarded = 0
		self.text = "text"
		if email:
			self.email = email.split('@')[0]
		else:
			self.email = email
		# ---dictionaty in the format {index: (tweet, emojiset)}---*
		self.result = {}
		now = time.localtime()
		self.started_at = strftime("%a, %d %b %Y %X", gmtime())
		self.current_datetime = time.strftime("%Y-%m-%d_%H:%M:%S", now)

		self.extract_primary = extract_primary
		self.extract_secondary = extract_secondary
		
		self.influencer_frequency_dist = Counter()
		self.mentioned_frequency_dist = Counter()
		self.hashtag_frequency_dist = Counter()
		self.url_frequency_dist = Counter()
		self.user_user_graph = {}
		self.user_hashtag_graph = {}
		self.hashtag_hashtag_graph = {}
		self.all_image_urls = []
		self.tweets = {}
		
		self.tweet_id = ""
		self.tweet_username = ""
		self.tweets_text = ""
		self.emojisets = ""
		self.tweet_status_urls = ""
		self.hashtags = ""
		self.urls = ""
		self.image_urls = ""
		self.timestamp = ""
		self.tweet_count = 0

		self.temporary_rows = []
		self.file_name = file_name

		self.save_dir = 'results/' + self.email + '/' + self.current_datetime
		if not os.path.exists(self.save_dir):
			os.makedirs(self.save_dir)


	def stream(self):
		# ---stream tweets---*
		finished = False
		allowed_reconnections = 10
		current_reconnections = 0
		if 'true' in self.extract_primary or 'true' in self.extract_secondary:
			while(not finished):
				try:
					self.get_tweet_stream()
				# ---error handling---*
				except KeyboardInterrupt:
					print("Keyboard interrupt...")
					return
				except Exception:
					print("Error...")
				
				current_reconnections += 1
				if current_reconnections == allowed_reconnections:
					finished = True
				else:
					if self.requested_limit_reached() or self.twarc_method != 'filter':
						finished = True


	def get_tweet_stream(self):
		# ---search function---*
		if self.twarc_method == "search":
			self.text = "full_text"
			# ---process function in regards to other user-options---*
			for tweet in self.twarc.search(self.keywords, lang=self.lang, result_type=self.result_type):
				self.job.refresh()
				if self.job.meta['cancel_flag']:
					break
				else:
					self.process_tweet(tweet)
					if self.requested_limit_reached():
						break
		# ---filter function---*
		elif self.twarc_method == "filter":
			if self.follow:
				# ---finds user based on their user ID (must be found through user_lookup, and is the only way to track specific users)---*
				for user in self.twarc.user_lookup(ids=self.follow, id_type="screen_name"):
					self.user_ids.append(user['id_str']) 
			# ---if either keywords are fine, or the location is provided, or the username is provided, then we can use filter to find some meaningful data---*
			for tweet in self.twarc.filter(track=self.keywords, lang=self.lang, follow=",".join(self.user_ids), locations=self.geo):
				self.job.refresh()
				if self.job.meta['cancel_flag']:
					break
				else:
					self.process_tweet(tweet)
					if self.requested_limit_reached():
						break
		# ---sample function---*    
		elif self.twarc_method == "sample":
			self.text = "text"
			for tweet in self.twarc.sample():
				self.job.refresh()
				if self.job.meta['cancel_flag']:
					break
				else:
					if self.text in tweet:
						self.process_tweet(tweet)
						if self.requested_limit_reached():
							break


	# ---extract emojiset, update progress bar, discard tweets without emojis, output # of discarded tweets---*
	def process_tweet(self, tweet):
		if self.discard:                                                                       
			if self.contains_emoji(tweet):
				self.parse_tweet(tweet)
				self.current_tweets += 1                                                       # counter of tweets w/ emojis to update progress bar*
				if self.current_tweets % 100 == 0:	
					self.job.refresh()     
					if self.max_tweets:                                                        # refreshes progress bar every 150 milliseconds (established in main.js)*
						self.job.meta['progress'] = round((self.current_tweets / self.max_tweets) * 100,2)     # updates progress bar (tweets with emojis / # of specified tweets) as a percentage*
					elif self.finish_time:
						self.job.meta['progress'] = 100 - round(((self.finish_time - time.time()) / self.total_time) * 100,2)
					self.job.save_meta()                                                           # saves new update to progress bar*
			else:
				self.discarded += 1     
				if self.current_tweets % 100 == 0:                                                       # counter of tweets w/o emojis*
					self.job.refresh()                                                             # refreshes # of discarded tweets every 150 milliseconds (established in main.js)*
					self.job.meta['discarded_tweets'] = self.discarded                             
					self.job.save_meta()                                                           # saves new update to # of discarded tweets message*
		else:   
			self.parse_tweet(tweet)
			self.current_tweets += 1
			if self.current_tweets % 100 == 0:
				self.job.refresh()
				if self.max_tweets:                                                       
					self.job.meta['progress'] = round((self.current_tweets / self.max_tweets) * 100,2)   
				elif self.finish_time:
					self.job.meta['progress'] = 100 - round(((self.finish_time - time.time()) / self.total_time) * 100,2)
				self.job.save_meta()


	# ---checks to see if any emojis are present---*
	def contains_emoji(self, tweet):
		if self.text in tweet:
			grapheme_clusters = regex.findall(r"\X", tweet[self.text])
			for cluster in grapheme_clusters:
				if cluster in EMOJI_SET:
					return True
		return False


	def parse_tweet(self, status):	
		self.tweet_count += 1

		self.tweets[self.tweet_count] = status

		if self.extract_primary[0] == 'true':
			if "created_at" in status:
				self.timestamp = status['created_at']
			else:
				self.timestamp = ""

		screen_name = ""
		if self.extract_primary[3] == 'true':
			if "user" in status:
				if "screen_name" in status["user"]:
					screen_name = status["user"]["screen_name"]
			self.tweet_username = screen_name

	# Tweet text can be in either "text" or "full_text" field...
		text = ""
		text_param_name = None
		if "full_text" in status:
			text_param_name = "full_text"
		elif "text" in status:
			text_param_name = "text"
			
		if screen_name and 'retweeted_status' in status:
			# ---if tweet is a retweet---*
			if 'extended_tweet' in status['retweeted_status']:
				# ---if tweet was found using filter API---*
				text = "RT " + screen_name + ': ' + status['retweeted_status']['extended_tweet']['full_text']
			else:
				# ---if tweet was found using search API---*
				text = "RT " + screen_name + ': ' + status['retweeted_status'][text_param_name]
		else:
			# ---if not a retweet---*
			if 'extended_tweet' in status:
				# ---if not retweet but still truncated---*
				text = status['extended_tweet']['full_text']
			else:
				# ---if not a retweet and not tuncated---*
				if text_param_name in status:
					text = status[text_param_name]
				else:
					text = ""

		id_str = ""
		if self.extract_primary[2] == 'true':
			if "id_str" in status:
				id_str = status["id_str"]
			self.tweet_id = id_str

	# Assemble the URL to the tweet we received...
		tweet_url = None
		if self.extract_primary[1] == 'true':
			if id_str != None and screen_name != None:
				tweet_url = "https://twitter.com/" + screen_name + "/status/" + id_str

	# ...and capture it
		if tweet_url != None:
				self.tweet_status_urls = tweet_url

		if text != None:
			self.tweets_text = text
			if self.extract_primary[5] == 'true':
				self.emojisets = self.extract_emoji_sequences(text)

	# Record mapping graph between users
		if self.extract_secondary[4] == 'true' or self.extract_secondary[5] == 'true':
			interactions = get_interactions(status)
			if interactions != None:
				for user in interactions:
					self.mentioned_frequency_dist[user] += 1
					if screen_name not in self.user_user_graph:
						self.user_user_graph[screen_name] = {}
					if user not in self.user_user_graph[screen_name]:
						self.user_user_graph[screen_name][user] = 1
					else:
						self.user_user_graph[screen_name][user] += 1

	# Record mapping graph between users and hashtags
		if self.extract_primary[5] == 'true':
			hashtags = get_hashtags(status)
			if hashtags != None:
				self.hashtags = ','.join(hashtags)
				if self.extract_secondary[2] == 'true' or self.extract_secondary[3] == 'true':
					if len(hashtags) > 1:
						hashtag_interactions = []
			# This code creates pairs of hashtags in situations where multiple
			# hashtags were found in a tweet
			# This is used to create a graph of hashtag-hashtag interactions
						for comb in combinations(sorted(hashtags), 2):
							hashtag_interactions.append(comb)
						if len(hashtag_interactions) > 0:
							for inter in hashtag_interactions:
								item1, item2 = inter
							if item1 not in self.hashtag_hashtag_graph:
								self.hashtag_hashtag_graph[item1] = {}
							if item2 not in self.hashtag_hashtag_graph[item1]:
								self.hashtag_hashtag_graph[item1][item2] = 1
							else:
								self.hashtag_hashtag_graph[item1][item2] += 1
						for hashtag in hashtags:
							self.hashtag_frequency_dist[hashtag] += 1
							if screen_name not in self.user_hashtag_graph:
								self.user_hashtag_graph[screen_name] = {}
							if hashtag not in self.user_hashtag_graph[screen_name]:
								self.user_hashtag_graph[screen_name][hashtag] = 1
							else:
								self.user_hashtag_graph[screen_name][hashtag] += 1
			else:
				self.hashtags = ""

		if self.extract_primary[7] == 'true':
			urls = get_urls(status)
			if urls != None:
				self.urls = ','.join(urls)
			else:
				self.urls = ""

		if self.extract_primary[8] == 'true':
			image_urls = get_image_urls(status)
			if image_urls != None:
				self.image_urls = ','.join(image_urls)
				if self.extract_secondary[1] == 'true':
					for url in image_urls:
						if url not in self.all_image_urls:
							self.all_image_urls.append(url)
			else:
				self.image_urls = ""

	# Iterate through image URLs, fetching each image if we haven't already
		if self.extract_secondary[1] == 'true':
			pictures_dir = os.path.join(self.save_dir, "images")
			if not os.path.exists(pictures_dir):
				os.makedirs(pictures_dir)
			for url in self.all_image_urls:
				m = re.search("^http:\/\/pbs\.twimg\.com\/media\/(.+)$", url)
				if m != None:
					filename = m.group(1)
					save_path = os.path.join(pictures_dir, filename)
					if not os.path.exists(save_path):
						response = requests.get(url, stream=True)
						with open(save_path, 'wb') as out_file:
							shutil.copyfileobj(response.raw, out_file)
						del response

	# Output a bunch of files containing the data we just gathered
		
		if self.tweet_count % 100 == 0:
			outputs = self.construct_secondary_outputs()
			json_outputs = outputs[0]
			for name, dataset in json_outputs.items():
				filename = os.path.join(self.save_dir, name)
				save_json(dataset, filename)
				self.tweets = {}

		# These files are created in a format that can be easily imported into Gephi
			csv_outputs = outputs[1]

			for name, dataset in csv_outputs.items():
				filename = os.path.join(self.save_dir, name)
				save_csv(dataset, filename)

			text_outputs = outputs[2]
			for name, dataset in text_outputs.items():
				filename = os.path.join(self.save_dir, name)
				save_text(dataset, filename)
		self.flush_results()
		

	# ---function returns emojiset list consisting of emoji sequences (a string) ; sequences are separated by any character that isn't an emoji---*
	def extract_emoji_sequences(self, text):
		emoji_sequence = []
		emojiset_str = ""
		grapheme_clusters = regex.findall(r"\X", text)         # extracts all of the grapheme clusters from text
		for cluster in grapheme_clusters:                      
			if cluster in EMOJI_SET:                           # if cluster is emoji -> append it to the emoji sequence
				emoji_sequence.append(cluster)
			else:                                              # if cluster is not an emoji, append sequence to emoji set and clear the sequence
				if(len(emoji_sequence) > 0):                   
					emojiset_str += "".join(emoji_sequence)
					emojiset_str += ","                                                             
					emoji_sequence = []
		if(len(emoji_sequence) > 0):                           # append the last emoji sequence to emoji set string
			emojiset_str += "".join(emoji_sequence)
			emojiset_str += ","
		if len(emojiset_str) > 1:                              # removes comma from end of string
			emojiset_str = emojiset_str[:-1]
		return emojiset_str                                    # returns emojiset as a string


	def requested_limit_reached(self):
		if self.max_tweets:
			if self.current_tweets >= self.max_tweets:
				return True
			else:
				return False
		elif self.finish_time:
			if time.time() >= self.finish_time:
				return True
			else:
				return False


	def result_to_csv(self, filename, colnames, data):
		csv_columns = []
		for colname in colnames:
			csv_columns.append(colname)
		
		with open(filename, 'a+') as f:
			writer = csv.DictWriter(f, fieldnames=csv_columns, lineterminator='\n')
			if self.tweet_count == 1:
				writer.writeheader()

			for row in data:
				csv_row = {}
				col_index = 0
				all_empty = True
				for value in row:
					if value:
						csv_row[colnames[col_index]] = value
						all_empty = False
					col_index += 1
				if not all_empty:
					writer.writerow(csv_row)


	def flush_results(self, ignore_amount=False):
		col_names = []
		values = []
		if self.extract_primary[0] == 'true':
			col_names.append('created at')
			values.append(self.timestamp)
		if self.extract_primary[1] == 'true':
			col_names.append('source')
			values.append(self.tweet_status_urls)
		if self.extract_primary[2] == 'true':
			col_names.append('tweet_id')
			values.append(self.tweet_id)
		if self.extract_primary[3] == 'true':
			col_names.append('username')
			values.append(self.tweet_username)
		if self.extract_primary[4] == 'true':
			col_names.append('text')
			values.append(self.tweets_text)
		if self.extract_primary[5] == 'true':
			col_names.append('emojiset')
			values.append(self.emojisets)
		if self.extract_primary[6] == 'true':
			col_names.append('hashtags')
			values.append(self.hashtags)
		if self.extract_primary[7] == 'true':
			col_names.append('urls')
			values.append(self.urls)
		if self.extract_primary[8] == 'true':
			col_names.append('image_urls')
			values.append(self.image_urls)

		self.temporary_rows.append(values)

		if len(col_names) > 0 and (len(self.temporary_rows) >= 100 or ignore_amount):
			filename = os.path.join(self.save_dir, self.file_name)
			self.result_to_csv(filename, col_names, self.temporary_rows)
			self.temporary_rows = []


	def construct_secondary_outputs(self):
		csv_outputs = {}
		json_outputs = {}
		txt_outputs = {}
		
		if self.extract_secondary[0] == 'true':
			json_outputs['full_tweets.json'] = self.tweets
		if self.extract_secondary[2] == 'true':
			csv_outputs["hashtag_hashtag_graph.csv"] = self.hashtag_hashtag_graph 
			json_outputs['hashtag_hashtag_graph.json'] = self.hashtag_hashtag_graph
		if self.extract_secondary[3] == 'true':
			csv_outputs["user_hashtag_graph.json"] = self.user_hashtag_graph
			json_outputs["user_hashtag_graph.json"] = self.user_hashtag_graph
		if self.extract_secondary[4] == 'true':
			json_outputs["mentioned.json"] = self.mentioned_frequency_dist
			txt_outputs['mentioned.txt'] = self.mentioned_frequency_dist
		if self.extract_secondary[5] == 'true':
			csv_outputs["user_user_graph.csv"] = self.user_user_graph
			json_outputs["user_user_graph.json"] = self.user_user_graph
		
		return [json_outputs, csv_outputs, txt_outputs]
