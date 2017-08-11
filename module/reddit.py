import praw
import time
import module.date as dt

from module.access_db import ControlData


class Reddit:
    def __init__(self, db=None):
        """
        :param db: AccessDB 의 인스턴스
        """

        client = open('client_key') # reddit API 의 클라이언트 id와 secret 이 포함 된 파일

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
            self.db = ControlData(db)
            self.dbname = 'reddit'

    def request2dbinsert(self, date, subreddit=None):
        """
        reddit에 요청부터 db에 저장하는 작업까지 수행
        :type date: str
        :param date: '20170301:20170305'형태로 받음. 뒤에 날짜까지 포함하여 요청
        :param subreddit: 요청할 subreddit, 없을 경우 self.subreddit에 등록된 모든 subreddit에 요청
        """
        """
        date를 20170228:20170301 로 받음
        start_date, end_date로 수정
        """

        interval = 86400  # 86400초(1일) 단위로 나눠서 요청

        start_time, end_time = dt.split_date(date)

        s = start_time
        while s < end_time:
            e = s + interval

            request_time = dt.stamp2str(s) + ":" + dt.stamp2str(e)

            print("-" * 10 + request_time + " request " + "-" * 10)

            self.subreddits_request(request_subreddit=subreddit, date=request_time, parse=True, db=True)

            print("-" * 10 + request_time + " complete " + "-" * 10)

            s += interval

    def subreddits_request(self, request_subreddit=None, date=None, parse=False, db=False):
        """
        여러개의 subreddit에 요청을 보냄
        :param request_subreddit: 요청할 subreddit. 없을 경우 self.subreddit에 등록된 subreddit에 요청함
        :param date: '20170301:20170305'형태로 받음. 뒤에 날짜까지 포함하여 요청
        :param parse: True 일 경우 parse()함수 까지 실행
        :param db: True 일경우 DB에 넣는 작업까지 수행
        :return: dictionary[subreddit]
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
        한개의 subreddit 에 대해서 요청
        :param subreddit: 요청할 subreddit
        :param num: 요청할 게시물 수 제한, 없을 경우 praw 기본 게시물제한 만큼 요청
        :param date: '20170301:20170305'형태로 받음. 뒤에 날짜까지 포함하여 요청
        :return: praw.Reddit.submissions 객체(Generator)
        """
        if date:
            start_time, end_time = dt.split_date(date)

            print(start_time)
            print(end_time)

            result = self.reddit.subreddit(subreddit).submissions(start_time, end_time)

            if not result:
                raise NotImplementedError

        else:
            result = self.reddit.subreddit(subreddit).new(limit=num)

        return result

    def parse(self, reddit_list):
        """
        praw.Reddit.submissions 객체로 부터 submission 정보 추출
        여기서  정보를 받아오는 시간이 많이 소요됨
        :param reddit_list: praw.Reddit.submissions 객체
        :return: 
        """
        """
        post['id'] 를 post['ID'] 로 수정?"""
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

                    posts.append(post)

            except:
                # 요청중 에러가 발생하면 30초 대기
                print("*" * 50)
                print("error! waiting 30sec")
                print("*" * 50)
                time.sleep(30)
            else:
                break

        return posts


if __name__ == "__main__":
    r = Reddit()

    test = r.list_request('programming', date="20170228:20170228")
    for i in test:
        print(i)
