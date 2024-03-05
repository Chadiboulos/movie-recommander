from fuzzywuzzy import fuzz, process
from utilities import (fetch_ratings_from_db,
                       fetch_movie_titles,
                       get_unrated_movies,
                       fetch_top_movies_from_db,
                       fetch_movie_titles_from_db,
                       delete_rating,
                       get_user_rate,
                       movie_details)
from authentication import (Token,
                            Rating,
                            Suggestion,
                            Movie,
                            verify_password,
                            create_access_token,
                            get_current_user,
                            get_username
                            )
import psycopg2
import pickle
from fastapi import FastAPI, Query, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from welcome import welcome
import time
from datetime import timedelta, datetime
from credentials import (ACCESS_TOKEN_EXPIRATION, db_params, pwd_context)
import os
from prometheus_fastapi_instrumentator import Instrumentator
from mlflow_model import load_mlflow_model


# Fetching environment variable for environment information
ENV = os.environ.get("ENV", "")
sha_id = os.environ.get('TAG', "")

# Initializing Prometheus Instrumentator


# Initializing FastAPI app with title, description, version, and tags
app = FastAPI(title="Movie Recommender"+" - "+ENV,
              description=f"Interface to get \
              recommendations about best rated movies. - version:{sha_id}",
              version="1.0.1", openapi_tags=[{
                  'name': 'Authentication',
                  'description': 'Token related endpoints'
              },
                  {
                  'name': 'API Status',
                  'description': 'Checks the status of the API'
              },
                  {
                  'name': 'Recommending',
                  'description': 'Get recommendations'
              },
                  {
                  'name': 'Rating Movies',
                  'description': 'Rate movies of your choice'
              },
                  {
                  'name': 'Search',
                  'description': 'Search a movie'
              },
                  {
                  'name': 'Administration',
                  'description': 'Admin related tasks'
              },])
instrumentator = Instrumentator().instrument(app)


@app.on_event("startup")
async def _startup():
    instrumentator.expose(app)

# Function to load the recommendation model


def load_model():
    try:
        model = load_mlflow_model()
        return model
    except Exception as e:
        print(f"Probleme de chargement du modèle mlflow:{e}")

    dir_path = os.path.dirname(__file__)
    with open(os.path.join(dir_path, "svd_model.pkl"), "rb") as f:
        model = pickle.load(f)
    return model


# Loading the recommendation model and necessary data
model = load_model()
ratings_df = fetch_ratings_from_db()
movies_df = fetch_movie_titles_from_db()
movies_df_cleaned = movies_df.assign(
    title=movies_df['title'].str.lower().str.replace(r'[^a-zA-Z ]',
                                                     '',
                                                     regex=True))

title_to_movieid = dict(zip(movies_df_cleaned['title'],
                            movies_df['movieid']))
cleaned_to_initial_title = dict(
    zip(movies_df_cleaned['title'],
        movies_df['title']))

model = load_model()


# Route for the home status page with welcome message
@app.get("/", tags=['API Status'], response_class=HTMLResponse)
# @app.get("/", tags=['API Status'], response_class=HTMLResponse)
def get_welcome():
    """
    Returns welcome message if API is functional
    """
    return welcome


# Route for checking API status
@app.get("/status", tags=['API Status'])
def get_api_status():
    """
    Returns ok if API is functional
    """
    return {"status": "OK",
            "version":sha_id}


# Route for generating access token
@app.post("/token", response_model=Token, tags=['Authentication'])
async def access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Generates a token for clients
    """
    try:
        user = get_username(form_data.username)
    except ValueError:
        raise HTTPException(status_code=400,
                            detail="Incorrect username or password")
    # user = users_db.get(form_data.username)
    hashed_password = user.get("hashed_password")
    user_id = user.get("user_id")
    if not user or not verify_password(form_data.password, hashed_password):
        raise HTTPException(status_code=400,
                            detail="Incorrect username or password")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRATION)
    access_token = create_access_token(data={"sub": form_data.username},
                                       expires_delta=access_token_expires)
    # ACCESS_TOKEN = access_token
    return {"access_token": access_token,
            "token_type": "bearer",
            "user_id": user_id}


# Route for getting personalized recommendations for authenticated clients
@app.get("/client_recommendation/", tags=['Recommending'])
async def get_recommendations(current_user: tuple = Depends(get_current_user)):
    """
    Generates personalized recommandations for authenticated clients
    """
    _, userid, _ = current_user
    try:

        unrated_movie_ids = get_unrated_movies(ratings_df, userid)

        # Predict ratings for unrated movies
        recommendations = []
        for movieid in unrated_movie_ids:
            predicted_rating = model.predict(userid, movieid).est
            recommendations.append((movieid, predicted_rating))

        # Sort recommendations by predicted ratings (descending order)
        recommendations.sort(key=lambda x: x[1], reverse=True)

        # Get top 10 recommendations
        top_recommendations = recommendations[:10]

        # Fetch movie titles for top recommendations
        top_movie_ids = [movieid for movieid, _ in top_recommendations]
        movie_titles = fetch_movie_titles(top_movie_ids)
        final_recommendations = []
        for movieid, rating in top_recommendations:
            if movieid in movie_titles:
                final_recommendations.append({"title": movie_titles[movieid],
                                              "predicted_rating": rating,
                                              "movieid": int(movieid)})

        # Return top 10 recommendations with movie titles
        return {
            "user_id": userid,
            "recommendations": final_recommendations
        }
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Error generating recommendations: {e}")


# Route for searching movies by title
@app.get("/movie_id_search/", tags=['Rating Movies', 'Search'])
def get_movie_id(search_query: str = Query(..., min_length=5)):
    processed_query = search_query.lower().replace('[^a-zA-Z ]', '')

    # Using fuzzywuzzy to find matches
    matches = process.extract(
        processed_query,
        movies_df_cleaned['title'],
        limit=10,
        scorer=fuzz.partial_ratio)

    # Finding corresponding movie_ids for the top matches
    top_matches = [{"movieid": title_to_movieid[match[0]],
                    "title": cleaned_to_initial_title[match[0]],
                    "score": match[1]} for match in matches]

    return top_matches


# Route for rating a movie
@app.post("/rate_movie/", tags=['Rating Movies'])
def rate_movie_based_on_its_id(rating: Rating, current_user: tuple = Depends(get_current_user)):
    """
    Endpoint to rate a movie
    """
    # Generate Unix timestamp
    timestamp = int(time.time())
    conn = psycopg2.connect(**db_params)
    cursor = conn.cursor()
    _, user_id, _ = current_user
    query_insert = """
            INSERT INTO rating (userid,
                                movieid,
                                rating,
                                timestamp)
            VALUES (%s, %s, %s, %s);
        """
    query_update = """
            UPDATE rating
            SET rating = %s, timestamp = %s
            WHERE movieid = %s
            AND userid = %s ;
        """
    query_verif = """
            SELECT *
            FROM rating
            WHERE movieid = %s
            AND userid = %s ;
        """

    try:
        cursor.execute(query_verif, (rating.movie_id, user_id))
        movie_rated = cursor.fetchall()
        if movie_rated:
            cursor.execute(query_update,
                           (rating.rating,
                            timestamp,
                            rating.movie_id,
                            user_id))
        else:
            cursor.execute(query_insert,
                           (user_id,
                            rating.movie_id,
                            rating.rating,
                            timestamp))
        conn.commit()
        cursor.close()

        return {"message": "Rating added successfully!",
                "timestamp": timestamp}
    except Exception as e:
        # Rollback the transaction if an error occurs
        conn.rollback()
        cursor.close()
        raise HTTPException(status_code=400,
                            detail=f"Error rating the movie: {e}")


# Route for getting previously rated movies by a user
@app.get("/previously_rated_movies/", tags=['Rating Movies'])
async def get_rated_movies(current_user: tuple = Depends(get_current_user)):
    """
    Get all rated movies by
    """
    _, userid, _ = current_user
    data = [{"movieid": rating[0],
             "rating": rating[1],
             "date": str(datetime.fromtimestamp(rating[2]))
             } for rating in get_user_rate(userid)]

    return data


# Route for getting top movies for general recommendations
@app.post("/prospect_suggestion/", tags=['Recommending', 'Search'])
async def get_top_movies(suggestion: Suggestion):
    """
    Get general recommandations (doesn't require authentication)
    """
    top_movies = fetch_top_movies_from_db(suggestion)
    return {"top_movies": top_movies}


# Route for deleting a rating
@app.delete("/delete_rate/{movieid}", tags=['Rating Movies'])
def delete_rate(movieid: int, current_user: tuple = Depends(get_current_user)):

    _, userid, _ = current_user
    delete_rating(userid, movieid)

    return {"ok": True}


# Route for adding admin users
@app.post("/add_admins/", tags=['Administration'])
async def add_admin_users(user: str = Form(...), password: str = Form(...), current_user: tuple = Depends(get_current_user)):
    _, _, is_admin = current_user
    if not is_admin:
        raise HTTPException(
            status_code=401,
            detail="Admin rights required"
        )
    conn = psycopg2.connect(**db_params)
    cursor = conn.cursor()

    query_get_db = """
            SELECT *
            FROM users;
        """
    query_insert_db = """
            INSERT INTO users (username,
                                password,
                                is_admin
                                )
            VALUES (%s, %s, %s);
        """

    cursor.execute(query_get_db)

    query_verif = """
            SELECT 1
            FROM users
            WHERE username = %s ;
        """

    admin_password = password
    admin_password_hash = pwd_context.hash(admin_password)

    try:
        cursor.execute(query_verif, (user, ))
        username_exists = cursor.fetchall()
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=400,
                            detail=f"Error connecting to database: {e}")

    if len(username_exists) > 0:
        raise HTTPException(status_code=400,
                            detail="user already exists in database")
    cursor.execute(query_insert_db, (user, admin_password_hash, 'true'))
    conn.commit()
    cursor.close()
    return {"message": "User added successfully!"}


# Route for adding a movie
@app.post("/add_movie/", tags=['Administration'])
def add_movie(movie: Movie, current_user: tuple = Depends(get_current_user)):
    _, _, is_admin = current_user
    if not is_admin:
        raise HTTPException(
            status_code=401,
            detail="Admin rights required"
        )
    conn = psycopg2.connect(**db_params)
    cursor = conn.cursor()
    query_max = """
        SELECT MAX(movieid)
        FROM movie;
        """
    query_verif = """
            SELECT *
            FROM movie
            WHERE title = %s ;
        """
    query_insert = """
            INSERT INTO movie (movieid,
                                title,
                                imdbid,
                                tmdbid)
            VALUES (%s, %s, %s, %s);
        """

    cursor.execute(query_max)
    movieid_max_db = cursor.fetchall()
    movieid_max = movieid_max_db[0][0]

    try:
        cursor.execute(query_verif, (movie.title,))
        movie_exists = cursor.fetchall()
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=400,
                            detail=f"Error adding new movie to database: {e}")
    if movie_exists:
        raise HTTPException(status_code=422,
                            detail=f"{movie.title} is already in the database")
    else:
        cursor.execute(query_insert, (movieid_max + 1,
                       movie.title, movie.imdbid, movie.tmdbid))
        conn.commit()
    cursor.close()
    return {"message": "Movie added successfully!"}


# Route for getting details of a movie by its ID
@app.get("/movie_details/{movieid}", tags=['Search'])
def get_movie_details(movieid: int):
    return movie_details(movieid)
