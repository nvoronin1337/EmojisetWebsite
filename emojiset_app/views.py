from emojiset_app import app
from emojiset_app import r
from emojiset_app import small_task_q, long_task_q
from emojiset_app import db
from emojiset_app.tasks import stream_task, stream_large
from emojiset_app.utils import *
from emojiset_app.models import SavedQuery, RunningTask, SavedResultDirectory, FinishedTask
from flask import render_template, request, redirect, url_for, jsonify, send_from_directory
from flask_user import login_required, roles_required, current_user
from time import strftime
from json import loads
import time
import calendar
import os
import emoji



# The Home page is accessible to anyone
@app.route('/')
def home_page():
	return render_template("home.html", register=url_for('user.register'), login=url_for('user.login'), profile=url_for('user.edit_user_profile'), home=url_for('home_page'), emojiset=url_for('emojiset_mining'), emojiset_large=url_for('emojiset_mining_large'),logout=url_for('user.logout'))


# --- this function is called when user opens website/emojiset-mining url ---*
# --- displays the html page located in /templates forder
@app.route("/emojiset", methods=['GET'])
@login_required
def emojiset_mining():
	return render_template("emojiset_mining_small.html")


@app.route("/docs", methods=['GET'])
@login_required
def documentation():
	return render_template("document.html")


@app.route("/emojiset_big_dataset", methods=['GET'])
@login_required
def emojiset_mining_large():
	return render_template("large_set.html")


@app.route("/epidemiology")
def epidemiology():
	return render_template("epidemiology.html")


@app.route("/epidemiology/mmr", methods=['POST'])
def mmr():
	from emojiset_app.epidemiology.TestMajority import MMR
	bias = float(request.form.get("bias"))
	adopter = float(request.form.get("adopter"))
	rejector = float(request.form.get("rejector"))
	q = int(request.form.get("q_group"))
	plot_html = MMR(bias, adopter, rejector, q)

	response = {
		"plot_html": plot_html
	}
	return jsonify(response), 200


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
			keywords = split_filter_keywords(keywords)
		else:
			keywords = split_filter_keywords(keywords)

	# ---send a job to the task queue---*
	job = None
	if form_data:
		job = small_task_q.enqueue(stream_task, twitter_keys, keywords, discard, twarc_method, form_data['languages'], form_data['result_type'], form_data['follow'], form_data['location'], tweet_amount=tweet_amount)
		json_query = query_to_json(keywords, discard, twarc_method, form_data)
	else:
		job = small_task_q.enqueue(stream_task, twitter_keys, keywords, discard, twarc_method, None, None, None, None, tweet_amount=tweet_amount)
		json_query = query_to_json(keywords, discard, twarc_method)
	
	job.meta['progress'] = 0
	job.meta['discarded_tweets'] = 0
	job.meta['query'] = json_query
	job.meta['cancel_flag'] = 0
	job.save_meta()
	return jsonify({}), 202, {'Status': url_for('job_status', job_key=job.id), 'Cancel': url_for('job_cancel', job_key=job.id)}
	

@app.route('/emojiset/_run_large_task', methods=['POST'])
@login_required
def run_large_task():
	twitter_keys = {
		'access_token': current_user.access_token,
		'access_token_secret': current_user.access_token_secret,
		'consumer_key': current_user.consumer_key,
		'consumer_secret': current_user.consumer_secret
	}
	user_email = current_user.email

	result_directory = SavedResultDirectory(
		directory = user_email.split('@')[0]
	)
	db.session.add(result_directory)
	db.session.commit()

	query_id = request.form["query_id"]
	tweet_amount = request.form["tweet_amount"]
	time_length = request.form["time_length"]
	offset = request.form["time_offset"]
	extract_primary = request.form.getlist('extract_primary[]')
	extract_secondary = request.form.getlist('extract_secondary[]')
	file_name = request.form['file_name']

	finish_time = None
	if tweet_amount:
		tweet_amount = int(tweet_amount)
	if time_length:
		finish_time = calendar.timegm(time.strptime(time_length, "%Y-%m-%dT%H:%M")) + (int(offset) * 60)
	
	query_json = loads(SavedQuery.query.get(query_id).saved_query)
	
	twarc_method = query_json["twarc_method"]

	job = None
	job = long_task_q.enqueue(stream_large, twitter_keys, query_json["keywords"], query_json["discard"], twarc_method, query_json["form_data"]['languages'], query_json["form_data"]['result_type'], query_json["form_data"]['follow'], query_json["form_data"]['location'], tweet_amount, finish_time, user_email, extract_primary, extract_secondary, offset, file_name=file_name)
	
	job.meta['progress'] = 0
	job.meta['discarded_tweets'] = 0
	job.meta['query'] = query_json
	job.meta['cancel_flag'] = 0
	job.save_meta()

	query_for_response = ""
	if(twarc_method == 'search'):
		query_for_response = query_json["keywords"] + "| Discard tweets without emojis: " + str(query_json['discard'])
		if not query_json['form_data']['languages']:
			query_for_response += " | Language: all"
		else:
			query_for_response += " | Language: " + query_json['form_data']['languages']
		if not query_json['form_data']['location']:
			query_for_response += " | Location: world"
		else:
			query_for_response += " | Location: " + query_json['form_data']['location']
		query_for_response += " | Post type: " + query_json['form_data']['result_type']

	elif(twarc_method == 'filter'):
		query = []
		for keyword in query_json["keywords"]:
			keyword = emoji.demojize(keyword)
			query.append(keyword)
		query_for_response = ", ".join(query) + " | Discard tweets without emojis: " + str(query_json['discard'])
		if not query_json['form_data']['languages']:
			query_for_response += " | Language: all"
		else:
			query_for_response += " | Language: " + query_json['form_data']['languages']
		if not query_json['form_data']['location']:
			query_for_response += " | Location: world"
		else:
			query_for_response += " | Location: " + query_json['form_data']['location']
		if not query_json['form_data']['follow']:
			query_for_response += " | User: all"
		else:
			query_for_response += " | User: " + query_json['form_data']['follow']
	elif(twarc_method == 'sample'):
		query_for_response = "Discard tweets without emojis: " + str(query_json['discard'])
	return jsonify({}), 202, {'Status': url_for('job_status', job_key=job.id), 'Cancel': url_for('job_cancel', job_key=job.id), 'Query': query_for_response}


# ---get job object from the queue by the id and check its status (finished or not)---*
@app.route("/emojiset/status/<job_key>", methods=['GET'])
@login_required
def job_status(job_key):
	job = small_task_q.fetch_job(job_key)
	if job is None:
		job = long_task_q.fetch_job(job_key)
		if job is None:
			response = {'status': 'unknown'}
			return jsonify(response, 404)
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
	return jsonify(response, 202)


# ---get job object from the queue by the id and cancel it
@app.route("/emojiset/cancel/<job_key>", methods=['GET'])
@login_required
def job_cancel(job_key):
	job = small_task_q.fetch_job(job_key)
	if job is None:
		job = long_task_q.fetch_job(job_key)
		if job is None:
			response = {'status': 'unknown'}
			return jsonify(response, 404)
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
	RunningTask.query.filter_by(user_id=current_user.id).delete()
	db.session.commit()
	return jsonify(response, 200)


@app.route("/emojiset/save_query", methods=["POST"])
@login_required
def save_query():
	query = request.form['query']
	user_id = current_user.id
	user_email = current_user.email
	saved_query = SavedQuery(
		user_email = user_email,
		saved_query = query,
		user_id=user_id
	)
	db.session.add(saved_query)
	db.session.commit()
	return jsonify({})


@app.route("/emojiset/delete_query/<query_id>", methods=["GET"])
@login_required
def delete_query(query_id):
	SavedQuery.query.filter_by(id=query_id).delete()
	db.session.commit()
	return jsonify({})


@app.route("/emojiset/load_queries", methods=["GET"])
@login_required
def load_queries():
	saved_queries = SavedQuery.query.filter_by(user_id=current_user.id).group_by(SavedQuery.saved_query).all()
	response = {}
	for q in saved_queries:
		response[q.id] = q.saved_query
	return jsonify(response, 202)


@app.route("/emojiset/save_task", methods=["POST"])
@login_required
def save_task():
	running_task = RunningTask(
		user_email = current_user.email,
		task_query = request.form["task-query"],
		status_url = request.form["status-url"],
		cancel_url = request.form["cancel-url"],
		started_on = request.form["started-on"],
		finished_on = request.form["finished-on"],
		user_id = current_user.id
	)
	db.session.add(running_task)
	db.session.commit()
	return jsonify({})


@app.route("/emojiset/load_task", methods=["GET"])
@login_required
def load_task():
	running_task = RunningTask.query.filter_by(user_id=current_user.id).first()
	if running_task:
		response = {
			'task_query': running_task.task_query,
			'status_url': running_task.status_url,
			'cancel_url': running_task.cancel_url,
			'started_on': running_task.started_on,
			'finished_on': running_task.finished_on,
		}
	else:
		response = {}
	return jsonify(response, 202)	


@app.route("/emojiset/delete_task", methods=["GET"])
@login_required
def delete_task():
	RunningTask.query.filter_by(user_id=current_user.id).delete()
	db.session.commit()
	return jsonify({})


@app.route("/emojiset/save_finished_task", methods=["GET"])
@login_required
def save_finished_task():
	running_task = RunningTask.query.filter_by(user_id=current_user.id).first()
	if running_task:
		now = time.localtime()
		current_time = time.strftime("%Y-%m-%d %H:%M:%S", now)
		finished_task = FinishedTask(
			user_email = running_task.user_email,
			task_query = running_task.task_query,
			started_on = running_task.started_on,
			finished_on = current_time,
			user_id = current_user.id
		)
		db.session.add(finished_task)
		db.session.commit()
	return jsonify({})


@app.route("/emojiset/get_downloads", methods=["GET"])
@login_required
def get_file_list():
	uploads = os.path.join(app.root_path, app.config['UPLOAD_FOLDER']) + "/" + current_user.email.split('@')[0]
	try:
		subfolder_list = os.listdir(uploads)
		subfolder_list.sort(reverse=True)
	except FileNotFoundError:
		return jsonify(str(uploads), 404)
	current_url = request.url_root + "/emojiset/"
	html_files_list = ""
	for subfolder in subfolder_list:
		files = os.path.join(app.root_path, app.config['UPLOAD_FOLDER']) + "/" + current_user.email.split('@')[0] + "/" + subfolder
		try:
			file_list =os.listdir(files)
		except FileNotFoundError:
			return jsonify(str(files), 404)
		html_files_list += '<div class="card"><div class="list-group">'
		html_files_list += '<a class="list-group-item list-group-item-secondary">' + "Results from " + str(subfolder) + '</a>'
		for file in file_list:
			html_files_list += '<a class="list-group-item" href="' + current_url + 'download/' + str(subfolder) + '/' + str(file) + '">' + str(file) + '</a>'
		html_files_list += '</div></div><br>'
	response = {
		'file_list': html_files_list
	}
	return jsonify(response)


@app.route("/emojiset/download/<subfolder>/<file_name>", methods=["GET"])
@login_required
def download(subfolder, file_name):
	uploads = os.path.join(app.root_path, app.config['UPLOAD_FOLDER']) + "/" + current_user.email.split('@')[0] + '/' + str(subfolder)
	return send_from_directory(directory=uploads, filename=file_name, as_attachment=True)


@app.route("/contact_us", methods=["POST"])
def contact_us():
	contact_data = {}
	contact_data['name'] = request.form.get('name')
	contact_data['email'] = request.form.get('email')
	contact_data['message'] = request.form.get('message')
	if 'bug' in request.form:
		contact_data['bug'] = 'Yes'
	else:
		contact_data['bug'] = 'No'
	send_contact_us_message(contact_data)
	return jsonify({}), 200