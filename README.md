# TODO

- cassandra with table and consumer that can write consumed messages into it

# Demo showing Kafka & Cassandra on Kubernetes via k3d

## Run cluster

```bash
# start k3d
$ make k3d-create
# start kafka + kafka ui
$ make kafka-create
```

To clean up after the demo/testing/dev just run:
```bash
$ make k3d-delete
```

## Access Kafka

Enable port forwarding to `kafka-0-external` service in order to send/consume messages from local machine:

```bash
$ make kafka-port-forward
```

Then you can use this broker on `127.0.0.1:9094`.

To access Kafka UI use another port forwarding command:

```bash
$ make kafka-ui-port-forward
```

The dashboard is then accesible on `localhost:8080`.

## Producer-consumer demo

Scripts for run producers and consumers are in `./apps/kafka`.

### Prepare env

Install dependencies and activate virtual-env:

```bash
# install deps
$ make venv
# activate venv
$ source venv/bin/activate
```

### Proposed demo scenario

_Run commands in different terminals to see live logs_

Create topic using admin api.
By default create just 1 partition:

```bash
$ TOPICS=temperature python admin.py
```

Run first producer:

```bash
$ TOPIC=temperature KEY=station-01 SENSOR=sensor-01 python producer.py
```

Run first consumer:

```bash
$ TOPICS=temperature GROUP=monitoring-service python consumer.py
```

Run second consumer in the same group:

```bash
$ TOPICS=temperature GROUP=monitoring-service python consumer.py
```

**Notice that consumers don't balance messages. Just one consumer will consume continously until it crashes etc., only then will the second one take over.**

Run another producer to produce on different KEY (station):

```bash
$ TOPIC=temperature KEY=station-02 SENSOR=sensor-01 python producer.py
```

**Notice that consumers still don't balance messages. This is because scaling is done based on partitions**

To see how multiple consumers and independently consume the same messages, assign different groups before launching them:

```bash
$ TOPICS=temperature GROUP=monitoring-service python consumer.py
$ TOPICS=temperature GROUP=prediction-service python consumer.py
```

That way both consumers consume in parallel, but messages are the same because groups are different.

To investigate the importance of partitions, recreate topic using admin api but this time force 2 partitions.
(may need to be run twice due to async nature of topic deletion/creation).

```bash
$ TOPICS=temperature PARTITIONS=2 python admin.py
```

Recreate the same producers and consumers (use the same group here):

```bash
$ TOPIC=temperature KEY=station-01 SENSOR=sensor-01 python producer.py
$ TOPIC=temperature KEY=station-02 SENSOR=sensor-01 python producer.py

$ TOPICS=temperature GROUP=monitoring-service python consumer.py
$ TOPICS=temperature GROUP=monitoring-service python consumer.py
```

So... now there can be 2 scenarios - either it worked ok and you are producing to 2 different partitions, thus consuming concurently using 2 consumers,
OR it still does not work for you and you are producing to a single partition.

Explanation:

- we are providing explicit KEY value in our producers
- if you delete that key, messages will be randomnly distributed across all available partitions. This is sometimes desired, sometimes not. This means that every new message can potentially choose a different partition
- now, because we are providing those keys, each message with the same key is guaranteed to land on the same partition. This is distributed using hash of the key message.
- there is a chance that hashes of 2 different keys will be such that Kafka will put those messages onto the same partition.
- so if the above is not working for you, just try with different partition keys OR try below

To test producers without partition keys, run them as such:

```bash
$ TOPIC=temperature KEY= SENSOR=sensor-01 python producer.py
$ TOPIC=temperature KEY= SENSOR=sensor-01 python producer.py
```

And now observe how round-robin assignment of partitions influences producers and consumers.

What more? Kill one (or both) of the consumers and observe what happens, which messages get consumed where, when etc.

## Delivery semantics

See `consumer.py` source code. What is defined there is a default configuration that includes `earliest` unread message and `auto commit` is enabled.

That means that the default configuration enables **at-least-once** semantics. Kafka supports:

- at least once (default)
- at most once
- exactly once

Moreover, autocommit can be disabled, seeks to specific offets can be done etc... this allows to, for example, store current offset
in Redis or on each restart seek to the last message that is written into the database etc. There are many possibilites.
Kafka architecture forces "dumb" broker and "smart" clients (consumers mainly) and this shows here.

Those configurations/scenarios are beyond this small demo.
