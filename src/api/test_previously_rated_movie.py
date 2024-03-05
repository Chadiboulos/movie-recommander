from fastapi.testclient import TestClient
from fastapi import status

from main import app
from utilities import delete_rating_testuser

test_app = TestClient(app)


def test_get_rating_authent():
    """
    Test getting previously rated movies by an authenticated user.

    Steps:
    1. Authenticates with the '/token' endpoint to obtain an access token.
    2. Rates two movies with IDs 1 and 2 using the '/rate_movie/' endpoint.
    3. Asserts that the response status code for rating the movies is 200 (OK).
    4. Gets the previously rated movies using the '/previously_rated_movies/' endpoint.
    5. Asserts that the response status code for getting previously rated movies is 200 (OK).
    6. Asserts that the user has rated 2 movies.
    7. Deletes the rating of movie with ID 1 using the '/delete_rate/{movie_id}' endpoint.
    8. Asserts that the response status code for deleting the rating is 200 (OK).
    9. Gets the previously rated movies again.
    10. Asserts that the user has rated only 1 movie after deleting the rating.

    Note:
    - The user is assumed to be logged in as 'test1' with the password 'testuser'.
    """

    delete_rating_testuser()

    # Step 1
    response = test_app.post('/token',
                             headers={
                                 'accept': 'application/json',
                                 'Content-Type': 'application/x-www-form-urlencoded'},
                             data={'username': 'test1',
                                   'password': 'testuser'
                                   })
    access_token = response.json()["access_token"]
    assert response.status_code == status.HTTP_200_OK

    # Step 2
    response = test_app.post("/rate_movie/",
                             headers={'accept': 'application/json',
                                      'Authorization': 'Bearer ' + access_token,
                                      'Content-Type': 'application/json'
                                      },
                             json={"movie_id": 1,
                                   "rating": 5}
                             )
    response = test_app.post("/rate_movie/",
                             headers={'accept': 'application/json',
                                      'Authorization': 'Bearer ' + access_token,
                                      'Content-Type': 'application/json'
                                      },
                             json={"movie_id": 2,
                                   "rating": 2}
                             )

    # Step 3
    assert response.status_code == status.HTTP_200_OK

    # Step 4
    response = test_app.get("/previously_rated_movies/",
                            headers={'accept': 'application/json',
                                     'Authorization': 'Bearer ' + access_token,
                                     'Content-Type': 'application/json'
                                     }
                            )

    # Step 5
    assert response.status_code == status.HTTP_200_OK

    # Step 6
    rates = response.json()
    assert len(rates) == 2

    # Step 7
    response = test_app.delete('/delete_rate/1',
                               headers={'accept': 'application/json',
                                        'Authorization': 'Bearer ' + access_token,
                                        'Content-Type': 'application/json'
                                        })

    # Step 8
    assert response.status_code == status.HTTP_200_OK

    # Step 9
    response = test_app.get("/previously_rated_movies/",
                            headers={'accept': 'application/json',
                                     'Authorization': 'Bearer ' + access_token,
                                     'Content-Type': 'application/json'
                                     })
    rates = response.json()

    # Step 10
    assert len(rates) == 1


def test_get_rating_unauthent():
    """
    Test attempting to get previously rated movies by an unauthenticated user.

    Steps:
    1. Sends a GET request to the '/previously_rated_movies/' endpoint with an invalid access token.
    2. Asserts that the response status code is 401 (Unauthorized).
    """
    response = test_app.get("/previously_rated_movies/",
                            headers={'accept': 'application/json',
                                     'Authorization': 'Bearer ' + 'Token',
                                     'Content-Type': 'application/json'
                                     })
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
