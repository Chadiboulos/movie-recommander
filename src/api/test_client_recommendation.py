from fastapi.testclient import TestClient
from fastapi import status
from main import app

client = TestClient(app=app)


def test_unauthenticated_user_get_recommendations():
    """
    Test retrieving recommendations by an unauthenticated user.

    Steps:
    1. Sends a GET request to the '/client_recommendation/' endpoint.
    2. Asserts that the response status code is 401 (Unauthorized).
    3. Asserts that the response JSON contains the expected error message.
    """
    response = client.get("/client_recommendation/")
    assert response.status_code == 401

    expected_error_message = {"detail": "Not authenticated"}
    assert response.json() == expected_error_message


def test_authenticated_user_get_recommendations():
    """
    Test retrieving recommendations by an authenticated user.

    Steps:
    1. Authenticates with the '/token' endpoint to obtain an access token.
    2. Sends a GET request to the '/client_recommendation/' endpoint with the access token.
    3. Asserts that the response status code is 200 (OK).
    4. Asserts that the response JSON contains recommendations.
    """

    username = 'test1'

    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded',
    }

    data = {
        'username': username,
        'password': 'testuser',  # user_hash_password
    }

    response = client.post('/token', headers=headers, data=data)

    access_token = response.json()['access_token']

    response = client.get(
        url="/client_recommendation/",
        headers={'accept': 'application/json',
                 'Authorization': 'Bearer ' + access_token}
    )

    print(response.json())

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) > 0
