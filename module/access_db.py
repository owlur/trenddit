import pymongo


class AccessDB:
    def __init__(self, dbname = None):
        self.client = pymongo.MongoClient('localhost',27017)

        if dbname:
            self.db = self.client[dbname]

    def use_db(self, dbname):
        self.db = self.client[dbname]

    def create_collection(self, name):
        self.db.create_collection(name)
        return True

    def insert(self, collection, query):
        """
        para query :: dict
        """
        # query = json.loads(query)
        self.db[collection].insert_one(query)

    def update(self, collection, target, query):

        self.db[collection].update_one(target, query)

    def find(self, query=None, projection={}, collection=None):
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


class ControlData:
    def __init__(self, db):
        """
        parameter db is instance of AccessDB()
        """
        self.DB = db

    def input_posts(self, db, subreddit, posts):

        result = False

        if type(posts) is list:
            for post in posts:
                result = self.input_post(db, subreddit, post)

            return result

        elif type(posts) is dict:
            result = self.input_post(db, subreddit, posts)
            return result

        else:
            return result

    def input_post(self, db, subreddit, post):
        self.DB.use_db(db)

        if 'id' in post:
            id_query = {"id": post['id']}
            post.pop('id')
        else:
            print("has not key(id)")
            return False

        if not self.DB.find(query=id_query, collection=subreddit):
            self.DB.insert(subreddit, id_query)

        update_query = {'$set': post}

        self.DB.update(subreddit, id_query, update_query)

        return True

    def find_post(self, db, subreddit=None, query=None):
        self.DB.use_db(db)

        return self.DB.find(query=query, collection=subreddit)


if __name__ == '__main__':
    a = AccessDB('reddit')
    b = a.find()
    print(b)