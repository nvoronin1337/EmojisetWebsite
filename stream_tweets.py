from twarc import Twarc
import traceback
import time
import emoji
from emojiset_app import EMOJI_SET, small_task_q, long_task_q
import regex
from rq import get_current_job  
from emojiset_app.utils import split_filter_keywords, split_search_keywords
import os
import csv


## Tweet Streamer class
#  Uses Twarc API to stream tweets from twitter
class Tweet_Streamer():
	def __init__(self, keys, keywords, discard, twarc_method, lang, result_type, follow, geo, max_tweets=None):
		# ---Configuring Twarc API---*
		self.consumer_key = keys['consumer_key']
		self.consumer_secret = keys['consumer_secret']
		self.access_token = keys['access_token']
		self.access_token_secret = keys['access_token_secret']
		if twarc_method == 'search':
			app_auth = True
		else:
			app_auth = False
		self.twarc = Twarc(self.consumer_key, self.consumer_secret, self.access_token, self.access_token_secret, http_errors=1, app_auth=app_auth)
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
		self.user_ids = []
		self.job = get_current_job()
		self.current_tweets = 0
		self.discarded = 0
		self.text = "text"
		# ---dictionaty in the format {index: (tweet, emojiset)}---*
		self.result = {}
		now = time.localtime()
		self.current_datetime = time.strftime("%Y-%m-%d_%H:%M:%S", now)


	def stream(self):
		 # ---stream tweets---*
		try:
			self.get_tweet_stream()
		# ---error handling---*
		except KeyboardInterrupt:
			print("Keyboard interrupt...")
			return
		except Exception:
			print("Error. Quitting...")
			traceback.print_exc()
			return


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
				self.map_tweet_to_emojiset(tweet)
				self.current_tweets += 1                                                       # counter of tweets w/ emojis to update progress bar*
				self.job.refresh()     
				if self.max_tweets:                                                        # refreshes progress bar every 150 milliseconds (established in main.js)*
					self.job.meta['progress'] = round((self.current_tweets / self.max_tweets) * 100,2)     # updates progress bar (tweets with emojis / # of specified tweets) as a percentage*
				self.job.save_meta()                                                           # saves new update to progress bar*
			else:
				self.discarded += 1                                                            # counter of tweets w/o emojis*
				self.job.refresh()                                                             # refreshes # of discarded tweets every 150 milliseconds (established in main.js)*
				self.job.meta['discarded_tweets'] = self.discarded                             
				self.job.save_meta()                                                           # saves new update to # of discarded tweets message*
		else:   
			self.map_tweet_to_emojiset(tweet)
			self.current_tweets += 1
			self.job.refresh()
			if self.max_tweets:                                                       
				self.job.meta['progress'] = round((self.current_tweets / self.max_tweets) * 100,2)   
			self.job.save_meta()


	# ---checks to see if any emojis are present---*
	def contains_emoji(self, tweet):
		if self.text in tweet:
			grapheme_clusters = regex.findall(r"\X", tweet[self.text])
			for cluster in grapheme_clusters:
				if cluster in EMOJI_SET:
					return True
		return False


	# ---Extracts full tweet text, extracts emojiset from that text, saves it to the result dictionary---*
	def map_tweet_to_emojiset(self, tweet):
		if self.text in tweet:
			tweet_text = ""
			emojiset = ""
			
			if 'retweeted_status' in tweet:
				# ---if tweet is a retweet---*
				if 'extended_tweet' in tweet['retweeted_status']:
					# ---if tweet was found using filter API---*
					tweet_text = "RT " + tweet['user']['screen_name'] + ': ' + tweet['retweeted_status']['extended_tweet']['full_text']
					emojiset = self.extract_emoji_sequences(tweet['retweeted_status']['extended_tweet']['full_text'])
					self.result[self.current_tweets] = (tweet_text, emojiset)
				else:
					# ---if tweet was found using search API---*
					tweet_text = "RT " + tweet['user']['screen_name'] + ': ' + tweet['retweeted_status'][self.text]
					emojiset = self.extract_emoji_sequences(tweet['retweeted_status'][self.text])
					self.result[self.current_tweets] = (tweet_text, emojiset)
			else:
				# ---if not a retweet---*
				if 'extended_tweet' in tweet:
					# ---if not retweet but still truncated---*
					tweet_text = tweet['extended_tweet']['full_text']
					emojiset = self.extract_emoji_sequences(tweet['extended_tweet']['full_text'])
					self.result[self.current_tweets] = (tweet_text, emojiset)
				else:
					# ---if not a retweet and not tuncated---*
					tweet_text = tweet[self.text]
					emojiset = self.extract_emoji_sequences(tweet[self.text])
					self.result[self.current_tweets] = (tweet_text, emojiset)
				

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

	# ---function returns emojiset list consisting of emoji sequences (a string looking like python list of lists)---*
	def extract_emoji_sequences_with_brackets(self, text):
		emoji_sequence = []
		emojiset_str = '['
		grapheme_clusters = regex.findall(r"\X", text)
		for cluster in grapheme_clusters:
			if cluster in EMOJI_SET:
				emoji_sequence.append(cluster)
			else:
				if(len(emoji_sequence) > 0):
					emojiset_str += "[" + ",".join(emoji_sequence) + "], "
					emoji_sequence = []
		if(len(emoji_sequence) > 0):
			emojiset_str += "[" + ", ".join(emoji_sequence) + "]"
		else:
			if(len(emojiset_str) > 1):
				emojiset_str = emojiset_str[:-2]
		emojiset_str += ']'
		return emojiset_str
    