#!/bin/bash

# - This script has been tested with macOS Sierra v10.12.3 and macOS High Sierra v10.13.3
# - It assumes Homebrew is available in the system (https://brew.sh/), as well as python (up to python 2.7.13 is supported).
# - Everything is installed in $HOME/$visorgen/, to keep it isolated
# - Check commented lines to install pip/virtualenv, which will require sudo access

# update repositories
brew update

# install some utils
brew install wget
brew install jpeg libpng libtiff

#install pip, if not already installed
#wget https://bootstrap.pypa.io/get-pip.py -P /tmp
#sudo python /tmp/get-pip.py
#sudo pip install virtualenv

# install everything in a virtual env, to keep it isolated
mkdir $HOME/visorgen/
cd $HOME/visorgen/
virtualenv .
source ./bin/activate

# install django dependencies
pip install django==1.10
brew install -vd libevent
brew install memcached
pip install python-memcached

# frontend dependencies
pip install Pillow==2.3.0
pip install protobuf==2.6.1
pip install Whoosh==2.7.4

# controller dependencies
brew install zeromq
pip install requests==1.1.0
pip install validictory==0.9.1
pip install msgpack-python==0.3.0
pip install gevent-zeromq

# download and setup vgg_frontend for JUST displaying results
wget https://gitlab.com/vgg/vgg_frontend/-/archive/master/vgg_frontend-master.zip -O /tmp/vgg_frontend.zip
unzip /tmp/vgg_frontend.zip -d $HOME/visorgen/
rm -rf /tmp/vgg_frontend.zip
mv $HOME/visorgen/vgg_frontend-* $HOME/visorgen/vgg_frontend/
echo '%45yak9wu56^(@un!b+&022fdr!-1@92_u*gctw*cw4*@hfu5t' > $HOME/visorgen/secret_key_visorgen
cp $HOME/visorgen/vgg_frontend/visorgen/settings_display.py $HOME/visorgen/vgg_frontend/visorgen/settings.py
sed -i '.sed' "s|/webapps|${HOME}|g" $HOME/visorgen/vgg_frontend/visorgen/settings.py
cd $HOME/visorgen/vgg_frontend
python manage.py migrate

# create folders for images, metadata and pre-defined lists
mkdir $HOME/visorgen/datasets
mkdir $HOME/visorgen/datasets/images/  $HOME/visorgen/datasets/images/mydataset
mkdir $HOME/visorgen/datasets/metadata/  $HOME/visorgen/datasets/metadata/mydataset
mkdir $HOME/visorgen/frontend_data  $HOME/visorgen/frontend_data/searchdata/
mkdir $HOME/visorgen/frontend_data/searchdata/predefined_rankinglists
mkdir $HOME/visorgen/frontend_data/searchdata/predefined_rankinglists/display

