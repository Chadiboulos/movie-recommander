from fastapi.testclient import TestClient
from main import app
from credentials import db_params
import psycopg2


test_app = TestClient(app)


def test_add_movie_unauthenticated():
    """
    Test adding a movie by an unauthenticated user.

    Steps:
    1. Sends a POST request to add a movie without authentication.
    2. Asserts that the response status code is 401 (Unauthorized).
    3. Asserts that the response JSON contains the expected error message.
    """
    response = test_app.post(
        '/add_movie/',
        headers={
            'accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded'},
        data={
            'title': 'zz',
            'imdbid': 1,
            'tmdbid': 1})
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_add_existing_movie():
    """
    Test adding a movie that already exists in the database.

    Steps:
    1. Retrieves an access token for an existing admin user.
    2. Sends a POST request to add a movie that already exists.
    3. Asserts that the response status code is 422 (Unprocessable Entity).
    4. Asserts that the response JSON contains the expected error message.
    """
    response_token = test_app.post(
        '/token',
        headers={
            'accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded'},
        data={
            'username': 'admin',
            'password': 'admin'})

    access_token = response_token.json()["access_token"]

    response_add_movie = test_app.post(
        "/add_movie/",
        headers={
            'accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + access_token},
        json={
            'title': 'Assassins (1995)',
            'imdbid': 112401,
            'tmdbid': 9691})

    assert response_add_movie.status_code == 422
    assert response_add_movie.json() == {"detail": "Assassins (1995) is already in the database"}


def test_add_new_movie():
    """
    Test adding a new movie by an authenticated admin user.

    Steps:
    1. Retrieves an access token for an existing admin user.
    2. Deletes any test movie from the database (if exists).
    3. Sends a POST request to add a new movie.
    4. Asserts that the response status code is 200 (OK).
    5. Asserts that the response JSON contains the expected success message.
    6. Checks if the new movie has been added to the database.
    """
    response_token = test_app.post(
        '/token',
        headers={
            'accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded'},
        data={
            'username': 'admin',
            'password': 'admin'})

    access_token = response_token.json()["access_token"]

    conn = psycopg2.connect(**db_params)
    cursor = conn.cursor()

    cursor.execute(""" SELECT movieid FROM movie where title = 'zz' """)
    id_movie_zz = cursor.fetchall()

    for id_zz in id_movie_zz:
        cursor.execute("""DELETE FROM imdb_data WHERE movieid = %s""", (id_zz, ))
        cursor.execute("""DELETE FROM movie WHERE movieid = %s""", (id_zz,))

    conn.commit()

    response_add_movie = test_app.post(
        "/add_movie/",
        headers={
            'accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + access_token},
        json={
            'title': 'zz',
            'imdbid': 999990,
            'tmdbid': 999990})

    cursor.execute(""" SELECT * FROM movie WHERE title = 'zz'; """)
    rows = cursor.fetchall()

    assert response_add_movie.status_code == 200
    assert response_add_movie.json() == {"message": "Movie added successfully!!"}
    assert len(rows) > 0
