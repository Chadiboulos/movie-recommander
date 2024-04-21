import psycopg2
from credentials import db_params
import pandas as pd
from authentication import Suggestion


def fetch_ratings_from_db():
    """
    Retrieves rating data from the 'rating' table in the database, limiting the result to 100,000 rows.
    The function establishes a connection to the database using the parameters provided in 'db_params',
    executes a SQL query to retrieve the data, and returns it as a pandas DataFrame.

    Returns:
        pandas.DataFrame: A DataFrame containing rating data with columns 'userid', 'movieid', and 'rating'.
    """
    try:
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()
        query = "SELECT userid, movieid, rating FROM rating LIMIT 100000"
        cursor.execute(query)
        rows = cursor.fetchall()
        columns = ['userid', 'movieid', 'rating']
        df = pd.DataFrame(rows, columns=columns)
        return df
    except Exception as e:
        print(f"Error fetching data from database: {e}")
    finally:
        cursor.close()
        conn.close()


def get_user_rate(userid: int, movieid: int = None):
    """
    Retrieves rating data for a specific user from the 'rating' table in the database.
    If 'movieid' is provided, it filters ratings for a specific movie for the user.

    Returns:
        list of tuples: A list of tuples containing (movieid, rating, timestamp) for the specified user.
        Each tuple represents a rating entry in the database.
    """
    select_query = """select movieid,rating,timestamp
                      from rating
                      where  userid = %s """
    conn = psycopg2.connect(**db_params)
    cursor = conn.cursor()
    params = [userid]
    if movieid:
        select_query += 'and movieid = %s ;'
        params.append(movieid)
    cursor.execute(select_query, params)
    rows = cursor.fetchall()
    return list(rows)


def fetch_movie_titles(movie_ids):
    """
    Retrieves titles for movies corresponding to the provided movie IDs from the 'movie' table in the database.

    Returns:
        dict: A dictionary where keys are movie IDs and values are corresponding movie titles.
    """
    conn = psycopg2.connect(**db_params)
    cursor = conn.cursor()
    # Convert movie_ids to a tuple for the SQL query
    movie_ids_tuple = tuple(movie_ids)
    try:
        query = f"""SELECT movieid, title
                    FROM movie
                    WHERE movieid IN {movie_ids_tuple}"""
        cursor.execute(query)
        rows = cursor.fetchall()
        movie_titles = {movieid: title for movieid, title in rows}
        return movie_titles
    except Exception as e:
        print(f"Error fetching movie titles: {e}")
    finally:
        cursor.close()
        conn.close()


def fetch_movie_titles_from_db():
    """
    Connects to the PostgreSQL database using the provided connection parameters in 'db_params'.
    Executes a query to select movie IDs and titles from the 'movie' table.
    Converts the fetched data into a pandas DataFrame.

    Returns:
        pandas.DataFrame: A DataFrame containing movie IDs and titles.
    """
    try:
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()
        query = "SELECT movieid, title FROM movie"
        cursor.execute(query)
        rows = cursor.fetchall()
        columns = ['movieid', 'title']
        df = pd.DataFrame(rows, columns=columns)
        return df
    except Exception as e:
        print(f"Error fetching data from database: {e}")
    finally:
        cursor.close()
        conn.close()


def get_unrated_movies(rating_df, userid):
    """
    Retrieves the IDs of movies not yet rated by a user.

    Returns:
        set: A set containing the IDs of movies that the user with the specified ID has not yet rated.
    """

    all_movie_ids = set(rating_df['movieid'].unique())
    rated_movie_ids = set(rating_df[rating_df['userid'] == userid]['movieid'])
    unrated_movie_ids = all_movie_ids - rated_movie_ids
    return unrated_movie_ids


def add_year_column(db_params):
    """
    Adds a 'year' column to the 'movie' table and populates it with the release year parsed from movie titles.
    """

    try:
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()

        add_column_query = "ALTER TABLE movie ADD COLUMN year INTEGER;"
        cursor.execute(add_column_query)
        conn.commit()

        update_query = """
            UPDATE movie
            SET year = CAST(SUBSTRING(title FROM '\\((\\d{4})\\)') AS INTEGER)
            WHERE title ~ '\\((\\d{4})\\)';
        """
        cursor.execute(update_query)
        conn.commit()

        print("Year column updated successfully!")

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def remove_movies_with_null_year(db_params):
    """
    Removes rows from the 'movie' table where the 'year' column is NULL.
    """

    try:
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()
        delete_query = "DELETE FROM movie WHERE year IS NULL;"
        cursor.execute(delete_query)
        conn.commit()
        print("Rows with NULL year values deleted successfully!")

    except Exception as e:
        print(f"An error occurred while deleting rows: {e}")

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def check_rating_table(db_params):
    """
    Checks the 'rating' table in the database by fetching the first 10 rows.
    """

    try:
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()
        check_query = "SELECT * FROM rating LIMIT 10;"
        cursor.execute(check_query)
        rows = cursor.fetchall()
        for row in rows:
            print(row)

    except Exception as e:
        print(f"An error occurred while checking table rating: {e}")

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def fetch_top_movies_from_db(filters: Suggestion):
    """
    Fetches top-rated movies from the database based on provided filters.

    Returns:
    - list: A list of dictionaries, each representing a movie with its attributes.
            Each dictionary contains the following keys:
            - title: Title of the movie.
            - Average rating: Average rating of the movie rounded to two decimal places.
            - number of scores: Number of scores given to the movie, formatted with thousands separator.
            - genre: Genre(s) of the movie.
            - summary: Summary or plot of the movie.
            - duration: Duration of the movie in minutes.
            - stars: Lead actors or actresses of the movie.
            - directors: Director(s) of the movie.
            - certificat: Certification or rating of the movie.
            - writers: Writer(s) of the movie.
            - poster: URL or path to the movie poster.
            - movieid: Unique identifier for the movie.
    """

    try:
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()

        query = """SELECT table_recap_view.title,
                   table_recap_view.avg_rating,
                   table_recap_view.nb_rating,
                   table_recap_view.genre,
                   imdb_data.summary,
                   imdb_data.duration,
                   imdb_data.stars,
                   imdb_data.directors,
                   imdb_data.certificat,
                   imdb_data.writers,
                   imdb_data.poster,
                   table_recap_view.movieid
                   FROM table_recap_view JOIN imdb_data
                   ON imdb_data.movieid = table_recap_view.movieid
                   WHERE 1=1"""

        params = []

        filter_names_value = ['genre',  'decade', 'duration',
                              'stars', 'directors', 'certificate', 'writers']

        for filter_name in filter_names_value:
            filter_value = getattr(filters, filter_name, None)
            if filter_value:
                if filter_name in ['genre', 'stars', 'directors', 'writers']:
                    user_values = filter_value.split("|")
                    or_conditions = []

                    for value in user_values:
                        or_conditions.append(
                            f"lower( {filter_name} ) LIKE lower( %s )")
                        params.append(f"%{value}%")

                    query += " AND (" + " OR ".join(or_conditions) + ")"
                else:
                    query += f" AND {filter_name} = %s"
                    params.append(filter_value)

        min_year = getattr(filters, 'start_year', None)
        max_year = getattr(filters, 'end_year', None)
        if min_year is not None or max_year is not None:
            if min_year is not None:
                query += " AND year >= %s"
                params.append(min_year)
            if max_year is not None:
                query += " AND year <= %s"
                params.append(max_year)

        min_duration = getattr(filters, 'min_duration', None)
        max_duration = getattr(filters, 'max_duration', None)
        if min_duration is not None or max_duration is not None:
            if min_duration is not None:
                query += " AND duration >= %s"
                params.append(min_duration)
            if max_duration is not None:
                query += " AND duration <= %s"
                params.append(max_duration)

        query += " ORDER BY avg_rating DESC LIMIT 20"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        results = [{"title": row[0],
                    "Average rating": round(row[1], 2),
                    "number of scores": f"{row[2]:,}",
                    "genre": row[3],
                    "summary": row[4],
                    "duration": row[5],
                    "stars": row[6],
                    "directors": row[7],
                    "certificat": row[8],
                    "writers": row[9],
                    "poster": row[10],
                    "movieid": row[11]} for row in rows]

        return results

    except Exception as e:
        print(f"An error occurred while fetching top movies: {e}")
        return []

    finally:
        if cursor:
            cursor.close()
        if conn:

            conn.close()


def delete_rating(userid: int, movieid: int):
    """
    Deletes a rating record for a specific user and movie from the database.
    """
    conn = psycopg2.connect(**db_params)
    cursor = conn.cursor()
    delete_query = """delete from rating
                where  userid = %s
                and movieid = %s;
                """
    cursor.execute(delete_query, (userid, movieid))
    conn.commit()
    cursor.close()
    conn.close()


def delete_rating_testuser():
    """
    Delete the rating for the test user.
    """

    query = """delete from rating
                    where userid = 999999 ; """
    conn = psycopg2.connect(**db_params)
    cursor = conn.cursor()
    cursor.execute(query)
    conn.commit()
    cursor.close()
    conn.close()


def movie_details(movieid: int):
    """
    Fetches details of a movie from the database based on the provided movie ID.

    Returns:
    - dict: A dictionary containing details of the movie. Keys represent attributes such as title, average rating,
            number of ratings, genre, summary, duration, stars, directors, certificate, writers, and poster.
    """
    try:
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()

        query = """SELECT movie.title ,
                   table_recap_view.avg_rating,
                   table_recap_view.nb_rating,
                   table_recap_view.genre,
                   imdb_data.summary,
                   imdb_data.duration,
                   imdb_data.stars,
                   imdb_data.directors,
                   imdb_data.certificat,
                   imdb_data.writers,
                   imdb_data.poster
                   FROM table_recap_view left outer JOIN imdb_data
                   ON imdb_data.movieid = table_recap_view.movieid
                   right outer join movie on movie.movieid = table_recap_view.movieid
                   WHERE movie.movieid=%s"""
        cursor.execute(query, [movieid])
        rows = cursor.fetchall()
        row = rows[0]
    except Exception as e:
        print(f"An error occurred while fetching the movie: {e}")
    if len(rows) == 0:
        return []
    movie_details = [(desc[0], row[i])
                     for i, desc in enumerate(cursor.description)]
    movie_details.insert(0, ("movieid", movieid))
    return dict(movie_details)
