from emojiset_app import app
from emojiset_app import r
from emojiset_app import q
from emojiset_app.tasks import stream_task

from flask import render_template, request, redirect, url_for, jsonify
from time import strftime


def debug(var):
    with open('out.txt', 'w') as f:
        print(var, file=f)


def create_bounding_box(long, lat, radius):
    long = float(long)
    lat = float(lat)
    radius = int(radius)
    km = 0.00904 #1 / 110.574
    left = round(long - (radius * km),4)
    up = round(lat + (radius * km),4)
    right = round(long + (radius * km),4)
    down = round(lat - (radius * km),4)
    return (left, up, right, down)


@app.route("/emojiset-mining", methods=['GET', 'POST'])
def emojiset_mining():
    return render_template("emojiset_mining.html")


@app.route('/_run_task', methods=['POST'])
def run_task():
    # read values that are always present
    keywords = request.form["keywords"]    
    tweet_amount = request.form["total_tweets"]
    twarc_method = request.form["twarc-method"]
    discard_checked = "discard_box" in request.form

    discard = False
    languages = None
    result_type = None
    geo = None
    radius = None
    units = None
    follow = None
    additional_settings = {}
    additional_selection_settings_used = False

    # read additional settings
    if "languages" in request.form:
        languages = request.form["languages"]
        
        additional_settings = {}
        additional_selection_settings_used = True
        if twarc_method == "search":
            additional_settings = {
                'since_date': request.form["since-date"],
                'until_date': request.form["until-date"],
                'hashtags': request.form["hashtags"],
                'from_user': request.form['from-user'],
                'to_user': request.form['to-user'],
                'mentioned_user': request.form['mentioned-user'],
                'result_type': request.form["result_type"],
                'min_likes': request.form["min-likes"],
                'max_likes': request.form["max-likes"],
                'verified_users_checked': "verified" in request.form,
                'near_me_checked': "near-me" in request.form,
                'city': request.form["city"],
                'radius': request.form["radius"],
                'units': request.form["units"],
            }
            radius = request.form["radius"]
            if not radius:
                additional_settings['radius'] = '10'
                radius = '10'
            units = request.form["units"]
            geo = request.form['long'] + ',' + request.form['lat']
            if len(geo) < 2:
                geo = None 
            else:
                geo += ',' + radius + units

            if additional_settings['from_user'] == additional_settings['mentioned_user']:
                additional_settings['from_user'] = ""
            
        elif twarc_method == "filter":
            follow = request.form['from-user']
            additional_settings = {
                'hashtags': request.form["hashtags"],
            }
            long = request.form['long']
            lat = request.form['lat']
            if long and lat:
                bounding_box = create_bounding_box(long, lat, 15)
                geo =  '\\' + str(bounding_box[0]) + ',' + str(bounding_box[1]) + ',' + str(bounding_box[2]) + ',' + str(bounding_box[3])

    if discard_checked:
        discard = True
    if not tweet_amount:
        tweet_amount = 100
    else:
        tweet_amount = int(tweet_amount)

    if additional_selection_settings_used:
        if twarc_method == 'search':
            keywords = construct_search_query(keywords, additional_settings)
        if twarc_method == 'filter':
            keywords = construct_filter_query(keywords, additional_settings)

    # Send a job to the task queue
    job = q.enqueue(stream_task, keywords, tweet_amount, discard, twarc_method, languages, result_type, follow, geo, result_ttl=500)
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


#TO DO: lat, long, country
def construct_search_query(keywords, additional_settings):
    query = keywords.replace(",", " OR ")
    if additional_settings['mentioned_user']:
        query += " -from:@" + additional_settings['mentioned_user'] + " @" + additional_settings['mentioned_user']
    if additional_settings['since_date']:
        query += " since:" + additional_settings['since_date']
    if additional_settings['until_date']:
        query += " until:" + additional_settings['until_date']
    if additional_settings['from_user']:
        query += " from:@" + additional_settings['from_user']
    if additional_settings['to_user']:
        query += " to:@" + additional_settings['to_user']
    if additional_settings['hashtags']: 
        query += " #" + additional_settings['hashtags']
    if additional_settings['min_likes']:
        query += " min_faves:" + additional_settings['min_likes']
    if additional_settings['max_likes']:
        query += " -min_faves:" + additional_settings['max_likes']
    if additional_settings['verified_users_checked']:
        query += " filter:verified"
    if additional_settings['near_me_checked']:
        query += " near:me"
        if additional_settings['radius']:
            query += " within:" + additional_settings['radius'] + additional_settings['units']
    elif additional_settings['city']:
        query += " near:" + additional_settings['city']
        if additional_settings['radius']:
            query += " within:" + additional_settings['radius'] + additional_settings['units']
    return query

def construct_filter_query(keywords, additional_settings):
    query = keywords
    if additional_settings['hashtags']:
        query += " #" + additional_settings['hashtags']
    return query