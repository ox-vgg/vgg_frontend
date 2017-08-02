#!/bin/bash

# - This script is to be run in a clean Ubuntu 14.04 LTS machine, by a sudoer user.
# - The directory /webapps/ should not exists
# - Caffe is compiled for CPU use only.

# update repositories
sudo apt-get update

# install git to clone repo
sudo apt-get install -y git

# Caffe  dependencies
sudo apt-get install -y cmake
sudo apt-get install -y pkg-config
sudo apt-get install -y libgoogle-glog-dev
sudo apt-get install -y libhdf5-serial-dev
sudo apt-get install -y liblmdb-dev
sudo apt-get install -y libleveldb-dev
sudo apt-get install -y libprotobuf-dev
sudo apt-get install -y protobuf-compiler
sudo apt-get install -y libopencv-dev
sudo apt-get install -y libatlas-base-dev
sudo apt-get install -y libsnappy-dev
sudo apt-get install -y libgflags-dev
sudo apt-get install -y --no-install-recommends libboost-all-dev

# pip and python dependencies
sudo apt-get install -y python-pip
sudo apt-get install -y python-dev

# setup folders
sudo mkdir /webapps/
sudo chmod 777 /webapps/
mkdir /webapps/visorgen
mkdir /webapps/visorgen/backend_dependencies

# caffe-backend aditional dependencies
sudo apt-get install -y libzmq-dev
sudo pip install protobuf==2.6.1
# liblinear installed below is also a dependency.
# caffe installed below is also a dependency.
# cpp-netlib installed below is also a dependency.

# cpp-netlib aditional dependencies
sudo apt-get install -y libssl-dev

# download caffe
sudo apt-get install -y unzip
wget https://github.com/BVLC/caffe/archive/rc3.zip
unzip rc3.zip -d /webapps/visorgen/backend_dependencies/

# download cpp-netlib
wget https://github.com/kencoken/cpp-netlib/archive/0.11-devel.zip
unzip 0.11-devel.zip -d /webapps/visorgen/backend_dependencies/

# download liblinear
wget https://github.com/cjlin1/liblinear/archive/v210.zip
unzip v210.zip -d /webapps/visorgen/backend_dependencies/

# compile caffe
cd /webapps/visorgen/backend_dependencies/caffe-rc3/
cp Makefile.config.example Makefile.config
sed -i 's/# CPU_ONLY/CPU_ONLY/g' Makefile.config
sed -i 's/\/usr\/include\/python2.7/\/usr\/include\/python2.7 \/usr\/local\/lib\/python2.7\/dist-packages\/numpy\/core\/include/g' Makefile.config
make all

# compile cpp-netlib
cd  /webapps/visorgen/backend_dependencies/cpp-netlib-0.11-devel/
mkdir build
cd build
cmake -DCMAKE_BUILD_TYPE=Debug -DCMAKE_C_COMPILER=/usr/bin/cc -DCMAKE_CXX_COMPILER=/usr/bin/c++ ../
make

# compile liblinear
cd /webapps/visorgen/backend_dependencies/liblinear-210/
make lib
ln -s liblinear.so.3 liblinear.so

# clone git repo
cd /webapps/visorgen/
git clone https://gitlab.com/vgg/vgg_classifier.git

# compile and install vgg_classifier
cd /webapps/visorgen/vgg_classifier
mkdir build
cd build
cmake -DCaffe_DIR=/webapps/visorgen/backend_dependencies/caffe-rc3/ -DCaffe_INCLUDE_DIR="/webapps/visorgen/backend_dependencies/caffe-rc3/include;/webapps/visorgen/backend_dependencies/caffe-rc3/build/src" -DLiblinear_DIR=/webapps/visorgen/backend_dependencies/liblinear-210/ -Dcppnetlib_DIR=/webapps/visorgen/backend_dependencies/cpp-netlib-0.11-devel/build/ ../
make
make install
