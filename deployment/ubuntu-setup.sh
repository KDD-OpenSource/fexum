sudo apt-get update
sudo apt-get install apt-transport-https ca-certificates -y
sudo apt-key adv \
               --keyserver hkp://ha.pool.sks-keyservers.net:80 \
               --recv-keys 58118E89F3A912897C070ADBF76221572C52609D
echo "deb https://apt.dockerproject.org/repo ubuntu-xenial main" | sudo tee /etc/apt/sources.list.d/docker.list
sudo apt-get update
apt-cache policy docker-engine
sudo apt-get install linux-image-extra-$(uname -r) linux-image-extra-virtual -y
sudo apt-get install docker-engine -y
sudo service docker start

# Configure docker for non sudo mode
sudo groupadd docker
sudo usermod -aG docker $USER
newgrp docker

# Install docker-compose
sudo apt-get install python-pip -y
pip install docker-compose

# Install netshare for shared file system
sudo apt-get install -y nfs-common
sudo apt-get install nfs-kernel-server
wget https://github.com/ContainX/docker-volume-netshare/releases/download/v0.20/docker-volume-netshare_0.20_amd64.deb
sudo dpkg -i docker-volume-netshare_0.20_amd64.deb
sudo service docker-volume-netshare start
