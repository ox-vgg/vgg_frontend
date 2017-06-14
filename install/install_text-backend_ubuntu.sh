#!/bin/bash

# - This script is to be run in a clean Ubuntu 14.04 LTS machine, by a sudoer user.
# - The directory /webapps/ should not exists

# update repositories
sudo apt-get update

# install git to clone repo
sudo apt-get install -y git

# pip and python dependencies
sudo apt-get install -y python-pip
sudo apt-get install -y python-dev

# setup folders
sudo mkdir /webapps/
sudo chmod 777 /webapps/
mkdir /webapps/visorgen
mkdir /webapps/visorgen/backend_dependencies

# text-backend aditional dependencies
sudo apt-get install -y openjdk-7-jdk
sudo pip install JCC==2.15
sudo apt-get install -y ant
# pylucene-3.6 installed below is also a dependency.

# download pylucene
wget https://www.apache.org/dist/lucene/pylucene/pylucene-3.6.2-1-src.tar.gz
tar -xzvf pylucene-3.6.2-1-src.tar.gz -C /webapps/visorgen/backend_dependencies/

# compile pylucene
cd /webapps/visorgen/backend_dependencies/pylucene-3.6.2-1/
cp Makefile Makefile.copy
sed -i 's/# Linux     (Ubuntu 11.10 64-bit/PREFIX_PYTHON=\/usr\nANT=JAVA_HOME=\/usr\/lib\/jvm\/java-7-openjdk-amd64 \/usr\/bin\/ant\nPYTHON=$(PREFIX_PYTHON)\/bin\/python\nJCC=$(PYTHON) -m jcc --shared\nNUM_FILES=4\n# Linux     (Ubuntu 11.10 64-bit/g' Makefile
make
sudo make install

# clone git repo
cd /webapps/visorgen/
git clone https://gitlab.com/vgg/text_search.git
