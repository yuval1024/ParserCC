#!/bin/bash

base_cwd=$(pwd)

bash setup_apts.sh

echo "installing wheel"
#python3 -m pip install wheel
pip install wheel

echo "installing setuptools"
pip install -U pip setuptools

if [[ -z "${GITHUB_JOB}" ]]; then
  echo "GITHUB_JOB is undef; not running in Github Action context"
  python3 -m venv ~/venv/
  source ~/venv/bin/activate
else
  echo "Running in Github Action context; not creating virtualenv"
fi


echo "installing docker + compose"
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

echo "done installing docker + compose"


#echo "install hyperscan"
# hyperscan::
# https://python-hyperscan.readthedocs.io/en/latest/
# http://intel.github.io/hyperscan/dev-reference/getting_started.html#requirements
sudo apt-get install -y libboost-all-dev
sudo apt-get install -y ragel

git clone https://github.com/intel/hyperscan.git
mkdir -p hyperscan/build
cd hyperscan/build
git checkout v5.1.1
cmake \
    -G "Unix Makefiles" \
    -DCMAKE_INSTALL_PREFIX:PATH=/usr \
    -DBUILD_SHARED_LIBS=ON ../
make -j $(( $(nproc)))
sudo make install
# back to home folder
cd ${base_cwd}
# some error with latest version (2.0.0), use 0.1.5 instead:: https://github.com/darvid/python-hyperscan/issues/28
pip install hyperscan==0.1.5


echo "install wheel"
# install wheel; otherwise have to install requirements twice
pip install wheel
pip install git+https://github.com/wearpants/warc3

echo "install requirements.txt"
cd ${base_cwd}
python3 -m pip install -r requirements.txt
#pip install -r requirements.txt

echo "install smart_open"
python3 -m pip install smart_open[all]

python3 -m pip install flake8
