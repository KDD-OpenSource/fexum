#!/bin/bash

USERNAME="user"

SWARM_PORT=2377
MASTER_NODE="BP2016MUE1WS07.hpi.uni-potsdam.d"
WORKER_NODES=("BP2016MUE1WS04.hpi.uni-potsdam.de" "BP2016MUE1WS05.hpi.uni-potsdam.de")
JOIN_TOKEN=""

function setup_master_node() {
  echo "Setting up master at $MASTER_NODE...";
  JOIN_TOKEN=$(ssh $USERNAME@$MASTER_NODE 'docker swarm init &> /dev/null; docker swarm join-token manager -q >&1');
  echo "Join token is $JOIN_TOKEN";
  
  echo "Starting NFS server..."
}

function setup_worker_node() {
  for worker in $WORKER_NODES; do
    echo "Setting up worker at $worker";
    ssh $USERNAME@$MASTER_NODE "docker swarm join --token $JOIN_TOKEN $MASTER_NODE:$SWARM_PORT";
  done
}

setup_master_node
setup_worker_node
