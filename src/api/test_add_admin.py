from fastapi.testclient import TestClient
from fastapi import status
from main import app
from credentials import db_params
import psycopg2


test_app = TestClient(app)


def test_add_admin():
    """
    Test adding a new admin user to the system.

    Steps:
    1. Retrieves an access token for an existing admin user.
    2. Deletes any test admin user from the database (if exists).
    3. Adds a new test admin user with a username and password.
    4. Tries to add an existing admin user (admin) which should fail.

    Assertions:
    - The response status code for adding a new admin should be 200 OK.
    - The response JSON message should indicate successful addition of the user.
    - Trying to add an existing admin user should return a 400 Bad Request.
    - The response JSON should contain the appropriate error message.
    """
    # Step 1
    response = test_app.post('/token',
                             headers={
                                 'accept': 'application/json',
                                 'Content-Type': 'application/x-www-form-urlencoded'},
                             data={'username': 'admin',
                                   'password': 'admin'
                                   })
    access_token = response.json()["access_token"]
    assert response.status_code == status.HTTP_200_OK

    # Step 2
    conn = psycopg2.connect(**db_params)
    cursor = conn.cursor()
    cursor.execute(""" DELETE FROM users WHERE username = 'test_admin' """)
    conn.commit()

    # Step 3
    response = test_app.post("/add_admins/",
                             headers={
                                 'accept': 'application/json',
                                 'Content-Type': 'application/x-www-form-urlencoded',
                                 'Authorization': 'Bearer ' + access_token},
                             data={
                                 'user': 'test_admin',
                                 'password': 'test_admin'})
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": "User added successfully!"}

    # Step 4
    response = test_app.post("/add_admins/",
                             headers={
                                 'accept': 'application/json',
                                 'Content-Type': 'application/x-www-form-urlencoded',
                                 'Authorization': 'Bearer ' + access_token},
                             data={
                                 'user': 'admin',
                                 'password': 'admin'})
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "user already exists in database"}

    conn.close()
    cursor.close()
