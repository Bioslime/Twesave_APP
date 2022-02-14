import os 
import logging
from flask import Flask ,session, redirect, render_template, make_response, request
from datetime import datetime
import sqlite3
import tweepy
import uuid

CK = "c0FMfavwrXcAG6zBFjxs8tM6v"
CS = "teMLByDGOORNval7K3Yz78c6Tg2nbT8mg3VatHKARTNv0HAJL9"
max_age = 60 * 60 * 24 * 1
logging.warning("app start!")

def enter_task():
    # 認証確認　認証済み→ユーザーぺージ　未認証→認証
    user_key = request.cookies.get("key", None)
    if user_key != None:
        sql_code = """ SELECT * FROM user_data WHERE key = '%s' """%(user_key)
        user_data_len = len(DB_read(sql_code))
        if user_data_len == 1:
            title, txt, like, retweet, titleid, textid = tweet_load()
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


def DB_read(sql_code):
    con = sqlite3.connect("DATA.db")
    cur = con.cursor()
    tmp = cur.execute(sql_code)
    data = [row for row in tmp]
    return data


def DB_write(sql_code):
    con = sqlite3.connect("DATA.db")
    cur = con.cursor()
    cur.execute(sql_code)
    con.commit()


def tweet_load():
    user_id = user_data_load()[3]
    sql_code = """ SELECT * FROM tweet_data WHERE id = '%s' """%(user_id)
    data = DB_read(sql_code)
    lenge = len(data)
    rangen = range(lenge)

    title = [data[lenge-i-1][0] for i in rangen]
    txt = [data[lenge-i-1][1] for i in rangen]
    titleid = [data[lenge-i-1][2] for i in rangen]
    textid = [data[lenge-i-1][3] for i in rangen]
    like = [data[lenge-i-1][4] for i in rangen]
    retweet = [data[lenge-i-1][5] for i in rangen]
    
    return title, txt, like, retweet, titleid, textid


def user_data_load():
    while True:
        try:
            user_key = request.cookies.get("key", None)
            break
        except:
            tweauth()
    sql_code = """ SELECT * FROM user_data WHERE key = '%s' """%(user_key)
    data = DB_read(sql_code)
    return data[0]


def user_api_load():
    user_data = user_data_load()
    auth = tweepy.OAuthHandler(CK, CS)
    auth.set_access_token(user_data[0], user_data[1])
    api = tweepy.API(auth, wait_on_rate_limit = True)
    return api


def user_api_get(verifier):
    token = session.pop("request_token", None)
    auth = tweepy.OAuthHandler(CK, CS)
    auth.request_token = token
    auth.get_access_token(verifier)
    api = tweepy.API(auth, wait_on_rate_limit = True)

    user_id = api.me().id
    token = auth.access_token
    secret_token = auth.access_token_secret

    return user_id, token, secret_token  


def tweet_data_get():
    api = user_api_load()
    tweet_num = api.me().statuses_count

    user_id = int(user_data_load()[3])
    sql_code = """ SELECT * FROM user_tweet_num WHERE id = '%d' """%(user_id)
    last_num = int(DB_read(sql_code)[0][1])
    new_tweet = tweet_num - last_num
    # tweet_tmp = []
    tweets = []

    page_per_num = 100
    page = int(new_tweet/page_per_num ) + 1
    if new_tweet > 0:
        for i in range(page):
            tweets.extend(api.user_timeline(id=user_id, count=page_per_num, page=i+1, tweet_mode="extended"))
    else:
        return

    sql_code = """ UPDATE user_tweet_num SET latest_volue= "%s" WHERE id = "%d" """%(tweet_num, user_id)
    DB_write(sql_code)

    sql_code = """ SELECT * FROM tweet_data WHERE id = '%d' """%(user_id)
    tmp = DB_read(sql_code)
    if tmp == None:
        save_ids = [0]
    else:
        save_ids = [int(tmp[i][3]) for i in range(len(tmp))]
    print("test\n", save_ids)
    for tweet in tweets:
        t = tweet.in_reply_to_user_id
        if t == user_id:
            txt_id = tweet.in_reply_to_status_id
            print(txt_id, ":txt_id\n")
            if txt_id in save_ids:
                continue
            txt = api.get_status(id=txt_id, tweet_mode="extended").full_text
            title = tweet.full_text
            if "#ツイ説保存" not in title:
                continue
            title = title.replace("#ツイ説保存", "")
            title_id = tweet.id
            txt_id = api.get_status(id=txt_id).id
            like = api.get_status(id=txt_id).favorite_count
            retweet = api.get_status(id=txt_id).retweet_count

            sql_code = """INSERT INTO tweet_data VALUES("%s", "%s", "%s", "%s", "%s", "%s", "%d" )"""%(title, txt, title_id, txt_id, like, retweet, user_id)
            DB_write(sql_code)


def user_data_save(verifier):
    user_id, token, secret_token  = user_api_get(verifier)
    sql_code = """ SELECT * FROM user_data WHERE id = "%s" """%(user_id)
    data = DB_read(sql_code)
    user_key = str(uuid.uuid4())

    if len(data) ==  0:
        sql_code = """INSERT INTO user_data VALUES("%s", "%s", "%s", "%s", "%s")"""%(token, secret_token, verifier, user_id, user_key)
        DB_write(sql_code)
        sql_code = """INSERT INTO user_tweet_num VALUES("%s", "%s")"""%(user_id, "0")
        DB_write(sql_code)
    else:
        sql_code = """ UPDATE user_data SET token = "%s" , secret= "%s" ,verifier= "%s" ,key= "%s" WHERE id = "%s" """%(token, secret_token, verifier, user_key, user_id)
        DB_write(sql_code)

    respones = make_response(redirect("/"))
    expires = int(datetime.now().timestamp()) + max_age
    respones.set_cookie("key", value=user_key, max_age=max_age, expires=expires)
    return respones


def log_out():
    try:
        sql_code = """ UPDATE user_data SET key= "0" WHERE key = "%s" """%(request.cookies.get("key", None))
        DB_write(sql_code)
    except Exception:
        pass

    return make_response(redirect("/"))


def like_ranking_task():
    user_key = request.cookies.get("key", None)
    if user_key != None:
        sql_code = """ SELECT * FROM user_data WHERE key = '%s' """%(user_key)
        user_data_len = len(DB_read(sql_code))
        if user_data_len == 1:
            title, txt, like, retweet, titleid, textid = tweet_load()
            #並び替え(いいね順)-------------
            like_set = reversed(sorted(list(set(like))))
            lst = [[title[i], txt[i], like[i], retweet[i], titleid[i], textid[i]] for i in range(len(title))]
            ranklst = []
            for i in like_set:
                tmp = []
                for dataset in lst:
                    if i == dataset[2]:
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
    api = user_api_load()
    while True:
        try:
            api.retweet(ID)
            return
        except tweepy.TweepError as e:
            status  = api.get_status(ID, include_my_retweet=1)
            if status.retweeted == True:
                api.destroy_status(status.current_user_retweet['id'])
            logging.error(e)



if __name__ == "__main__" :

    sql_code = """ SELECT * FROM user_data WHERE key = '%s' """%("317f1d7f-2f58-4491-b3d3-5ecc3975b950")
    data = DB_read(sql_code)
    print(data)