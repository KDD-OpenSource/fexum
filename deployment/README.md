# 0. Clone this repo
```
$ git clone git@github.com:KDD-OpenSource/fexum.git
$ cd fexum/
```

# 1. Install Docker on Ubuntu 16.04
Configure locales by selecting german (de, UTF-8) when prompted
```
$ sudo dpkg-reconfigure locales
```

Setup Docker, Docker Compose and NFS:
```
$ ./ubuntu-setup.sh
```

# 2. Start cluster 
```
$ ./start-cluster.sh
```

# 4. View configuration using Portainer
```
$ docker run -d -p 9000:9000 portainer/portainer -v "/var/run/docker.sock:/var/run/docker.sock"
```
