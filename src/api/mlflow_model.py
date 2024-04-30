import os
import mlflow
import psycopg2
import pickle
from credentials import db_params


mlflowserver = os.environ.get('MLFLOW_SERVER')
mlflow.set_tracking_uri(mlflowserver)


def load_model_from_mlflow_runid(run_id):
    model_path = mlflow.artifacts.download_artifacts(run_id=run_id)
    model_path = os.path.join(model_path, "model")
    model_name = os.listdir(model_path)[0]
    model_path = os.path.join(model_path, model_name)
    model = pickle.load(open(model_path, "rb"))
    return model


def load_mlflow_model():
    conn = psycopg2.connect(**db_params)
    cursor = conn.cursor()
    statement = """select mlflow_run_id  from
                    model_prediction
                    where end_date is null
                    order by start_date desc"""
    cursor.execute(statement)
    result = list(cursor.fetchall())
    if len(result) != 0:
        mlflow_run_id = result[0][0]
        return mlflow_run_id,load_model_from_mlflow_runid(mlflow_run_id)
    else: raise Exception("Any model is available in the table 'model_prediction'.")

class Model:
    def __init__(self,db_params):
        self.db_params = db_params
        self.mlflow_run_id = ''
        self.model = None
        dir_path = os.path.dirname(__file__)
        with open(os.path.join(dir_path, "svd_model.pkl"), "rb") as f:
            self.defaut_model = pickle.load(f)

    def load_model_from_mlflow_runid(self, run_id: str):
        model_path = mlflow.artifacts.download_artifacts(run_id=run_id)
        model_path = os.path.join(model_path, "model")
        model_name = os.listdir(model_path)[0]
        model_path = os.path.join(model_path, model_name)
        model = pickle.load(open(model_path, "rb"))
        return model

    def get_model(self):
        conn = psycopg2.connect(**self.db_params)
        cursor = conn.cursor()
        statement = """select mlflow_run_id  from
                        model_prediction
                        where end_date is null
                        order by start_date desc"""
        cursor.execute(statement)
        result = list(cursor.fetchall())
        if len(result) != 0:
            mlflow_run_id = result[0][0]
            if mlflow_run_id == self.mlflow_run_id: return self.model
            else:
                self.mlflow_run_id = mlflow_run_id
                self.model = self.load_model_from_mlflow_runid(self.mlflow_run_id)
                return self.model
        else: return self.defaut_model


