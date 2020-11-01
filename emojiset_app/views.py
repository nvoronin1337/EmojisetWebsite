from emojiset_app import app
from emojiset_app import r
from emojiset_app import small_task_q
from emojiset_app import db
from emojiset_app.tasks import stream_task
from emojiset_app.utils import *
from emojiset_app.models import SavedQuery
from flask import render_template, request, redirect, url_for, jsonify, render_template_string
from flask_user import login_required, roles_required, current_user
from time import strftime


# The Home page is accessible to anyone
@app.route('/')
def home_page():
	return render_template("index.html", register=url_for('user.register'), login=url_for('user.login'), profile=url_for('user.edit_user_profile'), home=url_for('home_page'), emojiset=url_for('emojiset_mining'), emojiset_large=url_for('emojiset_mining_large'),logout=url_for('user.logout'))


# --- this function is called when user opens website/emojiset-mining url ---*
# --- displays the html page located in /templates forder
@app.route("/emojiset", methods=['GET'])
@login_required
def emojiset_mining():
	return render_template("emojiset_mining_small.html")


@app.route("/emojiset_big_dataset", methods=['GET'])
@login_required
def emojiset_mining_large():
	return render_template("large_set.html")


# --- this URL can't be directly accessed by user ---*
# --- this URL is being called using AJAX call when the submit button is clicked ---*
# --- request.form data is being passed to this URL in the AJAX call (request.form contains data that users has entered in the form) ---*
# --- this function reads all the values and parses them to ensure they are valid ---*
# --- after all of the data is read and parsed, creates a new job object which takes the function name, and parameters (check tasks.py) ---*
# --- returns empty json with one header (Location: website/status/<job_key>) which is later used to check the jobs status by its id (job_key) ---*
@app.route('/emojiset/_run_small_task', methods=['POST'])
@login_required
def run_small_task():
	twitter_keys = {
		'access_token': current_user.access_token,
		'access_token_secret': current_user.access_token_secret,
		'consumer_key': current_user.consumer_key,
		'consumer_secret': current_user.consumer_secret
	}

	# read values that are always present
	keywords = ""
	if 'keywords' in request.form:
		twarc_method = 'search'
		keywords = request.form["keywords"] 
		tweet_amount = request.form["tweet_amount"]
		discard_checked = "discard_box" in request.form
	elif 'keywords_filter' in request.form:
		twarc_method = 'filter'
		keywords = request.form["keywords_filter"]
		tweet_amount = request.form["tweet_amount_filter"]
		discard_checked = "discard_box_filter" in request.form
	else:
		twarc_method = 'sample'
		tweet_amount = request.form["tweet_amount_sample"]
		discard_checked = "discard_box_sample" in request.form
	
	form_data = validate_and_parse_form(request.form, twarc_method)

	discard = False
	if discard_checked:
		discard = True
	if not tweet_amount:
		tweet_amount = 100
	else:
		tweet_amount = int(tweet_amount)

# ---to use additional settings properly we need to make sure that the query is constructed correctly---*
	if twarc_method == 'search':
		if form_data:
			keywords = construct_search_query(keywords, form_data['additional_settings'], form_data['operator'])
		else:
			keywords = split_search_keywords(keywords)
	if twarc_method == 'filter':
		if form_data:
			keywords = construct_filter_query(keywords, form_data['additional_settings'])
			keywords = split_filter_keywords(keywords)
		else:
			keywords = split_filter_keywords(keywords)


	# ---send a job to the task queue---*
	job = None
	if form_data:
		job = small_task_q.enqueue(stream_task, twitter_keys, keywords, tweet_amount, discard, twarc_method, form_data['languages'], form_data['result_type'], form_data['follow'], form_data['location'])
		json_query = query_to_json(keywords, discard, twarc_method, form_data)
	else:
		job = small_task_q.enqueue(stream_task, twitter_keys, keywords, tweet_amount, discard, twarc_method, None, None, None, None)
		json_query = query_to_json(keywords, discard, twarc_method)
	
	
	job.meta['progress'] = 0
	job.meta['discarded_tweets'] = 0
	job.meta['query'] = json_query
	job.meta['cancel_flag'] = 0

	job.save_meta()
	
	return jsonify({}), 202, {'Status': url_for('job_status', job_key=job.id), 'Cancel': url_for('job_cancel', job_key=job.id)}
	


# ---get job object from the queue by the id and check its status (finished or not)---*
@app.route("/emojiset/status/<job_key>", methods=['GET'])
@login_required
def job_status(job_key):
	job = small_task_q.fetch_job(job_key)
	if job is None:
		response = {'status': 'unknown'}
	else:
		job.refresh()
		response = {
			'status': job.get_status(),
			'progress': job.meta['progress'],
			'discarded_tweets': job.meta['discarded_tweets'],
			'result': job.result,
			'query': job.meta['query'],
			'cancel_flag': job.meta['cancel_flag']
		}
		if job.is_failed:
			response['message'] = job.exc_info.strip().split('\n')[-1]
	return jsonify(response)


# ---get job object from the queue by the id and cancel it
@app.route("/emojiset/cancel/<job_key>", methods=['GET'])
@login_required
def job_cancel(job_key):
	job = small_task_q.fetch_job(job_key)
	if job is None:
		response = {'status': 'unknown'}
	else:
		job.refresh()
		job.meta['cancel_flag'] = 1
		job.save_meta()
		response = {
			'status': 'canceled',
			'progress': job.meta['progress'],
			'discarded_tweets': job.meta['discarded_tweets'],
			'result': job.result,
			'query': job.meta['query']
		}
		if job.is_failed:
			response['message'] = job.exc_info.strip().split('\n')[-1]
	return jsonify(response)


@app.route("/emojiset/save_query", methods=["POST"])
@login_required
def save_query():
	query = request.form['query']
	user_id = current_user.id
	saved_query = SavedQuery(
		query = query,
		user_id=user_id
	)
	db.session.add(saved_query)
	db.session.commit()
	return jsonify({}, 202)
