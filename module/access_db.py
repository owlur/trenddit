import pymongo


class AccessDB:
    def __init__(self, dbname = None):
        """
        MongoDB에 직접 접근
        :param dbname: 사용할 DB이름
        """
        self.client = pymongo.MongoClient('localhost',27017)

        if dbname:
            self.db = self.client[dbname]

    def use_db(self, dbname):
        """
        사용할 DB변경
        :param dbname: 사용할 DB이름
        """
        self.db = self.client[dbname]

    def create_collection(self, name):
        """
        collection 생성
        :param name: 생성할 collection 이름
        :return:
        """
        self.db.create_collection(name)
        return True

    def insert(self, collection, query):
        """
        insert 수행
        :param collection: insert할 collection
        :param query: MongoDB 쿼리
        """
        self.db[collection].insert_one(query)

    def update(self, collection, target, query):
        """
        update 수행
        :param collection: update할 collection
        :param target: update할 target
        :param query: update할 쿼리
        """
        self.db[collection].update_one(target, query)

    def find(self, query=None, projection={}, collection=None):
        """
        find 수행
        오브젝트ID는 반환하지 않음
        :param query:
        :param projection:
        :param collection:
        :return: list
        """
        projection['_id'] = 0

        if collection:
            documents = [i for i in self.db[collection].find(query, projection)]

        else:
            documents = []
            for i in self.db.collection_names():
                document = self.db[i].find(query, projection)

                for j in document:
                    documents.append(j)

        return documents


class RedditDB(AccessDB):
    def __init__(self):
        AccessDB.__init__(self, 'reddit')

    def input_posts(self, subreddit, posts):
        result = False

        if type(posts) is list:
            for post in posts:
                result = self.input_post(subreddit, post)

        elif type(posts) is dict:
            result = self.input_post(subreddit, posts)

        return result

    def input_post(self, subreddit, post):
        if 'id' in post:
            id_query = {"id": post['id']}
            post.pop('id')
        else:
            print("has not key(id)")
            return False

        if not self.find(query=id_query, collection=subreddit):
            self.insert(subreddit, id_query)

        update_query = {'$set': post}

        self.update(subreddit, id_query, update_query)

        return True

    def find_post(self, subreddit=None, query=None):
        return self.find(query=query, collection=subreddit)


if __name__ == '__main__':
    a = AccessDB('reddit')
    b = a.find()
    print(b)