# https://docs.confluent.io/platform/current/clients/confluent-kafka-python/html/index.html#producer
import time
import os
import json
import atexit
from random import random
from dataclasses import dataclass, asdict
from confluent_kafka.cimpl import Producer, Message
from datetime import datetime, timezone

BOOTSTRAP_SERVERS = os.getenv("BOOTSTRAP_SERVERS", "127.0.0.1:9094")
TOPIC = os.getenv("TOPIC", "testtopic")
SENSOR = os.getenv("SENSOR", "testsensor")
KEY = os.getenv("KEY", "teststation")
INTERVAL = 2


@dataclass
class Measurement:
    name: str
    timestamp: str
    value: float


def generate_data_json() -> str:
    d = Measurement(SENSOR, now_utc_tz().isoformat(), random())
    return json.dumps(asdict(d))


def now_utc_tz() -> datetime:
    return datetime.now(timezone.utc)


def delivery_report(err: str, msg: Message):
    """Called once for each message produced to indicate delivery result.
    Triggered by poll() or flush()."""
    if err is not None:
        print("Message delivery failed: {}".format(err))
    else:
        print("Message delivered to {} [{}]".format(msg.topic(), msg.partition()))


if __name__ == "__main__":
    # async producer
    # default serializers -> BYTES
    p = Producer(
        {
            "bootstrap.servers": BOOTSTRAP_SERVERS,
        }
    )

    @atexit.register
    def finisher():
        # Wait for any outstanding messages to be delivered and delivery report
        # callbacks to be triggered.
        p.flush(5)

    while True:
        # Trigger any available delivery report callbacks from previous produce() calls
        p.poll(0)

        # Asynchronously produce a message, the delivery report callback
        # will be triggered from poll() above, or flush() below, when the message has
        # been successfully delivered or failed permanently.
        value = generate_data_json().encode()
        key = KEY if KEY.strip() != "" else None
        print("Producing message: KEY: {} | VALUE: {}".format(key, value))
        p.produce(TOPIC, value, key, callback=delivery_report)
        # wait specified interval
        time.sleep(INTERVAL)
