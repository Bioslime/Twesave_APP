import os 
import logging
from types import resolve_bases
from flask import Flask ,session, redirect, render_template, make_response, request
from datetime import datetime
import back_system as back


app = Flask(__name__, static_url_path="/static")
app.secret_key = "hgruihgfhdgljkfdhkslhjgfsiurhegjkfbj;ah;ajh"


@app.route("/")
def first_page():
    respones = back.enter_task()
    return respones

@app.route("/twitter_auth")
def twitter_auth():
    return back.tweauth()

@app.route("/tmp_site",methods = ["GET"])
def user_data_save():
    verifier = request.args.get("oauth_verifier")
    respones =  back.user_data_save(verifier)
    return respones

@app.route("/log_out")
def log_out():
    respones = back.log_out()
    return respones

@app.route("/ranking")
def ranking():
    respones = back.like_ranking_task()
    return respones

@app.route("/retweet/<ID>")
def retweet(ID):
    back.retweet(ID)
    return redirect("/")


@app.route("/reload")
def reload():
    back.tweet_data_get()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=80, threaded=True)

