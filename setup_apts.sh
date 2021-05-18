#!/bin/bash

sudo apt-get update

echo "installing python3-dev"
sudo apt-get install -y python3-dev

echo "installing build-essential"
sudo apt-get install -y build-essential

echo "installing python-setuptools, python3-setuptools"
sudo apt-get install -y python3-setuptools
sudo apt-get install -y python-setuptools

echo "installing python3-pip"
sudo apt-get install -y python3-pip

echo "installing python-pip"
sudo apt-get install -y python-pip

echo "installing python3-venv"
sudo apt-get install -y python3-venv

echo "installing cmake"
sudo apt-get install -y cmake

echo "installing python3-distutils"
sudo apt-get install -y python3-distutils

# network monitor
echo "installing bmon"
sudo apt-get install -y bmon

# postgresql
sudo apt-get install -y libpq-dev


echo "installing docker + docker-compose"
sudo apt-get remove -y docker docker-engine docker.io containerd runc
sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo \
  "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io
sudo docker run hello-world

sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

echo "done installing docker + docker-compose"

