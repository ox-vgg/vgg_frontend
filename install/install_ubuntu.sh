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

# create empty file for secret key
touch /webapps/visorgen/secret_key_visorgen

# create data folders
mkdir /webapps/visorgen/backend_data
mkdir /webapps/visorgen/datasets  /webapps/visorgen/datasets/images/  /webapps/visorgen/datasets/images/mydataset
mkdir /webapps/visorgen/datasets/metadata/  /webapps/visorgen/datasets/metadata/mydataset
mkdir /webapps/visorgen/datasets/negatives/  /webapps/visorgen/datasets/negatives/mydataset
mkdir /webapps/visorgen/frontend_data  /webapps/visorgen/frontend_data/searchdata/ /webapps/visorgen/frontend_data/curatedtrainimgs
mkdir /webapps/visorgen/frontend_data/searchdata/classifiers
mkdir /webapps/visorgen/frontend_data/searchdata/postrainanno
mkdir /webapps/visorgen/frontend_data/searchdata/postrainfeats
mkdir /webapps/visorgen/frontend_data/searchdata/postrainimgs
mkdir /webapps/visorgen/frontend_data/searchdata/rankinglists
mkdir /webapps/visorgen/frontend_data/searchdata/uploadedimgs

# Django dependencies
sudo pip install django==1.10
sudo apt-get install -y memcached
sudo pip install python-memcached

# frontend dependencies
sudo apt-get install -y libz-dev libjpeg-dev libfreetype6-dev
sudo pip install protobuf==2.6.1
sudo pip install Pillow==2.3.0

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

# dependencies for start/stop scripts
sudo apt-get install -y screen

# clone git repo
cd /webapps/visorgen/
git clone https://gitlab.com/vgg/vgg_frontend.git
