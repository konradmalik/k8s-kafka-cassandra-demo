import os
import json
import queue
import atexit
import dateutil.parser

from cassandra.cluster import Cluster, Session, ResponseFuture
from cassandra.auth import PlainTextAuthProvider
from cassandra.policies import ConstantReconnectionPolicy

from confluent_kafka.cimpl import Consumer

from producer import Measurement

CASSANDRA_HOSTS = os.getenv("CASSANDRA_HOSTS", "127.0.0.1").split(",")
CASSANDRA_PORT = os.getenv("CASSANDRA_PORT", "9042")
CASSANDRA_USERNAME = os.getenv("CASSANDRA_USERNAME", "cassandra")
CASSANDRA_PASSWORD = os.getenv("CASSANDRA_PASSWORD", "cassandra")

CONCURRENCY_LEVEL = 32
TOTAL_QUERIES = 10000

BOOTSTRAP_SERVERS = os.getenv("BOOTSTRAP_SERVERS", "127.0.0.1:9094")
TOPICS = os.getenv("TOPICS", "testtopic").split(",")
# notice the convention - <keyspace>-<table>.
# This allows to easily scale dumping data
GROUP = os.getenv("GROUP", "testkeyspace-testtable")


def get_session() -> Session:
    auth = PlainTextAuthProvider(
        username=CASSANDRA_USERNAME, password=CASSANDRA_PASSWORD
    )
    rp = ConstantReconnectionPolicy(5, max_attempts=None)
    cluster = Cluster(
        contact_points=CASSANDRA_HOSTS,
        port=CASSANDRA_PORT,
        auth_provider=auth,
        reconnection_policy=rp,
    )
    return cluster.connect()


def initialize_keyspace(session: Session, name: str, replication: int = 1):
    session.execute(
        (
            f"CREATE KEYSPACE IF NOT EXISTS {name} "
            "WITH replication = "
            f"{{'class': 'SimpleStrategy', 'replication_factor': '{replication}'}}"
        )
    )


def initialize_measurements_table(session: Session, keyspace: str, table: str):
    session.execute(
        (
            f"CREATE TABLE IF NOT EXISTS {keyspace}.{table} "
            "(name text, timestamp timestamp, value double, "
            "PRIMARY KEY (name, timestamp)) "
            "WITH CLUSTERING ORDER BY (timestamp DESC)"
        )
    )


def async_data_insert(
    session: Session, keyspace: str, table: str, measurement: Measurement
) -> ResponseFuture:
    prepared_statement = session.prepare(
        f"INSERT INTO {keyspace}.{table} (name, timestamp, value) VALUES (?, ?, ?)"
    )
    # parse date into datetime instance with timezone info
    timestamp = dateutil.parser.isoparse(measurement.timestamp)
    return session.execute_async(
        prepared_statement, (measurement.name, timestamp, measurement.value)
    )


def clear_queue():
    while True:
        try:
            futures.get_nowait().result()
        except queue.Empty:
            break


if __name__ == "__main__":

    ###
    # CASSANDRA
    session = get_session()

    # initialize db in case keyspace and table do not exist
    # we use kafka consumer group to specify keyspace and table
    keyspace, table = GROUP.split("-")
    initialize_keyspace(session, keyspace)
    initialize_measurements_table(session, keyspace, table)
    futures: queue.Queue = queue.Queue(maxsize=CONCURRENCY_LEVEL)

    ###
    # KAFKA
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
        clear_queue()

    # can subscribe to multiple topics
    c.subscribe(TOPICS)

    while True:
        # poll for new message at most 1 second
        msg = c.poll(1.0)

        if msg is None:
            continue
        if msg.error():
            print("Cassandra Consumer error: {}".format(msg.error()))
            continue

        topic = msg.topic()
        key = msg.key().decode()
        value = msg.value().decode()

        print(
            "Cassandra Received message: TOPIC: {} | KEY: {} | VALUE: {}".format(
                topic, key, value
            )
        )

        data = Measurement(**json.loads(value))
        print("Cassandra Parsed data: {}".format(data))

        # actual data dump
        # Chunking way, when the max concurrency level is reached, we
        # wait the current chunk of requests to finish
        future = async_data_insert(session, keyspace, table, data)
        try:
            futures.put_nowait(future)
        except queue.Full:
            clear_queue()
            futures.put_nowait(future)
