#!/bin/bash

# - This script has been tested with macOS Sierra v10.12.3
# - It assumes Homebrew is available in the system (https://brew.sh/).
# - It assumes GIT is installed (https://sourceforge.net/projects/git-osx-installer/files/)
# - Everything is installed in $HOME/visorgen/, to keep it isolated

brew update

#install python, if not already installed (up to python 2.7.13 is supported)
#brew install python

#install pip, if not already installed
#curl -O http://python-distribute.org/distribute_setup.py
#python distribute_setup.py
#curl -O https://raw.github.com/pypa/pip/master/contrib/get-pip.py
#python get-pip.py

#install everything in a virtual env, to keep it isolated
pip install virtualenv
mkdir $HOME/visorgen/
cd $HOME/visorgen/
virtualenv .
source ./bin/activate

#install django dependencies
pip install django==1.10
brew install -vd libevent
brew install memcached
pip install python-memcached

#frontend dependencies
pip install Pillow==2.3.0
pip install protobuf==2.6.1

#imsearch-tools dependencies
pip install gevent
pip install Flask==0.10.1

#controller dependencies
brew install zeromq
pip install requests==1.1.0
pip install validictory==0.9.1
pip install msgpack-python==0.3.0
pip install gevent-zeromq

# clone git repo
git clone https://gitlab.com/vgg/vgg_frontend.git
