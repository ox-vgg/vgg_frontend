#!/bin/bash

# - This script is to be run in a clean Ubuntu 14.04 LTS machine, by a sudoer user.
# - The directory /webapps/ should not exist

# update repositories
sudo apt-get update

# install git to clone repo
sudo apt-get install -y git

# pip and python dependencies
sudo apt-get install -y python-pip
sudo apt-get install -y python-dev

# create main folders
sudo mkdir /webapps/
sudo chmod 777 /webapps/
mkdir /webapps/visorgen

# create data folders
mkdir /webapps/visorgen/datasets
mkdir /webapps/visorgen/datasets/images/  /webapps/visorgen/datasets/images/mydataset
mkdir /webapps/visorgen/datasets/metadata/  /webapps/visorgen/datasets/metadata/mydataset
mkdir /webapps/visorgen/frontend_data  /webapps/visorgen/frontend_data/searchdata/
mkdir /webapps/visorgen/frontend_data/searchdata/predefined_rankinglists
mkdir /webapps/visorgen/frontend_data/searchdata/predefined_rankinglists/display

# Django dependencies
sudo pip install django==1.10
sudo apt-get install -y memcached
sudo pip install python-memcached

# frontend dependencies
sudo apt-get install -y libz-dev libjpeg-dev libfreetype6-dev
sudo pip install protobuf==2.6.1
sudo pip install Pillow==2.3.0
sudo pip install Whoosh==2.7.4

# imsearch-tools dependencies
sudo apt-get install -y libevent-dev
sudo pip install greenlet==0.4.10
sudo pip install gevent==0.13.8
sudo pip install Flask==0.10.1

# controller dependencies
sudo apt-get install -y libzmq-dev
sudo pip install validictory==0.9.1
sudo pip install msgpack-python==0.3.0
sudo pip install requests==1.1.0
sudo pip install gevent-zeromq==0.2.5

# download and setup vgg_frontend for JUST displaying results
wget https://gitlab.com/vgg/vgg_frontend/-/archive/master/vgg_frontend-master.zip -O /tmp/vgg_frontend.zip
unzip /tmp/vgg_frontend.zip -d /webapps/visorgen/
rm -rf /tmp/vgg_frontend.zip
mv /webapps/visorgen/vgg_frontend-* /webapps/visorgen/vgg_frontend/
echo '%45yak9wu56^(@un!b+&022fdr!-1@92_u*gctw*cw4*@hfu5t' > /webapps/visorgen/secret_key_visorgen
cp /webapps/visorgen/vgg_frontend/visorgen/settings_display.py /webapps/visorgen/vgg_frontend/visorgen/settings.py
sed -i '.sed' "s|/webapps|${HOME}|g" /webapps/visorgen/vgg_frontend/visorgen/settings.py
cd /webapps/visorgen/vgg_frontend
python manage.py migrate

