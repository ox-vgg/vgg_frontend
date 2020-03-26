#!/bin/bash

# - This script is to be run in a clean Ubuntu 16 LTS machine, by a sudoer user.
# - The directory /webapps/ should not exist.
# - A python3 virtualenv is created in /webapps/visorgen/ which needs to be activated to run the application.

# update repositories
sudo apt-get update

# install all apt-get dependencies
sudo apt-get install -y python-pip python3-pip
sudo apt-get install -y python-dev python3-dev
sudo apt-get install -y memcached
sudo apt-get install -y libz-dev libjpeg-dev libfreetype6-dev
sudo apt-get install -y libzmq-dev

# install virtualenv
sudo pip install configparser==4.0.2
sudo pip install virtualenv==20.0.7
pip install --upgrade pip
pip install zipp

# create main folders
sudo mkdir /webapps/
sudo chmod 777 /webapps/
mkdir /webapps/visorgen
cd /webapps/visorgen
virtualenv -p python3 .
source ./bin/activate

# create data folders
mkdir /webapps/visorgen/datasets
mkdir /webapps/visorgen/datasets/images/  /webapps/visorgen/datasets/images/mydataset
mkdir /webapps/visorgen/datasets/metadata/  /webapps/visorgen/datasets/metadata/mydataset
mkdir /webapps/visorgen/frontend_data  /webapps/visorgen/frontend_data/searchdata/
mkdir /webapps/visorgen/frontend_data/searchdata/predefined_rankinglists
mkdir /webapps/visorgen/frontend_data/searchdata/predefined_rankinglists/display

# Django dependencies
pip install django==1.10
pip install python-memcached

# frontend dependencies
pip install protobuf==3.0.0
pip install Pillow==2.3.0
pip install Whoosh==2.7.4
pip install simplejson==3.8.2

# controller dependencies
pip install validictory==0.9.1
pip install msgpack-python==0.3.0
pip install requests==2.2.1
pip install pyzmq==17.1.2

# download and setup vgg_frontend for JUST displaying results
wget https://gitlab.com/vgg/vgg_frontend/-/archive/master/vgg_frontend-master.zip -O /tmp/vgg_frontend.zip
unzip /tmp/vgg_frontend.zip -d /webapps/visorgen/
rm -rf /tmp/vgg_frontend.zip
mv /webapps/visorgen/vgg_frontend-* /webapps/visorgen/vgg_frontend/
echo '%45yak9wu56^(@un!b+&022fdr!-1@92_u*gctw*cw4*@hfu5t' > /webapps/visorgen/secret_key_visorgen
cp /webapps/visorgen/vgg_frontend/visorgen/settings_display.py /webapps/visorgen/vgg_frontend/visorgen/settings.py
cd /webapps/visorgen/vgg_frontend
python manage.py migrate
