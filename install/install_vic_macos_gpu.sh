#!/bin/bash

# - This script has been tested in a clean macOS High Sierra 10.13.3
# - It assumes Homebrew is available in the system (https://brew.sh/).
# - If used to install pip and virtualenv, it will require a sudoer user.
# - Everything is installed in $HOME/visorgen/, to keep it isolated.
# - It assumes the CUDA Toolkit and drivers are installed in your PC. Make sure you can compile and run the CUDA Toolkit Samples.
# - CUDA must be accesible, define the environment variables below to suit your local setup. The same variables should be
#   available when actually running VIC. See also the last part of the script where $HOME/.profile is modified.

#export PATH=/usr/local/cuda/bin:$PATH
#export CUDAHOME=/usr/local/cuda

# update repositories
brew update

# install some utils
brew install wget
brew install cmake
brew install jpeg libpng libtiff
brew install screen

# install pip and virtualenv, which requires sudo access
#wget https://bootstrap.pypa.io/get-pip.py -P /tmp
#sudo python /tmp/get-pip.py
#sudo pip install virtualenv

# Caffe dependencies
brew install -vd snappy leveldb gflags glog szip lmdb
brew install -vd hdf5 opencv
brew install -vd protobuf
brew install -vd boost@1.57 # the cpp-netlib version used below won't compile with newest boost
brew link --force boost@1.57
brew install -vd openblas

# create app folders
cd $HOME
mkdir $HOME/visorgen/
mkdir $HOME/visorgen/backend_data $HOME/visorgen/backend_data/cpuvisor-srv
mkdir $HOME/visorgen/datasets  $HOME/visorgen/datasets/images/  $HOME/visorgen/datasets/images/mydataset
mkdir $HOME/visorgen/datasets/metadata/  $HOME/visorgen/datasets/metadata/mydataset
mkdir $HOME/visorgen/datasets/negatives/  $HOME/visorgen/datasets/negatives/mydataset
mkdir $HOME/visorgen/frontend_data  $HOME/visorgen/frontend_data/searchdata/ $HOME/visorgen/frontend_data/curatedtrainimgs
mkdir $HOME/visorgen/frontend_data/searchdata/classifiers
mkdir $HOME/visorgen/frontend_data/searchdata/postrainanno
mkdir $HOME/visorgen/frontend_data/searchdata/postrainfeats
mkdir $HOME/visorgen/frontend_data/searchdata/postrainimgs
mkdir $HOME/visorgen/frontend_data/searchdata/rankinglists
mkdir $HOME/visorgen/frontend_data/searchdata/uploadedimgs
mkdir $HOME/visorgen/backend_dependencies
cd $HOME/visorgen/
virtualenv .
source ./bin/activate

# register the numpy version used by opencv, so that python-opencv can be used in the virtualenv
BREW_NUMPY_VERSION=$(brew info numpy | grep Cellar/numpy | awk -F '[/| |_]' '{print $6}'  )

# register the protobuf installed by homebrew, so that pycaffe can be used in the virtualenv
PROTOBUF_NUMPY_VERSION=$(brew info protobuf | grep Cellar/protobuf | awk -F '[/| |_]' '{print $6}' )

# register the openblas directory for compiling the vgg_classifier
OPENBLAS_DIR=$(brew --prefix openblas)

# update setuptools
pip install setuptools==39.1.0

# install django dependencies
pip install django==1.10
brew install -vd libevent
brew install memcached
pip install python-memcached

# frontend dependencies
pip install Pillow==2.3.0
pip install protobuf==$PROTOBUF_NUMPY_VERSION
pip install numpy==$BREW_NUMPY_VERSION
pip install Whoosh==2.7.4

# imsearch-tools dependencies
pip install gevent
pip install Flask==0.10.1

# controller dependencies
brew install -vd zeromq
pip install requests==1.1.0
pip install validictory==0.9.1
pip install msgpack-python==0.3.0
pip install gevent-zeromq

# vgg_img_downloader additional dependencies
pip install pyopenssl==17.5.0 pyasn1 ndg-httpsclient

# download caffe
wget https://github.com/BVLC/caffe/archive/1.0.zip -O /tmp/1.0.zip
unzip /tmp/1.0.zip -d $HOME/visorgen/backend_dependencies/
mv $HOME/visorgen/backend_dependencies/caffe* $HOME/visorgen/backend_dependencies/caffe

# download cpp-netlib
wget https://github.com/kencoken/cpp-netlib/archive/0.11-devel.zip -O /tmp/0.11-devel.zip
unzip /tmp/0.11-devel.zip -d $HOME/visorgen/backend_dependencies/

# download liblinear
wget https://github.com/cjlin1/liblinear/archive/v210.zip -O /tmp/v210.zip
unzip /tmp/v210.zip -d $HOME/visorgen/backend_dependencies/

# download vgg_classifier repo
wget https://gitlab.com/vgg/vgg_classifier/-/archive/master/vgg_classifier-master.zip -O /tmp/vgg_classifier.zip
unzip /tmp/vgg_classifier.zip -d $HOME/visorgen/
mv $HOME/visorgen/vgg_classifier*  $HOME/visorgen/vgg_classifier

# download vgg_frontend repo
wget https://gitlab.com/vgg/vgg_frontend/-/archive/master/vgg_frontend-master.zip -O /tmp/vgg_frontend.zip
unzip /tmp/vgg_frontend.zip -d $HOME/visorgen/
mv $HOME/visorgen/vgg_frontend*  $HOME/visorgen/vgg_frontend

# remove zips
rm -rf /tmp/*.zip

# compile caffe
cd $HOME/visorgen/backend_dependencies/caffe/
cp Makefile.config.example Makefile.config
sed -i '.sed' 's/# OPENCV_VERSION := 3/OPENCV_VERSION := 3/g' Makefile.config # homebrew will install opencv3
sed -i '.sed' 's/BLAS := atlas/BLAS := open/g' Makefile.config
sed -i '.sed' 's/# BLAS_INCLUDE := $(/BLAS_INCLUDE := $(/g' Makefile.config
sed -i '.sed' 's/# BLAS_LIB := $(/BLAS_LIB := $(/g' Makefile.config
sed -i '.sed' 's/# PYTHON_INCLUDE +=/PYTHON_INCLUDE +=/g' Makefile.config
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

#if the C++ ZMQ port is not installed, vgg_classifier won't compile.
#do this to obtain it.
wget https://raw.githubusercontent.com/zeromq/cppzmq/master/zmq.hpp -O /tmp/zmq.hpp
cp /tmp/zmq.hpp /usr/local/include/

# compile and install vgg_classifier
cd $HOME/visorgen/vgg_classifier
mkdir build
cd build
cmake -DCaffe_DIR=$HOME/visorgen/backend_dependencies/caffe \
      -DCaffe_INCLUDE_DIR="$HOME/visorgen/backend_dependencies/caffe/include;$HOME/visorgen/backend_dependencies/caffe/build/src;$OPENBLAS_DIR/include" \
      -DLiblinear_DIR=$HOME/visorgen/backend_dependencies/liblinear-210/ \
      -Dcppnetlib_DIR=$HOME/visorgen/backend_dependencies/cpp-netlib-0.11-devel/build/ ../
make
make install

# config vgg_classifier
sed -i '.sed' "s|<full_path_to_this_directory>|${HOME}/visorgen/vgg_classifier|g" $HOME/visorgen/vgg_classifier/config.prototxt
sed -i '.sed' "s|<full_path_to_base_folder_where_images_in_dsetpaths_sample.txt_are_located>|${HOME}/visorgen/datasets/images/mydataset|g" $HOME/visorgen/vgg_classifier/config.prototxt
sed -i '.sed' "s|<full_path_to_base_folder_where_images_in_negpaths_sample.txt_are_located>|${HOME}/visorgen/datasets/negatives/mydataset|g" $HOME/visorgen/vgg_classifier/config.prototxt
sed -i '.sed' "s|<full_path_to_dsetfeats_binaryproto_file_produced_by_cpuvisor_preproc>|${HOME}/visorgen/backend_data/cpuvisor-srv/dsetfeats.binaryproto|g" $HOME/visorgen/vgg_classifier/config.prototxt
sed -i '.sed' "s|<full_path_to_negpaths_binaryproto_file_produced_by_cpuvisor_preproc>|${HOME}/visorgen/backend_data/cpuvisor-srv/negfeats.binaryproto|g" $HOME/visorgen/vgg_classifier/config.prototxt
sed -i '.sed' "s|negpaths_sample|negpaths|g" $HOME/visorgen/vgg_classifier/config.prototxt
sed -i '.sed' "s|dsetpaths_sample|dsetpaths|g" $HOME/visorgen/vgg_classifier/config.prototxt

# configure vgg_frontend
echo '%45yak9wu56^(@un!b+&022fdr!-1@92_u*gctw*cw4*@hfu5t' > $HOME/visorgen/secret_key_visorgen
cp -f $HOME/visorgen/vgg_frontend/visorgen/settings_cpuvisor-srv.py $HOME/visorgen/vgg_frontend/visorgen/settings.py
sed -i '.sed' 's/"\/vgg_frontend"/"\/vic"/g' $HOME/visorgen/vgg_frontend/visorgen/settings.py
sed -i '.sed' "s|/webapps|${HOME}|g" $HOME/visorgen/vgg_frontend/visorgen/settings.py
sed -i '.sed' "s|/webapps|${HOME}|g" $HOME/visorgen/vgg_frontend/scripts/*.sh

# configure default user in vgg_frontend
cd $HOME/visorgen/vgg_frontend/
python manage.py migrate
printf "import os\nfrom django.core.wsgi import get_wsgi_application\nos.environ['DJANGO_SETTINGS_MODULE']='visorgen.settings'\napplication = get_wsgi_application()\nfrom django.contrib.auth.models import User\nuser=User.objects.create_user('admin', password='vggadmin')\nuser.is_superuser=True\nuser.is_staff=True\nuser.save()" > super.py
python super.py
rm -f super.py

#add dylb paths to vgg_classifier dependencies
echo "export DYLD_LIBRARY_PATH=$DYLD_LIBRARY_PATH:$CUDAHOME/lib:$HOME/visorgen/backend_dependencies/liblinear-210:$HOME/visorgen/backend_dependencies/caffe/build/lib" >> $HOME/.profile
source $HOME/.profile
