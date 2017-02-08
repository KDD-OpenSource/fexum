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

# Authorize our ssh keys
printf "\n# ubuntu-setup.sh\nAuthorizedKeysFile /etc/ssh/authorized_keys" >> /etc/ssh/sshd_config
cat > /etc/ssh/authorized_keys <<EOL
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAINHM/Rdj1UtrqPWMWjgXkjr5xFkyV0yRseM/uHxlHmxe AlexanderMeissner@gmx.net
ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEA6m0g/ePWldluT2zWGU2iCSCSJeJ6ZDsqoHbt7FEsUuHBC7e0OjwvxxAereiqG3coiECHVxUryIDXdrMznSZeq5gKSW6bPIDzNP0ZxgT1cyud9ILUS1oeKs6g06IoktpOxHLKeaITn5/TXbVBtGUa5NsI0snz4PW59UHs9VrFEDgW5l8oXEwvZv0tRks7gjXjbqw6jItNKoKxPynVa1wgugVnH9lGya7FJZukXtBszsey0AHuNOiLk6hE5BpXrCGiN+AHCfHe4v1G09hFYgb9r/1aeGhGMvIvhqEN4RutRS4KnIZddksPY64tgZyu6TRBJ7632IqyW7jhc5EuClkcmw== Julius@FUSIONPC
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDCX5bRx4rltnOowTGq6REMM6wbPJW9ePCIifXdCkQG8s0Apk/rKbR01FcHZLPIc7ZuhRPTBcfpx5y26JsmpwwvbZLwKTxN8i+zgANZS2h4DoeQovSbERuKT5J3OT6Ma6L/5at2Lz99S+2Wfxm+FaJ9Kg9z2zyHBZ8NxhaFsUNmi3H3eeb9r5zzQFeNwWq/6ZAn+KKwSAPSamaGWB+8BBmEKZmIMGtuNH4u+r3N66cUSwsSobAxCfrDg34QulzEKf5HdrGE5qmWxQR/eXy2bjfUMz/6/qdxoMia3Qk62fyRPUZpuDyluP4gJ40JAc0pwXG5Vst6CADO9AdCEeMDcrVj danthe@danthe-Laptop
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDna3R8BmC0OkpSgChAT8RybgE+839JAx0Cl8K3cMIFlGWqxoAUpiiukeH2TanWSB+iRwzdbGPQZj+Zd96S7qurNdSSWNibDl04gAGNGYfaWiAikS4h1uUt1hcqsC3Kb61lcyO+NHRTUqGqzNL/l2dOSEAqlM+T9EWioyycLQ0rzyMM5RXYet/Wt8jZyVVLD5GnMvVThakuDIAB00ymGo2sq3IlA2OZDD9pauauOoE01zX5SDBAspfTxxGCaD3w4/IN36s/FAkb025jo6ajw2K9Zw8jsFUyLwgsZcsAEWbmmzetAv+zy1AGRruxdf+bbypolq+qp3Y4LagwQOOUhlMJ nikriek@gmail.com
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCgvodloG1zVIUNxzaBOzgsIF3xCmU2KmCOWESzm9doqJfIQnhVsVSmm3iqYJW7xn8vnKmhHhZo59hLf+8YXPAEX/GsYu6yH/zAB0Rplei6hEWzQAH+Da9/RcowIpQF2r+XzZKdIzSDkQAc/HpKt7OQv49cZ9ToOvGACEG9X4lhHrDpdW9TWowgXJWfVbIHB+LkjSnXn7ek2SNzLLLqU10FFyffqnDRALk1Z9RBeXymaSCAZaS3l/QSGpq8TN8Jq3QNoVv016kLWYvVt1e7RQdhtTLItgU26g3RIwQyU8ixEUKRt5VnIMvZRhwgzLT59rgvHX/O3+JK3gx22O8KZj4n axels@Axel
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQCzdVLPxBAS4SSDqREvwqc4FENo5bGohoLY07ZmSnx+fWOeUSUHTg3VzBh3mZAkumC841kYCPnJ7yJVgJlNMb1xp89gvfVKIXfVtJLvBIbkpq9pn1aC9NUT2aJKoMGZgPsthrXIcHs2HInLY1nJQRzKoeR4GrsV5PhkysLZ9yD+PoLbZ4g/sFC+gmWTlOgZd5zq9jxSQ30C+7CQy2x8Ayi6HkRfxhu5YK8ug+JXaTgFEsY7KdsBVYMn/V0aDDr3i+IlVx5DpjMoGV+F20mRrPyPAqeTOx9191/yVSBKkofHQF/N/PIhhiGY1R4k4oI+oUrrgYx7M7sDDNITDQ8m+zCeZTEZzEANi9MyJjjtpshBb86rllR5GW7E8Z3ntXJ37OV/58icNLb2BKytyERxQ9U699d56xeDAdmnVtO82D+wAQqAnnS4FQZG9TWICQLmoMtcciE8TKJ8hwiOjFFxRsGGjLdVhKLBPHD2DpQo3nX2vMYjzC9BadZa5iG7TjZnYzxLBgy2F6K/m7SlZxCX+wBk6fS4r/F4qnFCOBsELVnr9kT10ptVjfezao14/t8lVVZQ4wTPwQcLDJzw2ACHRkRx+HGoVLgVcxEmIxsGDjcFxGNmyrjhiiALgvZ3t0oVbpsTqKFASllEyVyXLdgDUSarErM35+tX1d/WV5uLcbHJxQ== louis@localhost.localdomain
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQD5TMhK83NlzU6ADocQ+dCKc/KlMXp+fOfIwWca30JaNxraFacR083wVp0yJMPMd76uoVYt5tdE3GrX5GUp22Z7UtwttGyU+p+9EHhi7Zwxt1uxJIHb2LSa5i0wp0Fu+0ysxckdzN1XOY5ANWvq/djyyrvnElAxmdxJhPqRKIlTMPnU8Ydi2Cl+DTB3egEog1in7YQ3YYr4bZdRFYAA3dXCND+TyTxslLhcYwvN2hdIYouxtutBQduKJ72WxAQhWNx64I3JRZEfgPIV12t8nSJ8ufe1qvHk4GkRjyYN3ezjzXi3K+pB3bQAsyFAsGyduDbn0e6i5NaPlLnScYnmM+hyz8w7ym3ApM0CtdmgoQPmiO8o6K5wYQ/rLBPklOJn6DKk74XR1RMrsTb+bAHjac25yBAA1b+XliepRnwuvqWR1sfZVWrIBVXG6uG1F6X6HHsijmqtr7HeDqlTPXD+blaV0z9+uOIZ22WvTYEg1/+R8rJ7FN5GYOVWb8gUiKT9mwmKED5Gdad4nFniBfeJsUsgL9wYi6DihWdVwkdrW6ULYjcOcOlRbNMXOm3yAOlZ1PjorRg7GSIDr2zrlOi/ppo3OTM2mABafi8JO21QvqFIXQ5D285t0qoy9mgK57KMPIJDok6qRIB5ytks+hQhDuQDmPABAZ+/6lxTpLsPlatFqw== marcus@marcus-Aspire-E5-571G
EOL
