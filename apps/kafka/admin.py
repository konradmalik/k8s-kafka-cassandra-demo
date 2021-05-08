# https://docs.confluent.io/platform/current/clients/confluent-kafka-python/html/index.html?highlight=newtopic#module-confluent_kafka.admin
import os
from confluent_kafka.cimpl import NewTopic
from confluent_kafka.admin import AdminClient

BOOTSTRAP_SERVERS = os.getenv("BOOTSTRAP_SERVERS", "127.0.0.1:9094")
TOPIC = os.getenv("TOPIC", "testtopic")
PARTITIONS = os.getenv("PARTITIONS", "1")
REPLICATION = os.getenv("REPLICATION", "1")


def delete_topic(
    client: AdminClient,
    name: str,
):
    # Call delete_topics to asynchronously delete topics, a future is returned.
    # By default this operation on the broker returns immediately while
    # topics are deleted in the background. But here we give it some time (30s)
    # to propagate in the cluster before returning.
    #
    # Returns a dict of <topic,future>.
    fs = client.delete_topics(topics=[name], operation_timeout=30)

    # Wait for operation to finish.
    for topic, f in fs.items():
        try:
            f.result()  # The result itself is None
            print("Topic {} deleted".format(topic))
        except Exception as e:
            print("Failed to delete topic {}: {}".format(topic, e))


def create_topic(
    client: AdminClient, name: str, partitions: int, replication_factor: int = -1
):
    nt = NewTopic(
        topic=name,
        num_partitions=partitions,
        replication_factor=replication_factor,
    )

    # Call create_topics to asynchronously create topics, a dict
    # of <topic,future> is returned.
    fs = client.create_topics(new_topics=[nt])

    # Wait for operation to finish.
    # Timeouts are preferably controlled by passing request_timeout=15.0
    # to the create_topics() call.
    # All futures will finish at the same time.
    for topic, f in fs.items():
        try:
            f.result()  # The result itself is None
            print("Topic {} created".format(topic))
        except Exception as e:
            print("Failed to create topic {}: {}".format(topic, e))


if __name__ == "__main__":
    # manually create topic to force 2 partitions
    # partitions can be added to existing topics but we want convinience here
    a = AdminClient(
        {
            "bootstrap.servers": BOOTSTRAP_SERVERS,
        }
    )
    delete_topic(a, TOPIC)
    create_topic(a, TOPIC, int(PARTITIONS), int(REPLICATION))

    print(
        "created: {} with {} partitions and {} replication factor".format(
            TOPIC, PARTITIONS, REPLICATION
        )
    )
