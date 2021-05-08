KUBECTL ?= kubectl
HELM ?= helm

k3d-create:
	k3d cluster create --config k3d.yaml

k3d-delete:
	k3d cluster delete rc

kafka-create:
	${KUBECTL} create namespace kafka --dry-run -o yaml | ${KUBECTL} apply -f - \
	&& ${HELM} repo add bitnami https://charts.bitnami.com/bitnami \
	&& ${HELM} upgrade --install --create-namespace --namespace kafka kafka bitnami/kafka --version 12.17.6 --values ./kafka/values.yaml \
	&& ${KUBECTL} apply --namespace kafka -f kafka/kafka-ui.yaml

kafka-delete:
	${KUBECTL} delete --namespace kafka -f kafka/kafka-ui.yaml \
	; ${HELM} uninstall --namespace kafka kafka

kafka-port-forward:
	${KUBECTL} --namespace kafka port-forward svc/kafka-0-external --address 0.0.0.0 9094:9094

kafka-ui-port-forward:
	${KUBECTL} --namespace kafka port-forward svc/kafka-ui --address 0.0.0.0 8080:8080

cassandra-create:
	${KUBECTL} create namespace cassandra --dry-run -o yaml | ${KUBECTL} apply -f - \
	&& ${HELM} repo add bitnami https://charts.bitnami.com/bitnami \
	&& ${HELM} upgrade --install --create-namespace --namespace cassandra cassandra bitnami/cassandra --version 7.5.5 --values ./cassandra/values.yaml

cassandra-delete:
	${HELM} uninstall --namespace cassandra cassandra

cassandra-port-forward:
	${KUBECTL} --namespace cassandra port-forward svc/cassandra --address 0.0.0.0 9042:9042

cassandra-cqlsh:
	${KUBECTL} --namespace cassandra run --rm -it cassandra-client \
		--restart='Never' \
		--image bitnami/cassandra:3.11.10-debian-10-r78 \
		-- cqlsh -u cassandra -p cassandra cassandra
