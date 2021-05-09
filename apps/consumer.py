# https://docs.confluent.io/platform/current/clients/confluent-kafka-python/html/index.html#consumer
import os
import json
import atexit
from confluent_kafka.cimpl import Consumer
from producer import Measurement

BOOTSTRAP_SERVERS = os.getenv("BOOTSTRAP_SERVERS", "127.0.0.1:9094")
TOPICS = os.getenv("TOPICS", "testtopic").split(",")
GROUP = os.getenv("GROUP", "testservice")

if __name__ == "__main__":

    c = Consumer(
        {
            "bootstrap.servers": BOOTSTRAP_SERVERS,
            "group.id": GROUP,
            # by using earliest offset reset and autocommit we have "at-least-once" semantic (default)
            # "at-most-once" and "exactly-once" are also available
            # https://docs.confluent.io/platform/current/clients/consumer.html
            "auto.offset.reset": "earliest",
            "enable.auto.commit": "true",
        }
    )

    @atexit.register
    def finisher():
        # close consumer on exit
        c.close()

    # can subscribe to multiple topics
    c.subscribe(TOPICS)

    while True:
        # poll for new message at most 1 second
        msg = c.poll(1.0)

        if msg is None:
            continue
        if msg.error():
            print("Consumer error: {}".format(msg.error()))
            continue

        topic = msg.topic()
        key = msg.key().decode()
        value = msg.value().decode()

        print(
            "Received message: TOPIC: {} | KEY: {} | VALUE: {}".format(
                topic, key, value
            )
        )

        data = Measurement(**json.loads(value))
        print("Parsed data: {}".format(data))
