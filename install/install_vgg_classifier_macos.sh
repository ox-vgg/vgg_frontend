#!/bin/bash

# - This script has been tested with macOS Sierra v10.12.3
# - It assumes Homebrew is available in the system (https://brew.sh/).
# - It assumes GIT is installed (https://sourceforge.net/projects/git-osx-installer/files/)

# Everything is installed in $HOME/visorgen/, to keep it isolated. Note
# that the paths in the start/stop scripts must also be modified for the
# scripts to work.

#install basic stuff
brew update
brew install wget
brew install cmake
#brew install python, if not already installed (up to python 2.7.13 is supported)

#caffe dependencies
brew install -vd snappy leveldb gflags glog szip lmdb
brew tap homebrew/science
brew install hdf5 opencv
brew install protobuf@2.5 boost@1.57
brew install openblas
brew install zeromq

#link some stuff
brew link glog
brew link lmdb
brew link snappy
brew link --force protobuf@2.5
brew link --force boost@1.57
brew link --force openblas
brew link zeromq

# directories
cd $HOME
mkdir $HOME/visorgen/
mkdir $HOME/visorgen/backend_dependencies

# download caffe
wget https://github.com/BVLC/caffe/archive/rc3.zip
unzip rc3.zip -d $HOME/visorgen/backend_dependencies/

# download cpp-netlib
wget https://github.com/kencoken/cpp-netlib/archive/0.11-devel.zip
unzip 0.11-devel.zip -d $HOME/visorgen/backend_dependencies/

# download liblinear
wget https://github.com/cjlin1/liblinear/archive/v210.zip
unzip v210.zip -d $HOME/visorgen/backend_dependencies/

# compile caffe
mv $HOME/visorgen/backend_dependencies/caffe-rc3/ $HOME/visorgen/backend_dependencies/caffe/
cd $HOME/visorgen/backend_dependencies/caffe/
cp Makefile.config.example Makefile.config
sed -i '.sed' 's/# CPU_ONLY/CPU_ONLY/g' Makefile.config
sed -i '.sed' 's/# BLAS_INCLUDE := $(/BLAS_INCLUDE := $(/g' Makefile.config
sed -i '.sed' 's/# BLAS_LIB := $(/BLAS_LIB := $(/g' Makefile.config
make all

# compile cpp-netlib
cd  $HOME/visorgen/backend_dependencies/cpp-netlib-0.11-devel/
mkdir build
cd build
cmake -DOPENSSL_INCLUDE_DIR=/usr/local/opt/openssl/include -DOPENSSL_SSL_LIBRARY=/usr/local/opt/openssl/lib/libssl.dylib ../
make

# compile liblinear
cd $HOME/visorgen/backend_dependencies/liblinear-210/
make lib
ln -s liblinear.so.3 liblinear.so

# clone git repo
cd $HOME/visorgen/
git clone https://gitlab.com/vgg/vgg_classifier.git

#if the C++ ZMQ port is not installed, vgg_classifier won't compile.
#do this to obtain it.
#wget https://raw.githubusercontent.com/zeromq/cppzmq/master/zmq.hpp
#cp zmq.hpp /usr/local/include/

# compile and install vgg_classifier
cd $HOME/visorgen/vgg_classifier
mkdir build
cd build
cmake -DCaffe_DIR=$HOME/visorgen/backend_dependencies/caffe \
      -DCaffe_INCLUDE_DIR="$HOME/visorgen/backend_dependencies/caffe/include;$HOME/visorgen/backend_dependencies/caffe/build/src" \
      -DLiblinear_DIR=$HOME/visorgen/backend_dependencies/liblinear-210/ \
      -Dcppnetlib_DIR=$HOME/visorgen/backend_dependencies/cpp-netlib-0.11-devel/build/ ../
make
make install

#add dylb paths to vgg_classifier dependencies
echo "export DYLD_LIBRARY_PATH=$DYLD_LIBRARY_PATH:$HOME/visorgen/backend_dependencies/liblinear-210:$HOME/visorgen/backend_dependencies/caffe/build/lib" >> $HOME/.profile
