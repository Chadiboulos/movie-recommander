import psycopg2
import glob
import pandas as pd
import numpy as np
import re

# Remplacez ces valeurs par vos informations de connexion
dbname = 'postgres'
user = 'postgres'
password = 'recommendation_films_oct_23_MLOPS'
host = 'localhost'

sql_file = sorted(glob.glob("./database/test/sql/*"))

movie_to_keep = [1,2,23]

def executesql(fichier_sql):
    conn = psycopg2.connect(dbname=dbname, user=user, password=password, host=host)
    # Créer un objet cursor
    cur = conn.cursor()

    # Ouvrir le fichier SQL et exécuter son contenu
    with open(fichier_sql, 'r') as file:
        # Divise le script en commandes séparées par ';'
        sql_script = file.read()
        commands = sql_script.split(';')

        # Exécute chaque commande individuellement
        for command in commands:
            if command.strip() != '':  # Vérifie si la commande n'est pas vide
                    print(command)
                    cur.execute(command)
                    conn.commit()
    # Fermer la communication avec la base de données
    conn.commit()
    cur.close()
    conn.close()
def execute_all_sql(sql_file):
    for file in sql_file:
            print(file)
            executesql(file)



rating = pd.read_csv("./ml-latest-small/ratings.csv")
movie = pd.read_csv("./ml-latest-small/movies.csv")
link= pd.read_csv("./ml-latest-small/links.csv")



movie=movie.merge(link,on="movieId")
movie=movie.replace(np.nan,"")

def get_year(row):
    title = row["title"]
    match = re.search(r'\((\d{4})\)', title)
    year = int(match.group(1)) if match else 0
    return year
def get_decade(row):
    year = int(row["year"])
    return (year//10)*10

movie['year'] = movie.apply(get_year,axis=1)
movie['decade'] = movie.apply(get_decade,axis=1)


movie = movie[movie['decade'] == 1990 ].head(30)


rating = rating[ rating.movieId.isin( movie.movieId)]

import re

def insert_sql_movie(row):
    with psycopg2.connect(dbname=dbname, user=user, password=password, host=host) as conn:
        with conn.cursor() as cur:
            insert_query = """INSERT INTO movie (movieid, title, imdbid, tmdbid, year, decade)
            VALUES (%s, %s, %s, %s, %s, %s);
            """
            title = row["title"]
            match = re.search(r'\((\d{4})\)', title)
            year = int(match.group(1)) if match else None
            decade = (year // 10) * 10 if year else None

            # It's a good idea to check if year is None before proceeding
            if year is None:
                # Handle the case where the year couldn't be extracted
                print(f"Year could not be extracted for title: {title}")
                return

            data_to_insert = (
                int(row["movieId"]),
                row["title"],
                row["imdbId"],
                row["tmdbId"] if row["tmdbId"] else None,
                year,
                decade
            )
            cur.execute(insert_query, data_to_insert)

def insert_sql_rating(row):
    try:
        # Utilisation de gestionnaires de contexte pour la connexion et le curseur
        with psycopg2.connect(dbname=dbname, user=user, password=password, host=host) as conn:
            with conn.cursor() as cur:
                insert_query = """INSERT INTO rating (userid, movieid, rating, timestamp)
                                  VALUES (%s, %s, %s, %s);"""
                data_to_insert = (
                    int(row["userId"]),
                    int(row["movieId"]),  # Assurez-vous que movieId est également un entier
                    row["rating"],
                    row["timestamp"]
                )
                cur.execute(insert_query, data_to_insert)
    except Exception as e:
        # Gestion des erreurs en affichant un message d'erreur
        print(f"An error occurred: {e}")
        return 1
    return 0



def create_movie_genre_df():
    with psycopg2.connect(dbname=dbname, user=user, password=password, host=host) as conn:
        with conn.cursor() as cur:
            query = """select * from genre;"""
            cur.execute(query=query)
            rows = cur.fetchall()
            movie_genres = pd.DataFrame()
            for row in rows:
                movie_genre = movie[ movie['genres'].str.contains(row[1], case=False, na=False)][["movieId"]]
                movie_genre["genreId"]=[row[0]]*len(movie_genre)
                movie_genres=pd.concat((movie_genres,movie_genre),axis=0)
    return movie_genres
    


def insert_sql_movie_genre(row):
    try:
        with psycopg2.connect(dbname=dbname, user=user, password=password, host=host) as conn:
            with conn.cursor() as cur:
                insert_query = """INSERT INTO movie_genre ( movieid, genreid)
                                  VALUES (%s, %s);"""
                cur.execute(insert_query,(int(row["movieId"]),int(row['genreId'])))
    except Exception:
        print(
              (
               int(row["movieId"]),
               int(row['genreId'])
               )
              )
        return 1
    return 0

def refresh_table_recap_view():
    #Refresh de la vue table_recap_view
    try:
        with psycopg2.connect(dbname=dbname, user=user, password=password, host=host) as conn:
            with conn.cursor() as cur:
                refresh_query = """REFRESH MATERIALIZED VIEW table_recap_view;"""
                cur.execute(refresh_query)
    except Exception as e:
        print("Error for refresh Table Recap {e}")
def insert_fake_imdb_data(movie):
    for movieid in set(movie["movieId"]):
        try:
            with psycopg2.connect(dbname=dbname, user=user, password=password, host=host) as conn:
                with conn.cursor() as cur:
                    refresh_query = f"""INSERT INTO imdb_data
                                    (movieid, titre, summary, certificat, duration, poster, directors, writers, stars)
                                    VALUES({movieid}, '', '', '', '', '', '', '', '');"""
                    cur.execute(refresh_query)
        except Exception as e:
            print("Error for refresh Table Recap {e}")

execute_all_sql(sql_file)
movie.apply(insert_sql_movie,axis=1)
rating.apply(insert_sql_rating,axis=1)
movie_genres = create_movie_genre_df()
movie_genres.apply(insert_sql_movie_genre,axis=1)
refresh_table_recap_view()
insert_fake_imdb_data(movie)

