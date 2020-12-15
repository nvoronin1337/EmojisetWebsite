import json
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_message(user_email):
    MAIL_USERNAME = 'testemojiset@gmail.com'
    MAIL_PASSWORD = 'Em0jiset!'

    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.ehlo()
    s.starttls()
    s.ehlo()
    s.login(MAIL_USERNAME, MAIL_PASSWORD)
    toEmail = user_email
    fromEmail = MAIL_USERNAME
    msg = MIMEMultipart('alternative')
    msg['Subject'] = 'Finished Collecting Tweets'
    msg['From'] = fromEmail
    body = 'We have finished collecting tweets for you! Please follow this link to download your results: https://www.sogoresearch.com/emojiset. Please note that you have 7 days to download your results since they will be deleted after that.'

    content = MIMEText(body, 'plain')
    msg.attach(content)
    s.sendmail(fromEmail, toEmail, msg.as_string())

def send_contact_us_message(form):
    MAIL_USERNAME = 'testemojiset@gmail.com'
    MAIL_PASSWORD = 'Em0jiset!'

    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.ehlo()
    s.starttls()
    s.ehlo()
    s.login(MAIL_USERNAME, MAIL_PASSWORD)
    
    toEmail = 'sothman@kent.edu'
    fromEmail = MAIL_USERNAME
    msg = MIMEMultipart('alternative')
    msg['Subject'] = 'SOGOResearch Message from ' + form['name']
    msg['From'] = fromEmail
    body = "Email: " + form['email'] + "\n"
    body += "Is this a bug report? " + form['bug'] + "\n\n"
    body += form['message']

    content = MIMEText(body, 'plain')
    msg.attach(content)
    s.sendmail(fromEmail, toEmail, msg.as_string()) 

def load_key():
    """
    Loads the key named `secret.key` from the current directory.
    """
    return open(os.path.dirname(__file__) + '/secret.key').read()

# ---converts error to txt file and immediately outputs---*
def debug(var, filename='out.txt'):
    with open(filename, 'a+') as f:
        print(var, file=f)


def query_to_json(keywords, discard, twarc_method, form_data=None):
    if form_data:
        json_data = {
            'keywords': keywords,
            'discard': discard,
            'twarc_method': twarc_method,
            'form_data': form_data
        }
    else:
        json_data = {
            'keywords': keywords,
            'discard': discard,
            'twarc_method': twarc_method
        }
    json_query = json.dumps(json_data)
    return json_query


def split_search_keywords(keywords):
    keywords_stripped_list = []
    keywords_list = keywords.split(',')
    for keyword in keywords_list:
        keyword = keyword.strip()
        keywords_stripped_list.append(keyword)
    keywords = " OR ".join(keywords_stripped_list)
    return keywords


def split_filter_keywords(keywords):
    keyword_list = []
    keywords = keywords.split(',')
    for key in keywords:
        key = key.strip()
        keyword_list.append(key)
    return keyword_list


def validate_and_parse_form(form, method):
    output = {}
    additional_settings = {}
    languages = None
    result_type = None
    location = None
    follow_user = None
    operator = None
    if method == "search":
        languages = form.get('languages')
        if languages == 'all':
                languages = None
        long = form.get('long')
        lat = form.get('lat')
        radius = form.get('radius')
        if not radius:
            radius = '10'
        # ---location for search---*
        if 'units' in form:
            units = 'km'
        else:
            units = 'mi'
        additional_settings['since_date'] = form.get('since-date')
        additional_settings["until_date"] = form.get("until-date")
        additional_settings["from_user"] = form.get("from-user")
        additional_settings["to_user"] = form.get("to-user")
        additional_settings["mentioned_user"] = form.get("mentioned-user")
        additional_settings["min_likes"] = form.get("min-likes")
        additional_settings["max_likes"] = form.get("max-likes")
        additional_settings["verified_users_checked"] = "verified" in form
        result_type = form.get("result_type")
        if 'operator' in form:
            operator = 'AND'
        else:
            operator = 'OR'
        if long and lat:
            location = long + ',' + lat + ',' + radius + units
    elif method == "filter":
        languages = form.get('languages_filter')
        if languages == 'all':
                languages = None
        long = form.get('long_filter')
        lat = form.get('lat_filter')
        radius = form.get('radius_filter')
        if not radius:
            radius = '10'
        # ---location for filter---*
        if 'units_filter' in form:
            units = 'km'
        else:
            units = 'mi'
        if long and lat:
            if units == 'mi':
                radius = round(float(radius) * 0.62137, 4)
            bounding_box = create_bounding_box(long, lat, radius)
            location = str(bounding_box[0]) + ',' + str(bounding_box[1]) + ',' + str(bounding_box[2]) + ',' + str(bounding_box[3])
        follow_user = form.get('from-user_filter')
    output['additional_settings'] = additional_settings
    output['languages'] = languages
    output['result_type'] = result_type
    output['location'] = location
    output['follow'] = follow_user
    output['operator'] = operator
    return output


# --- creates box for filter's location option ---*
# --- accepts longitude, latitude and radius ---*
# --- creates a rombus with 'radius' being its width ---*
# --- returns 4 points that represent the rombus on the map ---*
def create_bounding_box(long, lat, radius):
    long = float(long)
    lat = float(lat)
    radius = float(radius)
    km = 0.00904 #1 / 110.574
    left = round(long - (radius * km),4)
    up = round(lat + (radius * km),4)
    right = round(long + (radius * km),4)
    down = round(lat - (radius * km),4)
    return (down,left, up, right)


#TO DO: (make country, city, and near me options work for premium API)
def construct_search_query(keywords, additional_settings, operator):
    query = keywords
    if keywords:
        query = split_search_keywords(keywords)

    # ---search by mentioned users: -from:@user @user OR -from:user2 @user2 (-from@user insures that we don't get tweets from the user, only mentiones of him posted by other uses)---*
    if additional_settings['mentioned_user']:
        mentioned_users_query = make_multiple_arguments_query(additional_settings['mentioned_user'], '-from:@', "OR", second_param_name='@')
        if query:
            query += " " + operator + ' ' + mentioned_users_query
        else:
            query += mentioned_users_query
    # ---search tweets posted by user: from:user OR from:user2---*
    if additional_settings['from_user']:
        from_users_query = make_multiple_arguments_query(additional_settings['from_user'], "from:@", "OR")
        if query:
            query += " " + operator + ' ' + from_users_query
        else:
            query += from_users_query
    # ---search tweets directed to user: to:user OR to:user2---*
    if additional_settings['to_user']:
        to_user_query = make_multiple_arguments_query(additional_settings['to_user'], "to:@", "OR")
        if query:
            query += " " + operator + ' ' + to_user_query
        else:
            query += to_user_query
    # ---search tweets that have at least specified amount of likes: min_faves:100---*
    if additional_settings['min_likes']:
        min_likes_query = "min_faves:" + additional_settings['min_likes']
        if query:
            query += ' ' + min_likes_query
        else:
            query += min_likes_query
    # ---search tweets that have no more than specified amount of likes: -min_faves:500---*
    if additional_settings['max_likes']:
        max_likes_query = "-min_faves:" + additional_settings['max_likes']
        if query:
            query += ' ' + max_likes_query
        else:
            query += max_likes_query
    # ---search tweets posted by verified users only: filter:verified---*
    if additional_settings['verified_users_checked']:
        verified_user_query = "filter:verified"
        if query:
            query += " " + operator + " " + verified_user_query
        else:
            query += verified_user_query
    # ---appending valid query for dates---*
    if additional_settings['since_date'] and additional_settings['until_date']:
        dates_range_query = "since:" + additional_settings['since_date'] + ' ' + "until:" + additional_settings['until_date']
        if query:
            query += " " + dates_range_query
        else:
            query += dates_range_query
    return query


# ---creates a valid multi parameter query (EX:'hashtag1, hashtag2' => ' #hashtag1 OR/AND #hashtag2')---*
def make_multiple_arguments_query(input_str, param_name, separator, second_param_name=None):
    query = ""
    input_list = input_str.replace(' ','').replace('#','').replace('@','').split(',')
    for input in input_list:
        if(second_param_name):
            query += param_name + input + ' ' + second_param_name + input + ' ' + separator + ' '
        else:         
            query += param_name + input + ' ' + separator + ' '
    query = query[:-(len(separator) + 2)]
    return query
