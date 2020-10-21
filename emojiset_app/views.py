from emojiset_app import app
from emojiset_app import r
from emojiset_app import q
from emojiset_app.tasks import stream_task
from emojiset_app.utils import debug, construct_search_query, construct_filter_query, validate_and_parse_form, split_search_keywords, split_filter_keywords
from flask import render_template, request, redirect, url_for, jsonify
from time import strftime


# --- this function is called when user opens website/emojiset-mining url ---*
# --- displays the html page located in /templates forder
@app.route("/emojiset-mining", methods=['GET'])
def emojiset_mining():
    return render_template("emojiset_mining.html")


# --- this URL can't be directly accessed by user ---*
# --- this URL is being called using AJAX call when the submit button is clicked ---*
# --- request.form data is being passed to this URL in the AJAX call (request.form contains data that users has entered in the form) ---*
# --- this function reads all the values and parses them to ensure they are valid ---*
# --- after all of the data is read and parsed, creates a new job object which takes the function name, and parameters (check tasks.py) ---*
# --- returns empty json with one header (Location: website/status/<job_key>) which is later used to check the jobs status by its id (job_key) ---*
@app.route('/_run_task', methods=['POST'])
def run_task():
    # read values that are always present
    twarc_method = request.form["twarc-method"]
    tweet_amount = request.form["total_tweets"]
    discard_checked = "discard_box" in request.form
    
    keywords = ""
    if 'keywords' in request.form:
        keywords = request.form["keywords"]    
    
    discard = False
    if discard_checked:
        discard = True

    if not tweet_amount:
        tweet_amount = 10
    else:
        tweet_amount = int(tweet_amount)

    form_data = validate_and_parse_form(request.form, twarc_method)
    
    # ---to use additional settings properly we need to make sure that the query is constructed correctly---*
    
    if twarc_method == 'search':
        if form_data:
            keywords = construct_search_query(keywords, form_data['additional_settings'], form_data['operator'])
        else:
            keywords = split_search_keywords(keywords)
    if twarc_method == 'filter':
        if form_data:
            keywords = construct_filter_query(keywords, form_data['additional_settings'])
        else:
            keywords = split_filter_keywords(keywords)


    # ---send a job to the task queue---*
    job = None
    if form_data:
        job = q.enqueue(stream_task, keywords, tweet_amount, discard, twarc_method, form_data['languages'], form_data['result_type'], form_data['follow'], form_data['location'], result_ttl=10)
    else:
        job = q.enqueue(stream_task, keywords, tweet_amount, discard, twarc_method, None, None, None, None, result_ttl=10)
    job.meta['progress'] = 0
    job.meta['discarded_tweets'] = 0
    job.meta['query'] = keywords
    job.save_meta()

    return jsonify({}), 202, {'Location': url_for('job_status', job_key=job.id)}


# ---get job object from the queue by the id and check its status (finished or not)---*
@app.route("/status/<job_key>", methods=['GET'])
def job_status(job_key):
    job = q.fetch_job(job_key)
    job.refresh()
    print("job key: " + job_key)
    if job is None:
        response = {'status': 'unknown'}
    else:
        response = {
            'status': job.get_status(),
            'progress': job.meta['progress'],
            'discarded_tweets': job.meta['discarded_tweets'],
            'result': job.result,
            'query': job.meta['query']
        }
    if job.is_failed:
        response['message'] = job.exc_info.strip().split('\n')[-1]
    return jsonify(response)
