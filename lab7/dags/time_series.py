from datetime import datetime, timedelta
from airflow.decorators import dag, task
import random
import pandas as pd


@dag(catchup=False, schedule="* * * * *", default_args={"catchup": False})
def time_series():
    @task
    def extract_time_series() -> list[dict]:
        start_time = datetime(2025, 1, 1)
        data = []

        for i in range(100):
            point = {
                "meta": {
                    "timestamp": (start_time + timedelta(minutes=i)).isoformat(),
                },
                "metrics": {
                    "value": round(random.uniform(10, 100), 2),
                },
            }
            data.append(point)

        return data

    @task
    def transform_time_series(data) -> list[dict]:
        flattened = [
            {
                "timestamp": d["meta"]["timestamp"],
                "value": d["metrics"]["value"],
            }
            for d in data
        ]
        flattened.sort(key=lambda x: x["value"])
        return flattened

    @task
    def load_time_series(data):
        loaded_data = pd.DataFrame(data)
        print(loaded_data)

    extracted = extract_time_series()
    transformed = transform_time_series(extracted)
    load_time_series(transformed)


time_series()
