import praw
import time
import module.date as dt

from module import access_db


class RedditRequestError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class TimestampIsNotAvailable(RedditRequestError):
    pass


class Reddit:
    def __init__(self, db=None):
        """
        :param db: AccessDB 의 객체
        """

        client = open('client_key')  # reddit API 의 클라이언트 id와 secret 이 포함 된 파일

        self.reddit = praw.Reddit(client_id=client.readline()[:-1],
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
            self.db = access_db.ControlData(db)
            self.dbname = 'reddit'

    def request2dbinsert(self, date, *subreddit ):
        """
        reddit에 요청부터 db에 저장하는 작업까지 수행
        :type date: str
        :param date: '20170301:20170305'형태로 받음. 뒤에 날짜 전날 까지 요청
        :param subreddit: 요청할 subreddit, 없을 경우 self.subreddit에 등록된 모든 subreddit에 요청
        """

        start_time, end_time = dt.split_date(date)

        interval = 86400 # interval(초) 만큼의 간격으로 요청 interval은 86400(1일)의 약수가 되어여함

        s = start_time
        while s < end_time:
            e = s + interval

            request_time = str(int(s)) + ":" + str(int(e))

            print("-" * 10 + request_time + " request " + "-" * 10)

            self.subreddits_request(*subreddit, time_stamp=(s, e), parse=True, db=True)

            print("-" * 10 + request_time + " complete " + "-" * 10)

            s += interval

    def subreddits_request(self, *request_subreddit, time_stamp=None, parse=False, db=False):
        """
        여러개의 subreddit에 요청을 보냄
        :param request_subreddit: 요청할 subreddit. 없을 경우 self.subreddit에 등록된 subreddit에 요청함
        :param time_stamp: tuple 이나 list 형태로 시작시간과 마지막 시간을 받음 [0] : 시작시간 [1] : 마지막 시간
        :param parse: True 일 경우 parse()함수 까지 실행
        :param db: True 일경우 DB에 넣는 작업까지 수행
        :return: dictionary[subreddit]
        """

        submissions = {}

        if request_subreddit:
            subreddits = request_subreddit
        else:
            subreddits = self.subreddits

        for subreddit in subreddits:
            print(subreddit, ' 의 작업을 시작합니다.')
            submissions[subreddit] = self.list_request(subreddit, time_stamp=time_stamp)

            if parse:
                submissions[subreddit] = self.parse(submissions[subreddit])

                if db:
                    print('DB에 데이터를 저장 중 입니다.')
                    self.db.input_posts(self.dbname, subreddit, submissions[subreddit])

                    submissions[subreddit] = True

        return submissions

    def list_request(self, subreddit, num=None, time_stamp=None):
        """
        한개의 subreddit 에 대해서 요청
        :param subreddit: 요청할 subreddit
        :param num: 요청할 게시물 수 제한, 없을 경우 praw 기본 게시물제한 만큼 요청
        :param time_stamp: tuple 이나 list 형태로 시작시간과 마지막 시간을 받음 [0] : 시작시간 [1] : 마지막 시간
        :return: praw.Reddit.submissions 객체(Generator)
        """
        print('게시글 주소를 요청중입니다.')

        if time_stamp:
            if len(time_stamp) != 2:
                raise TimestampIsNotAvailable('Timestamp의 길이는 2가 되어야 합나디 ex) [\'시작시간\', \'마지막 시간\']')

            result = self.reddit.subreddit(subreddit).submissions(time_stamp[0], time_stamp[1])

            if not result:
                raise RedditRequestError('요청한 정보를 받지 못 하였습니다.')

        else:
            result = self.reddit.subreddit(subreddit).new(limit=num)

        return result

    def parse(self, reddit_list):
        """
        praw.Reddit.submissions 객체로 부터 submission 정보 추출
        :param reddit_list: praw.Reddit.submissions 객체
        :return:
        """
        """
        post['id'] 를 post['ID'] 로 수정?"""
        print('게시글로부터 정보를 받아오고 있습니다.')
        posts = []
        post = {}

        time_start = int(time.time())
        timeout = 900

        while int(time.time()) < time_start + timeout:
            try:
                for submission in reddit_list:
                    comments = []
                    post.clear()

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

                    posts.append(post.copy())

            except RedditRequestError:
                # 요청중 에러가 발생하면 30초 대기
                print("*" * 50)
                print("error! waiting 30sec")
                print("*" * 50)
                time.sleep(30)
            else:
                break

        return posts


if __name__ == "__main__":
    reddit_db = access_db.AccessDB()
    r = Reddit(reddit_db)

    r.request2dbinsert('20170301:20170302')
