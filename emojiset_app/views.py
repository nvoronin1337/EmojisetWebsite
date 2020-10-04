from emojiset_app import app
from emojiset_app import r
from emojiset_app import q
from emojiset_app.tasks import stream_task

from flask import render_template, request, redirect, url_for, jsonify
from time import strftime


@app.route("/emojiset-mining", methods=['GET', 'POST'])
def emojiset_mining():
    jobs = q.jobs  # Get a list of jobs in the queue
    #q_len = len(q)  # Get the queue length
    message = None 
    message = "No tasks queued"
            
    return render_template("emojiset_mining.html", message=message, jobs=jobs)


@app.route('/_run_task', methods=['POST'])
def run_task():
    keywords = request.form["keywords"]
    keywords.split(",")

    if(len(keywords) > 0):
        keywords.replace(" ", "")
    
    tweet_amount = request.form["total_tweets"]
    if not tweet_amount:
        tweet_amount = 100
    else:
        tweet_amount = int(tweet_amount)
    
    job = q.enqueue(stream_task, keywords, tweet_amount, result_ttl=500)  # Send a job to the task queue

    return jsonify({}), 202, {'Location': url_for('job_status', job_key=job.id)}


@app.route("/status/<job_key>", methods=['GET'])
def job_status(job_key):
    job = q.fetch_job(job_key)
    print("job key: " + job_key)
    if job is None:
        response = {'status': 'unknown'}
    else:
        response = {
            'status': job.get_status(),
            'result': job.result,
        }
    if job.is_failed:
        response['message'] = job.exc_info.strip().split('\n')[-1]
    return jsonify(response)
