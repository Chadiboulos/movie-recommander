from fastapi.testclient import TestClient
from fastapi import status
from main import app

client = TestClient(app=app)


def test_status():
    """
    Test the status endpoint.

    Steps:
    1. Sends a GET request to the '/status' endpoint.
    2. Asserts that the response status code is 200 (OK).
    3. Asserts that the response JSON contains the key "status" end value is OK .
    """
    response = client.get('/status')
    assert response.status_code == status.HTTP_200_OK
    assert response.json().get("status") == "OK"


def test_root():
    """
    Test the root endpoint.

    Steps:
    1. Sends a GET request to the '/' endpoint.
    2. Asserts that the response status code is 200 (OK).
    3. Asserts that the response text contains "Welcome".
    """
    response = client.get('/')
    assert response.status_code == status.HTTP_200_OK
    assert "Welcome" in response.text


def test_secured():
    """
    Test the secured endpoint.

    Steps:
    1. Authenticates with the '/token' endpoint to obtain an access token.
    2. Sends a POST request to the '/token' endpoint with authentication data.
    3. Asserts that the response status code is 200 (OK).
    """

    username = 'daniel'

    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    data = {
        'username': username,
        'password': 'datascientest'
    }
    response = client.post('token', headers=headers, data=data)
    assert response.status_code == status.HTTP_200_OK
    
def test_secured_bad_user():
    """
    Negatif Test the secured endpoint.

    Steps:
    1. Try to authenticates with the '/token' with a bad user => not existing .
    2. Sends a POST request to the '/token' endpoint with authentication data.
    3. Asserts that the response status code is 400(KO).
    """

    username = 'danielLLL'

    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    data = {
        'username': username,
        'password': 'datascientest'
    }
    response = client.post('token', headers=headers, data=data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    
def test_secured_bad_password():
    """
    Negatif Test the secured endpoint.

    Steps:
    1. Try to authenticates with the '/token' with a bad password.
    2. Sends a POST request to the '/token' endpoint with authentication data.
    3. Asserts that the response status code is 400(KO).
    """

    username = 'daniel'

    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    data = {
        'username': username,
        'password': 'datascientestTTT'
    }
    response = client.post('token', headers=headers, data=data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
