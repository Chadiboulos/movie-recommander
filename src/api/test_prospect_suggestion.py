from fastapi.testclient import TestClient
from main import app
import pytest


client = TestClient(app=app)


@pytest.mark.parametrize("scenario, input_data, expected_status, expected_output_check", [
    ("decade_1990", {'decade': 1990}, 200, lambda x: len(x['top_movies']) > 0),
    ("genre_zzz", {'genre': 'zzz'}, 200, lambda x: len(x['top_movies']) == 0),
    ("decade_1700", {'decade': 1700}, 200, lambda x: len(x['top_movies']) == 0),
])
def test_prospect_suggestion(scenario, input_data, expected_status, expected_output_check):
    """
    Test different scenarios for prospect movie suggestions.

    Parameters:
    - scenario (str): A string describing the test scenario.
    - input_data (dict): Input data for the test scenario.
    - expected_status (int): Expected HTTP status code of the response.
    - expected_output_check (function): Function to check the expected output.

    Steps:
    1. Sends a POST request to the '/prospect_suggestion' endpoint with input data.
    2. Asserts that the response status code matches the expected status code.
    3. Asserts that the output of the response matches the expected output based on the check function.
    """

    headers = {
        'Content-Type': 'application/json',
    }
    response = client.post('/prospect_suggestion',
                           headers=headers, json=input_data)

    assert response.status_code == expected_status

    print(response.status_code)
    print(response.json()["top_movies"])
    assert expected_output_check(response.json())
   
