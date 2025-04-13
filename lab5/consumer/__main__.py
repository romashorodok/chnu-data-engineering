import os
import time

from kafka import KafkaConsumer
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


topic = os.environ["TOPIC"]

with Consumer(f"{topic}-queue") as consumer:
    consumer.subscribe([topic])
    print(f"CONSUMER {topic} | Start consumer")

    for msg in consumer:
        print(f"{topic} CONSUMER |", msg)
        time.sleep(2)
