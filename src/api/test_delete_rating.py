from fastapi.testclient import TestClient
from fastapi import status

from main import app
from utilities import delete_rating_testuser, get_user_rate

test_app = TestClient(app)


def test_delete_rating_authent():
    """
    Test deleting a rating by an authenticated user.

    Steps:
    1. Authenticates with the '/token' endpoint to obtain an access token.
    2. Asserts that the response status code for authentication is 200 (OK).
    3. Rates a movie with a rating of 5 using the '/rate_movie/' endpoint.
    4. Asserts that the response status code for rating the movie is 200 (OK).
    5. Asserts that the user's rating count for the movie is 1.
    6. Deletes the rating of the movie using the '/delete_rate/{movie_id}' endpoint.
    7. Asserts that the response status code for deleting the rating is 200 (OK).
    8. Asserts that the user's rating count for the movie is 0 after deletion.


    Note:
    - The user is assumed to have already rated the movie with ID 1.
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

    # Step 2
    assert response.status_code == status.HTTP_200_OK

    # Step 3
    response = test_app.post("/rate_movie/",
                             headers={'accept': 'application/json',
                                      'Authorization': 'Bearer ' + access_token,
                                      'Content-Type': 'application/json'
                                      },
                             json={"movie_id": 1,
                                   "rating": 5}
                             )

    # Steps 4 & 5
    assert response.status_code == status.HTTP_200_OK
    assert len(get_user_rate("999999", 1)) == 1

    # Step 6
    response = test_app.delete('/delete_rate/1', headers={'accept': 'application/json',
                                                          'Authorization': 'Bearer ' + access_token,
                                                          'Content-Type': 'application/json'
                                                          })

    # Steps 7 & 8
    assert response.status_code == status.HTTP_200_OK
    assert len(get_user_rate("999999", 1)) == 0


def test_delete_rating_unauthent():
    """
    Test attempting to delete a rating by an unauthenticated user.

    Steps:
    1. Sends a DELETE request to the '/delete_rate/{movie_id}' endpoint with an invalid access token.
    2. Asserts that the response status code is 401 (Unauthorized).
    """
    response = test_app.delete('/delete_rate/1', headers={'accept': 'application/json',
                                                          'Authorization': 'Bearer ' + "tokenfaux",
                                                          'Content-Type': 'application/json'
                                                          })
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
