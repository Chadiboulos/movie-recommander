from fastapi.testclient import TestClient
from fastapi import status
from main import app
from utilities import (get_user_rate,
                       delete_rating_testuser)
test_app = TestClient(app)


def test_rating_authent():
    """
    Test rating functionality for authenticated users.

    Steps:
    1. Authenticate with the '/token' endpoint to obtain an access token.
    2. Rate a movie with ID 1 with a rating of 5.
    3. Verify that the rating was successfully added.
    4. Rate the same movie again with a different rating of 2.
    5. Verify that the rating was updated successfully.
    6. Attempt to rate the same movie with an invalid rating (6), which should fail with a 422 status code.
    7. Delete the rating for the movie.
    8. Verify that the rating was deleted successfully.
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

    # Step 3
    assert response.status_code == status.HTTP_200_OK

    rates = get_user_rate("999999", 1)
    assert len(rates) == 1

    movieid, rating, _ = rates[0]
    assert movieid == 1 and rating == 5

    # Step 4
    response = test_app.post("/rate_movie/",
                             headers={'accept': 'application/json',
                                      'Authorization': 'Bearer ' + access_token,
                                      'Content-Type': 'application/json'
                                      },
                             json={"movie_id": 1,
                                   "rating": 2}
                             )

    # Step 5
    assert response.status_code == status.HTTP_200_OK
    rates = get_user_rate("999999", 1)
    assert len(rates) == 1
    movieid, rating, _ = rates[0]
    assert movieid == 1 and rating == 2

    # Step 6
    response = test_app.post("/rate_movie/",
                             headers={'accept': 'application/json',
                                      'Authorization': 'Bearer ' + access_token,
                                      'Content-Type': 'application/json'
                                      },
                             json={"movie_id": 1,
                                   "rating": 6}
                             )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Step 7
    response = test_app.delete('/delete_rate/1', headers={'accept': 'application/json',
                                                          'Authorization': 'Bearer ' + access_token,
                                                          'Content-Type': 'application/json'
                                                          })

    # Step 8
    assert response.status_code == status.HTTP_200_OK
    assert len(get_user_rate("999999")) == 0


def test_rating_unauthent():
    """
    Test rating functionality for unauthenticated users.

    Steps:
    1. Attempt to rate a movie without providing authentication.
    2. Verify that the request fails with a 401 Unauthorized status code.
    """
    response = test_app.post("/rate_movie/", headers={'accept': 'application/json',
                                                      'Authorization': 'Bearer ' + "tokenfaux",
                                                      'Content-Type': 'application/json'
                                                      },
                             json={"movie_id": 1,
                                   "rating": 6}
                             )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
