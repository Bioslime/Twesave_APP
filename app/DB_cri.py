import sqlite3

con = sqlite3.connect("DATA.db")
cur = con.cursor()


# sql = """DELETE FROM user_data"""
# cur.execute(sql)
# con.commit()
# sql = """DELETE FROM user_tweet_num"""
# cur.execute(sql)
# con.commit()
# sql = """DELETE FROM tweet_data"""
# cur.execute(sql)
# con.commit()

sql = """ CREATE TABLE user_tweet_num(id, tweet_num) """
cur.execute(sql)
con.commit()

sql = """ CREATE TABLE tweet_data(title, txt, titleid, txtid, like, retweet, id) """
cur.execute(sql)
con.commit()

sql = """ CREATE TABLE user_data(token, secret , verifier, id, key) """
cur.execute(sql)
con.commit()


for row in cur.execute('SELECT * FROM user_data '):
    print(row)

for row in cur.execute('SELECT * FROM user_tweet_num '):
    print(row)

for row in cur.execute('SELECT * FROM tweet_data'):
    print(row)