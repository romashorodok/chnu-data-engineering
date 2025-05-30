import csv
from io import TextIOWrapper
import json
import os
import time
from datetime import datetime
from minio import Minio

from kafka import KafkaConsumer
from kafka.consumer.fetcher import ConsumerRecord
from kafka.errors import KafkaError

servers = ["broker-1:29091", "localhost:9091", "broker-2:29092", "localhost:9092"]


class Consumer:
    inst: KafkaConsumer | None = None

    def __init__(self, group_id: str) -> None:
        self.__group_id = group_id

    def __enter__(self):
        max_retries = 20
        backoff_base = 1

        for attempt in range(1, max_retries + 1):
            try:
                inst = KafkaConsumer(
                    group_id=self.__group_id,
                    enable_auto_commit=True,
                    bootstrap_servers=servers,
                )
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
            self.inst.close()


minio_client = Minio(
    "minio:9000", access_key="minioadmin", secret_key="minioadmin", secure=False
)

BUCKET_NAME = os.environ.get("BUCKET_NAME", "dataset")
if not minio_client.bucket_exists(BUCKET_NAME):
    minio_client.make_bucket(BUCKET_NAME)


TEMP_DIR = "./temp"
os.makedirs(TEMP_DIR, exist_ok=True)


def open_file(month_year, init_data):
    print(f"Open {month_year}")
    path = os.path.join(TEMP_DIR, f"{month_year}.csv")
    file = open(path, "a")
    dict_writer = csv.DictWriter(file, init_data.keys())
    dict_writer.writeheader()
    dict_writer.writerow(init_data)
    file.flush()
    return file, dict_writer


def upload_to_minio(path):
    print(f"Upload the {path}")
    minio_client.fput_object(
        BUCKET_NAME,
        os.path.basename(path),
        path,
    )
    print(f"Uploaded the {path}")


topic = os.environ["TOPIC"]

with Consumer(f"{topic}-queue") as consumer:
    consumer.subscribe([topic])
    print(f"CONSUMER {topic} | Start consumer")

    cursor: str | None = None

    file: TextIOWrapper | None = None
    writer: csv.DictWriter | None = None

    for msg in consumer:
        msg: ConsumerRecord = msg
        data = json.loads(msg.value)

        start_time = data.get("start_time")

        dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        month_year = f"{dt.strftime('%B').lower()}-{dt.year}"

        if not cursor:
            cursor = month_year
            file, writer = open_file(month_year, data)

        if cursor != month_year:
            if file:
                file.flush()
                file.close()
                path = os.path.join(TEMP_DIR, f"{cursor}.csv")
                upload_to_minio(path)
                os.remove(path)

            file, writer = open_file(month_year, data)
            cursor = month_year

        assert writer
        writer.writerow(data)
        assert file
        file.flush()

        # time.sleep(2)
