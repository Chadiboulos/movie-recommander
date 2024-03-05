from models import Tag, Rating, Movie
import pandas as pd
from pymongo import MongoClient
from tqdm import tqdm
from datetime import datetime


genome_tags_csv = pd.read_csv("./ml-20m/genome-tags.csv")
genome_score_csv = pd.read_csv("./ml-20m/genome-scores.csv")
tags_csv = pd.read_csv("./ml-20m/tags.csv")
links_imdb_csv = pd.read_csv("./ml-20m/links.csv")
ratings_csv = pd.read_csv("./ml-20m/ratings.csv")
movies_csv = pd.read_csv("./ml-20m/movies.csv")

client = MongoClient(
    "mongodb://reco_films:recommendation_films_oct_23_MLOPS@35.180.118.85:27017")
db = client['Reco_films']

collection_movies = db.Movies
collection_rating = db.Ratings

l_movieid = list()


def load_movie():
    genome_tags_dict = dict(zip(genome_tags_csv.tagId, genome_tags_csv.tag))
    l_movie = list()
    for index, mov_data in tqdm(movies_csv.iterrows()):

        try:
            id_m = mov_data['movieId']
            genres_list = mov_data['genres'].split('|')
            tags_list = list()
            tags_mov_df = tags_csv[tags_csv.movieId == id_m]
            for i, t in tags_mov_df.iterrows():
                date_ = datetime.fromtimestamp(int(t['timestamp']))
                tags_list.append(
                    Tag(
                        userid=t['userId'],
                        tag=t['tag'],
                        date=date_.strftime("%Y-%m-%d %H:%M:%S")
                    )
                )

            genome_score_df = genome_score_csv[genome_score_csv.movieId == id_m]
            genome_score_dict = dict()
            for i, gt in genome_score_df.iterrows():
                genome_score_dict[genome_tags_dict[gt["tagId"]]
                                  ] = gt['relevance']

            imdb_tmdb = links_imdb_csv[links_imdb_csv.movieId == id_m].iloc[0]
            m = Movie(movieid=id_m,
                      title=mov_data["title"],
                      genres=genres_list,
                      genome_scores=genome_score_dict,

                      imdbid=imdb_tmdb["imdbId"],
                      tmdbid=imdb_tmdb["tmdbId"]
                      )
            l_movie.append(m.dict())
            l_movieid.append(id_m)
            if len(l_movie) % 1000 == 0:
                collection_movies.insert_many(l_movie)
                del l_movie
                l_movie = list()
        except Exception:
            print("Error a la ligne: ", index)
    collection_movies.insert_many(l_movie)


def load_rating():
    l_rating = list()
    for index, rat_data in tqdm(ratings_csv.iterrows()):
        id_m = rat_data['movieId']
        if not (id_m in l_movieid):
            continue
        date_ = datetime.fromtimestamp(int(rat_data['timestamp']))
        r = Rating(
            movieid=int(rat_data['movieId']),
            userid=rat_data['userId'],
            rating=rat_data['rating'],
            date=date_
        )
        l_rating.append(r.dict())
        if len(l_rating) % 1000:
            collection_rating.insert_many(l_rating)
            del l_rating
            l_rating = list()

    collection_rating.insert_many(l_rating)


load_movie()
load_rating()

client.close()
# modif_chadi
