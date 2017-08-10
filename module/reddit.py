import praw
import time
import date as dt

from access_db import ControlData


class Reddit:
    def __init__(self, db=None):
        """
        parameter db is instance of AccessDB()
        """

        client = open('client_key')

        self.reddit = praw.Reddit(client_id=client.readline(),
                                  client_secret=client.readline(),
                                  user_agent='my user agent')

        self.subreddits = ['programming',
                           'gaming',
                           'movies',
                           'hacking',
                           'worldnews',
                           'futurology',
                           'sports',
                           'news',
                           'music',
                           'science',
                           'technology',
                           'politics',
                           'nba',
                           'soccer',
                           'design'
                           ]
        if db:
            self.db = ControlData(db)
            self.dbname = 'reddit'

    def request2dbinsert(self, date, subreddit=None):
        """
        date를 1일 단위로 쪼개서 request 후 db에 넣음
        """
        """
        date를 20170228:20170301 로 받음
        start_date, end_date로 수정
        """

        start_time, end_time = dt.split_date(date)

        s = start_time
        while s < end_time:
            e = s + 86400

            request_time = dt.stamp2str(s) + ":" + dt.stamp2str(e)

            print("-" * 10 + request_time + " request " + "-" * 10)

            self.subreddits_request(request_subreddit=subreddit, date=request_time, parse=True, db=True)

            print("-" * 10 + request_time + " complete " + "-" * 10)

            s += 86400

    def subreddits_request(self, request_subreddit=None, date=None, parse=False, db=False):
        """
        :param request_subreddit:
        :param date:
        :param parse:
        :param db:
        :return:
        """
        """
        self.subreddits에 있는 서브렛딧들을 한번에 요청
        parse : parse 까지 실행
        db : db insert까지 실행 (parse가 true 일때만)
        """

        submissions = {}

        if request_subreddit:
            if type(request_subreddit) is list:
                subreddits = request_subreddit
            else:
                subreddits = [request_subreddit]

        else:
            subreddits = self.subreddits

        for subreddit in subreddits:
            print(subreddit + " request")
            submissions[subreddit] = self.list_request(subreddit, date=date)

            if parse:
                submissions[subreddit] = self.parse(submissions[subreddit])

                print(subreddit + " parse")

                if db:
                    self.db.input_posts(self.dbname, subreddit, submissions[subreddit])

                    print(subreddit + " insert to db ")

                    submissions[subreddit] = True

        return submissions

    def list_request(self, subreddit, num=None, date=None):
        """
        :param subreddit:
        :param num:
        :param date:
        :return:
        """
        """
        date를 20170228:20170301 형태로 받음"""

        if date:
            start_time, end_time = dt.split_date(date)

            print(start_time)
            print(end_time)

            query = "timestamp:" + str(int(start_time)) + ".." + str(int(end_time))

            result = self.reddit.subreddit(subreddit).submissions(start_time, end_time)

            if not result:
                raise NotImplementedError

        else:
            result = self.reddit.subreddit(subreddit).new(limit=num)

        return result

    def parse(self, reddit_list):
        """

        :param reddit_list:
        :return:
        """
        """
        post['id'] 를 post['ID'] 로 수정?"""
        posts = []

        time_start = int(time.time())
        timeout = 900

        while int(time.time()) < time_start + timeout:
            try:

                for submission in reddit_list:
                    comments = []
                    post = {}

                    post['id'] = submission.id
                    post['title'] = submission.title
                    post['date'] = submission.created
                    post['vote'] = submission.score
                    post['content'] = submission.selftext
                    post['url'] = submission.url

                    for temp_comment in list(submission.comments):

                        comment = {}

                        if not hasattr(temp_comment, 'body'):
                            continue

                        comment['id'] = temp_comment.id
                        comment['content'] = temp_comment.body
                        comment['date'] = temp_comment.created
                        comment['vote'] = temp_comment.score

                        comments.append(comment)

                    post['comments'] = comments

                    posts.append(post)


            except:
                # wait for 30 seconds since sending more requests to overloaded server might not be helping
                # last_exception = e
                print("*" * 50)
                print("error! waiting 30sec")
                print("*" * 50)
                time.sleep(30)
            else:
                break

        return posts
