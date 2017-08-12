# coding: utf-8

import math
from collections import defaultdict
from operator import itemgetter

from module import access_db, reddit, analyse


def start(): #현재까지 진행
    '''request_reddit = reddit.Reddit(db=True)
    request_reddit.request2dbinsert("20170306:20170309")
    for subreddit in request_reddit.subreddits:
        reddit_data = request_reddit.db.find(collection=subreddit)
        noun_result = analyse.posts_analyze(reddit_data)
        noun_db = access_db.NounDB()
        noun_db.input_posts(subreddit, noun_result)
    '''
    today = analyse.make_id_list('20170307')
    x_week = analyse.make_id_list('20170301', end_date='20170306')
    result = analyse.score(today, x_week)
    sorted_result = {}
    for subreddit in result:
        sorted_result[subreddit] = sorted(result[subreddit].items(), key=itemgetter(1), reverse=True)
        print("----------------subreddit----------------")
        for i in range(30):
            print(sorted_result[subreddit][i])



if __name__ == "__main__":
    # test_insert_score("20170108", "20170227")

    # start_date = "20170115"

    start()



'''    start_date = "20170227"
    end_date = "20170227"

    today = make_id_list("20170227", end_date="20170227")
    x_week = make_id_list("20170220", end_date="20170226")

    sss = Reddit().subreddits

    tf_idf_result = {}
    tf_idf_result = score(today, x_week)

    sorted_tf_idf = {}
    for i in sss:
        sorted_tf_idf[i] = sorted(tf_idf_result[i].items(), key=itemgetter(1), reverse=True)

    tf_result = {}
    for i in sss:
        tf_result[i] = tf(today[i])

    # In[112]:

    sorted_tf = {}
    for i in sss:
        sorted_tf[i] = sorted(tf_result[i].items(), key=itemgetter(1), reverse=True)

    # In[117]:

    trend_score = test_trend_score("20170227")
    sorted_trend = {}
    for i in sss:
        sorted_trend[i] = sorted(trend_score[i].items(), key=itemgetter(1), reverse=True)

    # In[125]:

    for i in sss:
        print("*" * 40 + i + "*" * 40)
        print(" " * 9 + "[" + "tf" + "]").ljust(30),
        print(" " * 7 + "[" + "tf-idf" + "]").ljust(30),
        print(" " * 5 + "[" + "trend_score" + "]")
        for j in range(30):
            print(str(j + 1) + ":" + sorted_tf[i][j][0] + str(sorted_tf[i][j][1])).ljust(30),
            print(str(j + 1) + ":" + sorted_tf_idf[i][j][0] + ":" + str(sorted_tf_idf[i][j][1])).ljust(30),
            print(str(j + 1) + ":" + sorted_trend[i][j][0] + ":" + str(sorted_trend[i][j][1]))
        print()


        # In[ ]:
'''