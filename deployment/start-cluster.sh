#!/bin/bash

# Hosts
# 172.16.19.193	BP1
# 172.16.19.196	BP2
# 172.16.16.97	BP3
# 172.16.19.237	BP4
# 172.16.19.197	BP5
# 172.16.19.199	BP6
# 172.16.18.127	BP7

USERNAME="user"

SWARM_PORT=2377
MASTER_NODE="172.16.18.127"
WORKER_NODES=("172.16.19.237", "172.16.19.197")
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
