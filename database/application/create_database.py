import psycopg2
import glob
import numpy as np
import pandas as pd
import os
import re
import datetime
import time
dbname = os.environ.get("POSTGRES_DB")
user = os.environ.get("POSTGRES_USER")
password = os.environ.get("POSTGRES_PASSWORD")
host = os.environ.get("POSTGRES_HOST")
port = int(os.environ.get("POSTGRES_PORT"))
print(datetime.datetime.now())
sql_file = sorted(glob.glob("./sql/*"))

def wait_database_connexion():
    while(True):
        try:
            conn = psycopg2.connect(dbname=dbname, user=user,
                            password=password, host=host, port=port)
            print("Connextion !!!")
            return 0
        except Exception as e:
            print("En attente de connexion")
            time.sleep(5)


def executesql(fichier_sql):
    conn = psycopg2.connect(dbname=dbname, user=user,
                            password=password, host=host, port=port)
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
link = pd.read_csv("./ml-latest-small/links.csv")


movie = movie.merge(link, on="movieId")
movie = movie.replace(np.nan, "")


def get_year(row):
    title = row["title"]
    match = re.search(r'\((\d{4})\)', title)
    year = int(match.group(1)) if match else 0
    return year


def get_decade(row):
    year = int(row["year"])
    return (year//10)*10


movie['year'] = movie.apply(get_year, axis=1)
movie['decade'] = movie.apply(get_decade, axis=1)


def insert_sql_movie(row):
    with psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port) as conn:
        with conn.cursor() as cur:
            insert_query = """INSERT INTO movie (movieid, title, imdbid, tmdbid, year, decade)
            VALUES (%s, %s, %s, %s, %s, %s);
            """

            data_to_insert = (
                int(row["movieId"]),
                row["title"],
                row["imdbId"],
                row["tmdbId"] if row["tmdbId"] else None,
                row["year"],
                row["decade"]
            )
            cur.execute(insert_query, data_to_insert)


def insert_sql_rating(row):
    try:
        # Utilisation de gestionnaires de contexte pour la connexion et le curseur
        with psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port) as conn:
            with conn.cursor() as cur:
                insert_query = """INSERT INTO rating (userid, movieid, rating, timestamp)
                                  VALUES (%s, %s, %s, %s);"""
                data_to_insert = (
                    int(row["userId"]),
                    # Assurez-vous que movieId est également un entier
                    int(row["movieId"]),
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
    with psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port) as conn:
        with conn.cursor() as cur:
            query = """select * from genre;"""
            cur.execute(query=query)
            rows = cur.fetchall()
            movie_genres = pd.DataFrame()
            for row in rows:
                movie_genre = movie[movie['genres'].str.contains(
                    row[1], case=False, na=False)][["movieId"]]
                movie_genre["genreId"] = [row[0]]*len(movie_genre)
                movie_genres = pd.concat((movie_genres, movie_genre), axis=0)
    return movie_genres


def insert_sql_movie_genre(row):
    try:
        with psycopg2.connect(dbname=dbname, user=user, password=password, host=host,port=port) as conn:
            with conn.cursor() as cur:
                insert_query = """INSERT INTO movie_genre ( movieid, genreid)
                                  VALUES (%s, %s);"""
                cur.execute(
                    insert_query, (int(row["movieId"]), int(row['genreId'])))
    except Exception as e:
        print(f"{e}",
            (
                int(row["movieId"]),
                int(row['genreId'])
            )
        )
        return 1
    return 0


def refresh_table_recap_view():
    # Refresh de la vue table_recap_view
    try:
        with psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port) as conn:
            with conn.cursor() as cur:
                refresh_query = """REFRESH MATERIALIZED VIEW table_recap_view;"""
                cur.execute(refresh_query)
    except Exception as e:
        print("Error for refresh Table Recap {e}")

wait_database_connexion()
print("execute_all_sql")
execute_all_sql(sql_file)
print("insert_sql_movie")
movie.apply(insert_sql_movie, axis=1)
print("insert_sql_rating")
rating.apply(insert_sql_rating, axis=1)
movie_genres = create_movie_genre_df()
print("insert_sql_movie_genre")
movie_genres.apply(insert_sql_movie_genre, axis=1)
print("refresh_table_recap_view")
refresh_table_recap_view()
print(datetime.datetime.now())