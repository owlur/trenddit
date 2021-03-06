import nltk
from collections import defaultdict
import math
from inflector import Inflector, English

from trenddittools import access_db
from trenddittools import date as dt


def posts_analyze(posts):
    """
    title, content, comment에서 명사 추출
    :param posts: 한개의 submission은 dict로 여러개의 submission은 list로 받음
                    Reddit.parse 의 return값과 동일한 형태를 가져야함
    :return: dict 형태로 키값은 명사, 밸류는 해당 명사의 빈도가 된다. ID키를 포함
    """
    if type(posts) is list:
        documents = []

        for post in posts:
            documents.append(posts_analyze(post))

        return documents

    elif type(posts) is dict:
        document = {'ID': posts['id']}

        document.update(parse_text(posts['title']))

        if posts['content']:
            document.update(parse_text(posts['content']))

        if posts['comments']:
            document['COMMENTS'] = []

            for comment in posts['comments']:
                comment_noun = parse_text(comment['content'])
                comment_noun['ID'] = comment['id']

                document['COMMENTS'].append(comment_noun)

        return document


def parse_text(text):
    return count_noun(tokenize(text))


def tokenize(text):
    """
    :param text: tokenize할 text
    :return:
    """
    tokens = nltk.word_tokenize(text)
    tagged_tokens = nltk.pos_tag(tokens)

    # parser_en = nltk.RegexpParser("NP: {<DT>?<JJ>?<NN.*>*}")
    # chunks_en = parser_en.parse(tagged_tokens)
    # chunks_en.draw()

    return tagged_tokens


def count_noun(tagged_tokens):
    """
    명사 추출 및 복수를 단수로 변환하는 작업
    :param tagged_tokens:
    :return:
    """
    noun_dict = defaultdict(lambda: 0)
    except_noun = [".", ",", "$", "[", "]", ">", "<", "/*", "*/", "*", "+", "-", "=", "%"]
    mongo_error_keyword = ['.', ',', '$']
    inflector = Inflector(English)

    for tagged_token in tagged_tokens:
        if "NN" in tagged_token[1]:
            noun = inflector.singularize(tagged_token[0].lower())

            if noun in except_noun \
                    or any(filter(lambda x: x in noun, mongo_error_keyword)) \
                    or not noun:
                continue

            noun_dict[noun] += 1

    return dict(noun_dict)


def make_id_list(date, end_date=None):
    """
    하루 이상의 데이터를 이용할 경우 끝나는 날을 end_date 입력
    make_id_list("20170101", end_date = "20170108")
    Reddit.subreddits 에 있는 모든 서브레딧에서 부터 해당하는 날짜의 명사들을 가져옴

    """
    interval = 86400
    start_time = dt.str2stamp(date)

    if end_date:
        end_time = dt.str2stamp(end_date)
    else:
        end_time = start_time + interval

    query = {"$and": [
        {"date": {"$gte": start_time}},
        {"date": {"$lt": end_time}}
    ]}

    projection = {"_id": 0, "id": 1}

    reddit_db = access_db.RedditDB()
    noun = access_db.NounDB()

    subreddits = reddit_db.subreddits

    id_list = {}

    for subreddit in subreddits:

        id_list[subreddit] = reddit_db.find(collection=subreddit, query=query, projection=projection)

        for ID in id_list[subreddit]:
            id_query = {"ID": ID["id"]}
            ID.pop('id')
            noun_list = noun.find(collection=subreddit, query=id_query)

            for nouns in noun_list:
                ID.update(nouns)

    return id_list


def df(documents):
    """
    ID, _id, COMMENTS, 명사명단이 포함된
    서브레딧하나만 받아야함
    """
    df = defaultdict(lambda : 0)

    exception = ["COMMENTS", "ID", "_id"]

    for submission in documents:
        nouns = set(submission)

        if "COMMENTS" in submission:
            for comment in submission["COMMENTS"]:
                nouns.union(set(comment))

        for noun in nouns:
            if noun not in exception:
                df[noun] += 1
    return df


def tf(documents):
    """
    ID, _id, COMMENTS, 명사명단이 포함된
    서브레딧하나만 받아야함
    """
    exception = ["COMMENTS", "ID", "_id"]

    tf = defaultdict(lambda: 0)
    df = defaultdict(lambda: 0)

    for submission in documents:
        frequency = defaultdict(lambda: 0)
        total = 0

        for noun_name in submission:
            if noun_name in exception:
                continue
            frequency[noun_name] += submission[noun_name]
            total += submission[noun_name]

        if "COMMENTS" in submission:
            for comments_list in submission["COMMENTS"]:
                for noun_name in comments_list:
                    if noun_name in exception:
                        continue

                    frequency[noun_name] += comments_list[noun_name]
                    total += comments_list[noun_name]

        for noun_name in frequency:
            tf[noun_name] += float(frequency[noun_name]) / total
            df[noun_name] += 1

    # sorted_tf = sorted(tf.items(), key=itemgetter(1), reverse = True)

    return tf, df


def tf_idf(for_tf, for_df):
    noun_df = defaultdict(lambda: 0)
    for subreddit in for_df:
        dfs = df(for_df[subreddit])
        for noun in dfs:
            noun_df[noun] += dfs[noun]

    df_total = sum(list(map(len, [for_df[i] for i in for_df])) + list(map(len, [for_tf[i] for i in for_tf])))

    all_tf = {}

    for subreddit in for_tf:
        all_tf[subreddit], dfs = tf(for_tf[subreddit])
        for noun in dfs:
            noun_df[noun] += dfs[noun]

    score = {}
    for subreddit in all_tf:
        score[subreddit] = {}
        for keyword in all_tf[subreddit]:
            score[subreddit][keyword] = all_tf[subreddit][keyword] * math.log10(float(df_total) / noun_df[keyword])

    # sorted_tf_idf = {}

    # sorted_tf_idf['programming'] = sorted(tf_idf['programming'].items(), key=itemgetter(1), reverse = True)

    return score


def insert_tf_idf(start_date, end_date):
    score_db = access_db.ScoreDB()

    stamp_start_date = int(dt.str2stamp(start_date))
    stamp_end_date = int(dt.str2stamp(end_date))

    day = 86400

    for date in range(stamp_start_date, stamp_end_date, day):
        x_week_date = dt.stamp2str(date - day * 7)
        yesterday = dt.stamp2str(date - day)

        today = dt.stamp2str(date)

        print(today, x_week_date, yesterday)

        today_list = make_id_list(today)
        x_week_list = make_id_list(x_week_date, end_date=yesterday)

        print(x_week_list)

        score = tf_idf(today_list, x_week_list)

        for subreddit in score:
            query = score[subreddit]
            query['SUBREDDIT'] = subreddit
            score_db.input_posts("d" + today, query)


def trend_score(date):
    score_db = access_db.ScoreDB()
    subreddits = access_db.RedditDB().subreddits

    x_week = dt.date2list(date, date, pre_day=7)
    x_week.remove(date)

    keyword_score = {}

    for subreddit in subreddits:
        query = {'SUBREDDIT': subreddit}
        today_scores = score_db.find(query= query, collection="d" + date)[0]
        x_week_scores = [score_db.find(query= query, collection="d" + i)[0] for i in x_week]

        keyword_score[subreddit] = {}
        for keyword in today_scores:
            if keyword == 'SUBREDDIT':
                continue
            score_sum = 0
            for scores in x_week_scores:
                if scores.get(keyword):
                    score_sum += scores[keyword]

            keyword_score[subreddit][keyword] = today_scores[keyword] - score_sum / len(x_week_scores)

    return keyword_score

if __name__ == '__main__':
    # a = access_db.AccessDB('reddit')
    # b = a.find(collection='hacking')

    # result = posts_analyze(b)

    # noun_db = access_db.NounDB()

    # noun_db.input_posts('hacking', result)

    test = make_id_list('20170301')

    for i in test:
        print(test[i])
        # print(make_id_list('20170301'))
