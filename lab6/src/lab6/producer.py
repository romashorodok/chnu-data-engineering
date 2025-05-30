import json
import time
import csv
from datetime import datetime

from kafka import KafkaProducer
from kafka.errors import KafkaError

servers = ["broker-1:29091", "localhost:9091", "broker-2:29092", "localhost:9092"]


class Producer:
    inst: KafkaProducer | None = None

    def __enter__(self):
        max_retries = 20
        backoff_base = 1

        for attempt in range(1, max_retries + 1):
            try:
                inst = KafkaProducer(bootstrap_servers=servers)
                self.inst = inst
                return inst
            except KafkaError as e:
                print(f"[ENTER] KafkaConsumer creation failed backoff {attempt}: {e}")
                if attempt == max_retries:
                    raise
                time.sleep(backoff_base * (2 ** (attempt - 1)))

        raise

    def __exit__(self, exc_type, exc_value, traceback):
        if self.inst:
            try:
                self.inst.flush()
            except Exception:
                pass
            self.inst.close()


topic_1 = "Topic-1"


def pred_datetime(row):
    return datetime.strptime(row["start_time"], "%Y-%m-%d %H:%M:%S")


with open("Divvy_Trips_2019_Q4.csv", "r") as f:
    dataset = list(csv.DictReader(f))
    dataset.sort(key=pred_datetime)

    with Producer() as producer:
        for row in dataset:
            print("send row", row)
            producer.send(
                topic_1,
                value=json.dumps(row).encode(),
            )
