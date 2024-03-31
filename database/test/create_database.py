import psycopg2
import glob
import numpy as np
import pandas as pd
dbname = 'movieflix_db'
user = 'movieflix'
password = 'movieflix'
host = 'localhost'

dbname = 'postgres'
user = 'postgres'
password = 'recommendation_films_oct_23_MLOPS'
host = 'reco-films-db.ck2uuvj8tg5b.eu-west-3.rds.amazonaws.com'

sql_file = sorted(glob.glob("./sql/*"))

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

for file in sql_file:
        print(file)
        executesql(file)



rating = pd.read_csv("./ml-latest-small/ratings.csv")
movie = pd.read_csv("./ml-latest-small/movies.csv")
link= pd.read_csv("./ml-latest-small/links.csv")



movie=movie.merge(link,on="movieId")
movie=movie.replace(np.nan,"")

movie[ movie['movieId']==791 ]

def insert_sql_movie(row):
    conn = psycopg2.connect(dbname=dbname, user=user, password=password, host=host)
    # Créer un objet cursor
    cur = conn.cursor()
    insert_query = """INSERT INTO movie (	movieid, title, imdbid,tmdbid)
    VALUES (%s, %s,%s,%s);
    """
    data_to_insert = (int(row["movieId"]),row["title"], row["imdbId"],row["tmdbId"] if row["tmdbId"] else None)
    cur.execute(insert_query, data_to_insert)
    conn.commit()
    cur.close()
    conn.close()
    return

def insert_sql_rating(row):
    conn = psycopg2.connect(dbname=dbname, user=user, password=password, host=host)
    # Créer un objet cursor
    cur = conn.cursor()
    insert_query = """INSERT INTO rating (	userid, movieid,rating	,timestamp)
    VALUES (%s, %s,%s,%s);
    """
    data_to_insert = (int(row["userId"]),row["movieId"], row["rating"],row["timestamp"])
    cur.execute(insert_query, data_to_insert)
    conn.commit()
    cur.close()
    conn.close()
    return

movie.apply(insert_sql_movie,axis=1)

rating.apply(insert_sql_rating,axis=1)

