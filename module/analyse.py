import nltk
from collections import defaultdict

class Analyse:
    '''
    def __init__(self,db):
        self.DB = controlData(db)

    def get_posts(self,subreddit,date=None):
        dbname = 'reddit'
        posts = self.DB.findPost(dbname, collection = subreddit)
        return posts
        '''

    def tokenize(self, text):
        try:
            tokens = nltk.word_tokenize(text)
        except:
            print(text)
        tagged_tokens = nltk.pos_tag(tokens)

        # parser_en = nltk.RegexpParser("NP: {<DT>?<JJ>?<NN.*>*}")
        # chunks_en = parser_en.parse(tagged_tokens)
        # chunks_en.draw()

        return tagged_tokens

    def posts_analyze(self, posts):
        if type(posts) is list:
            documents = []

            for post in posts:
                documents.append(self.posts_analyze(post))

            return documents

        if type(posts) is dict:
            document = {'ID': posts['ID']}

            title_analyse = self.tokenize(posts['title'])

            document.update(self.choose_noun(title_analyse))

            if posts['content']:
                content_analyse = self.tokenize(posts['content'])

                document.update(self.choose_noun(content_analyse))

            if posts['comments']:
                document['COMMENTS'] = []

                for comment in posts['comments']:
                    comment_analyse = self.tokenize(comment['content'])

                    comment_noun = self.choose_noun(comment_analyse)
                    comment_noun['ID'] = comment['id']

                    document['COMMENTS'].append(comment_noun)

            return document

    def choose_noun(self, tagged_token):
        noun_dict = {}
        except_noun = [".", "[", "]", ">", "<", "/*", "*/", "*", "+", "-", "=", "%"]

        for i in range(len(tagged_token)):
            if "NN" in tagged_token[i][1]:

                noun = tagged_token[i][0].lower()

                if noun in except_noun or "." in noun:
                    continue

                if noun in noun_dict.keys():
                    noun_dict[noun] += 1

                else:
                    noun_dict[noun] = 1

        if type(noun_dict) is int:
            print(tagged_token)
        return noun_dict

    def token_input(self, tagged_token):  # tagged-token : nltk로 pos_tag한 token
        input_word = set()

        for i in range(len(tagged_token)):
            if "NN" in tagged_token[i][1]:
                input_word.add(tagged_token[i][0].lower())

        for word in input_word:
            if self.word_dict.has_key(word):
                self.word_dict[word] += 1
            else:
                self.word_dict[word] = 1

class Score:
    def make_id_list(date, end_date=None):
        '''
        하루 이상의 데이터를 이용할 경우 끝나는 날을 end_date 입력
        make_id_list("20170101", end_date = "20170108")
        Reddit.subreddits 에 있는 모든 서브레딧에서 부터 해당하는 날짜의 명사들을 가져옴

        '''
        day = 86400
        start_time = str2stamp(date)

        if end_date:
            end_time = str2stamp(end_date) + day
        else:
            end_time = start_time + day

        query = {"$and": [
            {"date": {"$gte": start_time}},
            {"date": {"$lt": end_time}}
        ]}

        projection = {"_id": 0, "ID": 1}

        reddit = AccessDB('reddit')

        noun = AccessDB('noun')

        subreddits = Reddit().subreddits

        id_list = {}

        for subreddit in subreddits:

            id_list[subreddit] = reddit.find(collection=subreddit, query=query, projection=projection)

            for ID in id_list[subreddit]:
                id_query = {"ID": ID["ID"]}
                noun_list = noun.find(collection=subreddit, query=id_query)

                for nouns in noun_list:
                    ID.update(nouns)

        return id_list

    def df(documents):
        """
        ID, _id, COMMENTS, 명사명단이 포함된
        서브레딧하나만 받아야함
        """
        df = {}

        exception = ["COMMENTS", "ID", "_id"]

        for submission in documents:
            df[submission["ID"]] = set()

            df[submission["ID"]] = set([i for i in submission if i not in exception])

            if "COMMENTS" not in submission:
                continue

            for comment in submission["COMMENTS"]:
                df[submission["ID"]] = df[submission["ID"]].union(set(
                    [i for i in comment if i not in exception]))

        return df

    def tf(documents):
        """
        ID, _id, COMMENTS, 명사명단이 포함된
        서브레딧하나만 받아야함
        """
        exception = ["COMMENTS", "ID", "_id"]

        tf = {}
        tf = defaultdict(lambda: 0, tf)

        for submission in documents:
            frequency = {}
            frequency = defaultdict(lambda: 0, frequency)
            total = 0

            for noun_name in submission.keys():
                if noun_name in exception:
                    continue
                frequency[noun_name] += float(submission[noun_name])
                total += submission[noun_name]

            if "COMMENTS" not in submission:
                continue

            for comments_list in submission["COMMENTS"]:
                for noun_name in comments_list.keys():
                    if noun_name in exception:
                        continue

                    frequency[noun_name] += float(comments_list[noun_name])
                    total += comments_list[noun_name]

            for noun_name in frequency.keys():
                tf[noun_name] += frequency[noun_name] / total

        # sorted_tf = sorted(tf.items(), key=itemgetter(1), reverse = True)

        return tf

    # In[13]:

    def score(for_tf, for_df):
        all_df = {}
        for subreddit in for_tf.keys():
            all_df.update(df(for_tf[subreddit]))

        for subreddit in for_df.keys():
            all_df.update(df(for_df[subreddit]))

        noun_df = {}
        noun_df = defaultdict(lambda: 0, noun_df)
        df_total = 0

        for sub_id in all_df.keys():
            for keyword in all_df[sub_id]:
                noun_df[keyword] += 1
            df_total += 1

        all_tf = {}

        for i in for_tf.keys():
            all_tf[i] = tf(for_tf[i])

        tf_idf = {}
        for subreddit in all_tf.keys():
            tf_idf[subreddit] = {}
            for keyword in all_tf[subreddit]:
                tf_idf[subreddit][keyword] = all_tf[subreddit][keyword] * math.log10(float(df_total) / noun_df[keyword])

        # sorted_tf_idf = {}

        # sorted_tf_idf['programming'] = sorted(tf_idf['programming'].items(), key=itemgetter(1), reverse = True)

        return tf_idf

    def test_insert_tf_idf(start_date, end_date):
        scoreDB = AccessDB('score')

        stamp_start_date = str2stamp(start_date)
        stamp_end_date = str2stamp(end_date)

        date = stamp_start_date

        day = 86400

        while (date <= stamp_end_date):
            x_week_date = stamp2str(date - day * 7)
            yesterday = stamp2str(date - day)

            today = stamp2str(date)

            today_list = make_id_list(today)
            x_week_list = make_id_list(x_week_date, end_date=yesterday)

            tf_idf = score(today_list, x_week_list)

            scoreDB.insert("d" + today, tf_idf)

            date += day

    # In[107]:

    def test_trend_score(date):
        scoreDB = AccessDB('score')

        documents = scoreDB.find(collection="d" + date)[0]

        x_week = date2list(date, date, pre_day=7)
        x_week.remove(date)

        x_week_document = [scoreDB.find(collection="d" + i)[0] for i in x_week]

        documents.pop("_id")

        keyword_score = {}

        for subreddit in documents.keys():
            keyword_score[subreddit] = {}
            for keyword in documents[subreddit].keys():
                score_sum = 0
                for i in range(len(x_week_document)):
                    if x_week_document[i][subreddit].get(keyword):
                        score_sum += x_week_document[i][subreddit][keyword]

                keyword_score[subreddit][keyword] = documents[subreddit][keyword] - score_sum / len(x_week_document)

        return keyword_score