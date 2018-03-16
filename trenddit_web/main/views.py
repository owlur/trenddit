from django.shortcuts import render
from django.views import generic
from operator import itemgetter
import json
from trenddittools.access_db import ScoreDB
from trenddittools.analyse import trend_score
# Create your views here.


def connect(db, subreddit):
    res = trend_score('20170314')[subreddit]
    sorted_result = sorted(res.items(), key=itemgetter(1), reverse=True)

    return [i[0] for i in sorted_result[:5]]


def graph(db, subreddit, keywords):
    dates = sorted(db.db.collection_names())
    keyword = {}
    scores = [[], [], [], [], []]
    for i in keywords:
        keyword[i] = 1
    for i in dates:
        temp = db.find(collection=i, query={'SUBREDDIT': subreddit}, projection=keyword)[0]
        for n, j in enumerate(scores):
            if temp.get(keywords[n]):
                j.append(temp[keywords[n]])
            else:
                j.append(0)
    x = [list((map(int,[i[1:5], i[5:7], i[7:9]]))) for i in dates]

    return x, list(zip(scores[0], scores[1], scores[2], scores[3], scores[4]))


def index(request):
    subreddit = 'gaming'
    db = ScoreDB()
    res = connect(db, subreddit)
    date, data = graph(db, subreddit, res)
    return render(request, 'main/index.html', context={'rank':res,
                                                       'date': json.dumps(date),
                                                       'graph': json.dumps(data)})