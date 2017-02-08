sudo apt-get update
sudo apt-get install apt-transport-https ca-certificates -y
sudo apt-key adv \
               --keyserver hkp://ha.pool.sks-keyservers.net:80 \
               --recv-keys 58118E89F3A912897C070ADBF76221572C52609D
echo "deb https://apt.dockerproject.org/repo ubuntu-xenial main" | sudo tee /etc/apt/sources.list.d/docker.list
sudo apt-get update
apt-cache policy docker-engine
sudo apt-get install -y linux-image-extra-$(uname -r) linux-image-extra-virtual docker-engine
sudo service docker start

# Enable experimental version
sudo touch /etc/docker/deamon.json
echo '{"experimental": true}' | sudo dd of=/etc/docker/deamon.json

# Configure docker for non sudo mode
sudo groupadd docker
sudo usermod -aG docker $USER
newgrp docker

# Install docker-compose
sudo apt-get install -y python-pip
pip install docker-compose

# Install netshare for shared file system
sudo apt-get install -y nfs-common nfs-kernel-server
wget https://github.com/ContainX/docker-volume-netshare/releases/download/v0.20/docker-volume-netshare_0.20_amd64.deb
sudo dpkg -i docker-volume-netshare_0.20_amd64.deb
sudo service docker-volume-netshare start

# Install compiler
deb http://apt.llvm.org/precise/ llvm-toolchain-precise-4.0 main
deb-src http://apt.llvm.org/precise/ llvm-toolchain-precise-4.0 main
sudo apt-get install -y clang-4.0

# Install utilities
sudo apt-get install -y btrfs-tools htop unzip zip
