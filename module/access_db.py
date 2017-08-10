import pymongo

class AccessDB:
    def __init__(self, dbname):
        self.client = pymongo.MongoClient()
        self.db = self.client[dbname]

    def create_collection(self, name):
        try:
            self.db.create_collection(name)
            return True
        except:
            return False

    def insert(self, collection, query):
        """
        para query :: dict
        """
        # query = json.loads(query)
        self.db[collection].insert_one(query)

    def update(self, collection, target, query):

        self.db[collection].update_one(target, query)

    def find(self, query=None, projection=None, collection=None):

        if collection:
            documents = [i for i in self.db[collection].find(query, projection)]

        else:
            documents = []
            for i in self.db.collection_names():
                document = self.db[i].find(query, projection)

                for i in document:
                    documents.append(i)

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
                result = self.inputPost(db, subreddit, post)

            return result

        elif type(posts) is dict:
            result = self.inputPost(db, subreddit, posts)
            return result

        else:
            return result

    def inputPost(self, db, subreddit, post):
        self.DB.useDB(db)

        if 'id' in post:
            id_query = {"ID": post['id']}
        elif 'ID' in post:
            id_query = {"ID": post['ID']}
        else:
            print("has not key(id)")
            return False

        if not self.DB.find(query=id_query, collection=subreddit):
            self.DB.insert(subreddit, id_query)

        for key in post:
            if key is 'id' or key is 'ID':
                continue

            update_query = {'$set': {key: post[key]}}

            self.DB.update(subreddit, id_query, update_query)

        return True

    def findPost(self, db, subreddit=None, query=None):
        self.DB.useDB(db)

        return self.DB.find(query=query, collection=subreddit)