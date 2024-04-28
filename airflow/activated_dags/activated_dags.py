import requests
import os
import json
import time

airflow_api_url = os.environ.get("AIRFLOW_URL")
airflow_user = os.environ.get("AIRFLOW_USER")
airflow_usr_pwd = os.environ.get("AIRFLOW_USR_PWD")
auth = (airflow_user, airflow_usr_pwd)
airflow_is_run = False


while not airflow_is_run:
    response = requests.get(f"{airflow_api_url}/api/v1/dags",auth=auth)
    if response.status_code == 200:
        print ("Airflow is running!!!")
        airflow_is_run = True
    else:
        print ("Airflow is not running yet !!!")
        time.sleep(5)

dagname= list()
for dag in json.loads(response.text).get("dags"):
    dagname.append(dag['dag_id'])
print(dagname)


for dag in dagname:
    # Endpoint to activate a DAG
    endpoint_activate = f'{airflow_api_url}/dags/{dag}'

    activate_payload = {'is_paused': False}

    # Send a PATCH request to activate the DAG
    response = requests.patch(endpoint_activate, json=activate_payload, auth=auth)
    if response.status_code == 200:
        print("Dag {dag} activé !!!")
    else:
        print("Probleme a l'activation du dag {dag} !!!")