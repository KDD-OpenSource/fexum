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
WORKER_NODES=("172.16.19.237" "172.16.19.197")
JOIN_TOKEN=""

NFS_MOUNT_DIR="/var/nfs/general"

function setup_master_node() {
  echo "Setting up master at $MASTER_NODE...";
  JOIN_TOKEN=$(ssh $USERNAME@$MASTER_NODE 'docker swarm init &> /dev/null; docker swarm join-token manager -q >&1');
  echo "Join token is $JOIN_TOKEN";
  
}

function setup_nfs_master() {
  echo "Setting up NFS server..."
  
  # Setup options for settings file
  nfs_options="$NFS_MOUNT_DIR"
  for worker in "${WORKER_NODES[@]}"; do
      nfs_options+=" $worker(rw,sync,no_subtree_check)"
  done
  
  ssh $USERNAME@$MASTER_NODE /bin/bash << EOSSH
    # Create mounting point and make it non superuser accessible
    sudo mkdir $NFS_MOUNT_DIR -p
    sudo chown nobody:nogroup /var/nfs/general
    
    # Setup options in settings file
    echo "$nfs_options" | sudo dd of=/etc/exports
  
    # Restart to make changes happen
    sudo systemctl restart nfs-kernel-server
  
    # Setup firewall
    for worker in "${WORKER_NODES[@]}"; do
      sudo ufw allow from $worker to any port nfs
    done
EOSSH
  
  echo "Done setting up NFS server..."
}

function setup_nfs_client() {
  for worker in "${WORKER_NODES[@]}"; do
      ssh $USERNAME@$worker /bin/bash << EOSSH
        sudo mkdir -p $MOUNT_DIR
        sudo mount $MASTER_NODE:$MOUNT_DIR $MOUNT_DIR
EOSSH
  done
}

function setup_worker_node() {
  for worker in "${WORKER_NODES[@]}"; do
    echo "Setting up worker at $worker";
    ssh $USERNAME@$worker "docker swarm join --token $JOIN_TOKEN $MASTER_NODE:$SWARM_PORT";
  done
}
