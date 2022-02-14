import sqlite3

con = sqlite3.connect("DATA.db")
cur = con.cursor()

def DB_delite():
    sql = """DELETE FROM user_data"""
    cur.execute(sql)
    con.commit()
    sql = """DELETE FROM user_tweet_num"""
    cur.execute(sql)
    con.commit()
    sql = """DELETE FROM tweet_data"""
    cur.execute(sql)
    con.commit()

def DB_create():
    sql = """ CREATE TABLE user_tweet_num(id, latest_volue) """
    cur.execute(sql)
    con.commit()

    sql = """ CREATE TABLE tweet_data(title, txt, titleid, txtid, like, retweet, id) """
    cur.execute(sql)
    con.commit()

    sql = """ CREATE TABLE user_data(token, secret , verifier, id, key) """
    cur.execute(sql)
    con.commit()

def DB_refresh():
    print("Delited")
    DB_delite()
    DB_show()
    # print("created")
    # DB_create()

def DB_show():
    for row in cur.execute('SELECT * FROM user_data '):
        print(row)

    for row in cur.execute('SELECT * FROM user_tweet_num '):
        print(row)

    for row in cur.execute('SELECT * FROM tweet_data'):
        print(row)

if __name__ == "__main__":
    print("test")
    DB_refresh()
    DB_show()
    # DB_create()
