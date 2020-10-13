from emojiset_app import app
from emojiset_app import r
from emojiset_app import q
from emojiset_app.tasks import stream_task

from flask import render_template, request, redirect, url_for, jsonify
from time import strftime


def debug(var):
    with open('out.txt', 'w') as f:
        print(var, file=f)   


@app.route("/emojiset-mining", methods=['GET', 'POST'])
def emojiset_mining():
    return render_template("emojiset_mining.html")


@app.route('/_run_task', methods=['POST'])
def run_task():
    keywords = request.form["keywords"]    
    tweet_amount = request.form["total_tweets"]
    twarc_method = request.form["twarc_method"]
    discard_checked = "discard_box" in request.form

    verified_users_only_checked = False
    additional_selection_settings_used = False

    #additional settings for selecting tweets (if languages are there, then everything else is there too)
    if("languages" in request.form):
        languages = request.form.getlist("languages")
        since_date = request.form["since-date"]
        until_date = request.form["until-date"]
        hashtags = request.form["hashtags"]
        from_user = request.form['from-user']
        to_user = request.form['to-user']
        mentioned_user = request.form['mentioned-user']
        result_type = request.form["result_type"]
        min_likes = request.form["min-likes"]
        max_likes = request.form["max-likes"]
        verified_users_checked = "verified" in request.form

        additional_selection_settings_used = True
    else:
        languages = ["all"]
        result_type = None

    discard = False
    if discard_checked:
        discard = True
    
    if not tweet_amount:
        tweet_amount = 100
    else:
        tweet_amount = int(tweet_amount)

    if len(languages) > 0:
        for lang in languages:
            if lang == "all":
                languages = None
        if languages:
            languages = " AND ".join(languages)

    if additional_selection_settings_used and twarc_method == 'search':
        keywords = construct_search_query(keywords, since_date, until_date, hashtags, from_user, to_user, mentioned_user, min_likes, max_likes, verified_users_checked)

    # Send a job to the task queue
    job = q.enqueue(stream_task, keywords, tweet_amount, discard, twarc_method, languages, result_type, result_ttl=500)
    job.meta['progress'] = 0
    job.meta['discarded_tweets'] = 0
    job.save_meta()

    return jsonify({}), 202, {'Location': url_for('job_status', job_key=job.id)}


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
        }
    if job.is_failed:
        response['message'] = job.exc_info.strip().split('\n')[-1]
    return jsonify(response)


# also include until date, verified users, maube max and min amount of likes, think about geocode
def construct_search_query(keywords, since_date, until_date, hashtags, from_user, to_user, mentioned_user, min_likes, max_likes, verified_users_checked):
    query = keywords.replace(" ", "").replace(",", " OR ")
    if since_date:
        query += " since:" + since_date + " "
    if until_date:
        query += " until:" + until_date + " "
    if from_user:
        query += " from:@" + from_user + " "
    if to_user:
        query += " to:@" + to_user + " "
    if mentioned_user:
        query += " -from:@" + mentioned_user + " @" + mentioned_user + " "
    if hashtags: 
        query += " #" + hashtags + " "
    if min_likes:
        query += " min_faves:" + min_likes + " "
    if max_likes:
        query += " -min_faves:" + max_likes + " "
    if verified_users_checked:
        query += " filter:verified "
    return query
