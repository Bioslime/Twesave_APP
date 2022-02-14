import os 
import logging
from flask import Flask ,session, redirect, render_template, make_response, request
from datetime import datetime
import sqlite3
import tweepy
import uuid


CK = ************************************
CS = *************************************
max_age = 60 * 60 * 24 * 1
logging.warning("app start!")




def enter_task():
    ukey = request.cookies.get("ukey", None)
    if ukey != None:
        con = sqlite3.connect("DATA.db")
        cur = con.cursor()
        sql = """ SELECT * FROM user_data WHERE key = '%s' """%(ukey)
        tmp = cur.execute(sql)
        data = [row for row in tmp]
        if len(data) == 1:
            tweet_data_get()
            tweet_update()
            title, txt, like, retweet, titleid, textid = tweet_load(data[0][3])
            return make_response(render_template("user_page.html", txt=txt, title=title, like=like, retweet=retweet, titled=titleid, textid=textid,  lenge = len(txt)))
    return make_response(render_template("main.html"))

def tweauth():
    auth = tweepy.OAuthHandler(CK, CS)
    redirect_url = auth.get_authorization_url()
    try:
        session["request_token"] = auth.request_token
        logging.error(session["request_token"])
    except tweepy.TweepError as e:
        logging.error(str(e))
    return make_response(redirect(redirect_url))

def user_data_save(verifier):
    con = sqlite3.connect("DATA.db")
    cur = con.cursor()
    token = session.pop("request_token", None)

    auth = tweepy.OAuthHandler(CK, CS)
    auth.request_token = token
    auth.get_access_token(verifier)
    api = tweepy.API(auth, wait_on_rate_limit = True)
    user_id = api.me().id
    sql = """ SELECT * FROM user_data WHERE id = "%s" """%(user_id)
    tmp = cur.execute(sql)
    data = [row for row in tmp]
    ukey = str(uuid.uuid4())

    if len(data) ==  0:
        sql = """INSERT INTO user_data VALUES("%s", "%s", "%s", "%s", "%s")"""%(auth.access_token, auth.access_token_secret, verifier, user_id, ukey)
        cur.execute(sql)
        con.commit()
        sql = """INSERT INTO user_tweet_num VALUES("%s", "%s")"""%(user_id, "0")
        cur.execute(sql)
        con.commit()

        for row in cur.execute('SELECT * FROM user_data '):
            print(row)
    else:
        sql = """ UPDATE user_data SET token = "%s" , secret= "%s" ,verifier= "%s" ,key= "%s" WHERE id = "%s" """%(auth.access_token, auth.access_token_secret, verifier, ukey,  user_id)
        cur.execute(sql)
        con.commit()
        for row in cur.execute('SELECT * FROM user_data '):
            print(row)

    respones = make_response(redirect("/"))
    expires = int(datetime.now().timestamp()) + max_age
    respones.set_cookie("ukey", value=ukey, max_age=max_age, expires=expires)
    return respones


def user_data_load():
    con = sqlite3.connect("DATA.db")
    cur = con.cursor()
    ukey = request.cookies.get("ukey", None)
    sql = """ SELECT * FROM user_data WHERE key = '%s' """%(ukey)
    tmp = cur.execute(sql)
    data = [row for row in tmp]
    return data[0]


def tweet_data_get():
    data = user_data_load()
    con = sqlite3.connect("DATA.db")
    cur = con.cursor()

    tweets = []

    auth = tweepy.OAuthHandler(CK, CS)
    auth.set_access_token(data[0], data[1])
    user_id = int(data[3])
    api = tweepy.API(auth, wait_on_rate_limit = True)
    tweet_num = api.me().statuses_count
    sql = """ SELECT * FROM user_tweet_num WHERE id = '%s' """%(user_id)
    tmp = cur.execute(sql)
    last_num = int([row for row in tmp][0][1])
    page = int((tweet_num - last_num)/200 ) + 1
    count = tweet_num - last_num - 200 * (page - 1)
    if page == 1 and count == 0:
        return
    elif page != 1 and count == 0:
        page = page -1
        count = 200

    for i in range(page):
        tweets.extend(api.user_timeline(id=user_id, count=count, page=i+1, tweet_mode="extended"))
        # tweets.extend(api.user_timeline(id=user_id, count=count, page=i+1, tweet_mode='extended'))
    # tweets = api.user_timeline(id=user_id, count=200, page=1)
    sql = """ UPDATE user_tweet_num SET tweet_num= "%s" WHERE id = "%s" """%(tweet_num, user_id)
    cur.execute(sql)
    con.commit()

    for tweet in tweets:
        t = tweet.in_reply_to_user_id
        if t == user_id:
            txt_id = tweet.in_reply_to_status_id
            txt = api.get_status(id=txt_id, tweet_mode="extended").full_text
            title = tweet.full_text
            if "#ツイ説保存" not in title:
                continue
            title = title.replace("#ツイ説保存", "")
            title_id = tweet.id
            txt_id = api.get_status(id=txt_id).id
            like = api.get_status(id=txt_id).favorite_count
            retweet = api.get_status(id=txt_id).retweet_count

            sql = """INSERT INTO tweet_data VALUES("%s", "%s", "%s", "%s", "%s", "%s", "%s" )"""%(title, txt, title_id, txt_id, like, retweet, user_id)
            cur.execute(sql)
            con.commit()

def tweet_load(id):
    con = sqlite3.connect("DATA.db")
    cur = con.cursor()
    sql = """ SELECT * FROM tweet_data WHERE id = '%s' """%(id)
    tmp = cur.execute(sql)
    
    data = [row for row in tmp]
    title = [data[len(data)-i-1][0] for i in range(len(data))]
    txt = [data[len(data)-i-1][1] for i in range(len(data))]
    like = [data[len(data)-i-1][4] for i in range(len(data))]
    retweet = [data[len(data)-i-1][5] for i in range(len(data))]
    titleid = [data[len(data)-i-1][2] for i in range(len(data))]
    textid = [data[len(data)-i-1][3] for i in range(len(data))]

    return title, txt, like, retweet, titleid, textid

def log_out():
    con = sqlite3.connect("DATA.db")
    cur = con.cursor()
    try:
        sql = """ UPDATE user_data SET key= "0" WHERE key = "%s" """%(request.cookies.get("ukey", None))
    except Exception:
        pass
    cur.execute(sql)
    con.commit()

    for row in cur.execute('SELECT * FROM user_data '):
        print(row)

    return make_response(redirect("/"))


def tweet_update():
    con = sqlite3.connect("DATA.db")
    cur = con.cursor()

    data = user_data_load()

    auth = tweepy.OAuthHandler(CK, CS)
    auth.set_access_token(data[0], data[1])
    api = tweepy.API(auth, wait_on_rate_limit = True)

    id = int(data[3])

    sql = """ SELECT * FROM tweet_data WHERE id = '%s' """%(id)

    tweets = [tweet for tweet in cur.execute(sql)]

    for tweet in tweets:
        txt_id = tweet[3]
        like = api.get_status(id=txt_id).favorite_count
        retweet = api.get_status(id=txt_id).retweet_count
        sql = """ UPDATE tweet_data SET like = "%s", retweet = "%s" WHERE txtid = "%s" """%(like, retweet, txt_id)
        cur.execute(sql)
        con.commit()

def ranking_task():
    ukey = request.cookies.get("ukey", None)
    if ukey != None:
        con = sqlite3.connect("DATA.db")
        cur = con.cursor()
        sql = """ SELECT * FROM user_data WHERE key = '%s' """%(ukey)
        tmp = cur.execute(sql)
        data = [row for row in tmp]
        if len(data) == 1:
            tweet_data_get()
            tweet_update()
            title, txt, like, retweet, titleid, textid = tweet_load(data[0][3])
            like_set = reversed(sorted(list(set(like)))) 
            print(like_set)
            lst = [[title[i], txt[i], like[i], retweet[i], titleid[i], textid[i]] for i in range(len(title))]
            ranklst = []
            for i in like_set:
                print(i)
                tmp = []
                for dataset in lst:
                    if i == dataset[2]:
                        print(dataset)
                        ranklst.append(dataset)
                        tmp.append(dataset)
                for j in tmp:
                    lst.remove(j)

            txt = [ranklst[i][1] for i in range(len(ranklst))]
            title = [ranklst[i][0] for i in range(len(ranklst))]
            like = [ranklst[i][2] for i in range(len(ranklst))]
            retweet = [ranklst[i][3] for i in range(len(ranklst))]
            titleid = [ranklst[i][4] for i in range(len(ranklst))]
            textid = [ranklst[i][5] for i in range(len(ranklst))]

            return make_response(render_template("user_page.html", txt=txt, title=title, like=like, retweet=retweet, titled=titleid, textid=textid,  lenge = len(txt)))
    return make_response(render_template("main.html"))

def retweet(ID):
    data = user_data_load()
    auth = tweepy.OAuthHandler(CK, CS)
    auth.set_access_token(data[0], data[1])
    api = tweepy.API(auth, wait_on_rate_limit = True)
    while True:
        try:
            api.retweet(ID)
            return
        except tweepy.TweepError as e:
            status  = api.get_status(ID,include_my_retweet=1)
            if status.retweeted == True:
                api.destroy_status(status.current_user_retweet['id'])
            logging.error(e)