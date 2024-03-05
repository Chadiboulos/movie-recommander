from pymongo import MongoClient

client = MongoClient(
    "mongodb://reco_films:recommendation_films_oct_23_MLOPS@35.180.118.85:27017", 27017)
db = client['Reco_films']
collection_movies = db.Movies

userid_selected = 1
genre_selected = 'Adventure'
userid = 1


adventure_movies_userid1 = collection_movies.aggregate([
    {
        '$match': {
            'ratings.userid': userid
        }
    },
    {
        '$project': {
            '_id': 0,
            "title": 1,
            "movieid": 1,
            "genres": 1,
            "genome_scores": 1,
            'ratings': {
                '$filter': {
                    'input': '$ratings',
                    'as': 'rating',
                    'cond': {'$eq': ['$$rating.userid', userid]}
                }
            }
        }
    },
    {
        '$match': {
            'ratings.rating': {'$eq': 5}
        }
    }

]
)

for movie in adventure_movies_userid1:
    print(movie)
