#!/bin/bash

# - This script is to be run in a clean Ubuntu 16 LTS machine, by a sudoer user.
# - The directory /webapps/ should not exist
# - Caffe is compiled for CPU if nvidia-smi cannot be found in the system.
# - It creates one user for the Admin Tools: login/passwd --> admin/vggadmin
# - Start the application with /webapps/visorgen/vgg_frontend/scripts/ start_all_django.sh category

# update repositories
sudo apt-get update

# pip and python dependencies
sudo apt-get install -y python-pip python3-pip
sudo apt-get install -y python-dev python3-dev

# install Caffe dependencies
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

# cpp-netlib dependencies
sudo apt-get install -y libssl-dev

# frontend dependencies
sudo apt-get install -y libz-dev libjpeg-dev libfreetype6-dev
sudo apt-get install -y screen
sudo apt-get install -y libzmq-dev

# vgg_classifier dependencies
sudo apt-get install -y libevent-dev

# Django dependencies
sudo apt-get install -y memcached

# install virtualenv
sudo pip install configparser==4.0.2
sudo pip install virtualenv==20.0.7
pip install --upgrade pip
pip install zipp

# create main folder and virtualenv
sudo mkdir /webapps/
sudo chmod 777 /webapps/
mkdir /webapps/visorgen
cd /webapps/visorgen
virtualenv -p python3 .
source ./bin/activate

# create app folders
mkdir /webapps/visorgen/backend_data /webapps/visorgen/backend_data/cpuvisor-srv
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
mkdir /webapps/visorgen/backend_dependencies

# vgg_classifier dependencies
pip install numpy==1.11.1
pip install Pillow==6.1.0
pip install matplotlib==2.1.0

# Django python dependencies
pip install django==1.10
pip install python-memcached

# frontend python dependencies
pip install protobuf==3.0.0
pip install Whoosh==2.7.4
pip install simplejson==3.8.2

# vgg_img_downloader python dependencies
pip install greenlet==0.4.15
pip install gevent==1.1.0
pip install Flask==0.10.1
pip install pyopenssl==17.5.0 pyasn1 ndg-httpsclient

# controller python dependencies
pip install validictory==0.9.1
pip install msgpack-python==0.3.0
pip install requests==2.2.1
pip install pyzmq==17.1.2

# download caffe
sudo apt-get install -y unzip
wget https://github.com/BVLC/caffe/archive/1.0.zip -O /tmp/1.0.zip
unzip /tmp/1.0.zip -d /webapps/visorgen/backend_dependencies/
mv /webapps/visorgen/backend_dependencies/caffe* /webapps/visorgen/backend_dependencies/caffe

# download cpp-netlib
wget https://github.com/kencoken/cpp-netlib/archive/0.11-devel.zip -O /tmp/0.11-devel.zip
unzip /tmp/0.11-devel.zip -d /webapps/visorgen/backend_dependencies/

# download liblinear
wget https://github.com/cjlin1/liblinear/archive/v210.zip -O /tmp/v210.zip
unzip /tmp/v210.zip -d /webapps/visorgen/backend_dependencies/

# download vgg_classifier repo
wget https://gitlab.com/vgg/vgg_classifier/-/archive/master/vgg_classifier-master.zip -O /tmp/vgg_classifier.zip
unzip /tmp/vgg_classifier.zip -d /webapps/visorgen/
mv /webapps/visorgen/vgg_classifier*  /webapps/visorgen/vgg_classifier

# download vgg_frontend repo
wget https://gitlab.com/vgg/vgg_frontend/-/archive/develop/vgg_frontend-develop.zip -O /tmp/vgg_frontend.zip
unzip /tmp/vgg_frontend.zip -d /webapps/visorgen/
mv /webapps/visorgen/vgg_frontend*  /webapps/visorgen/vgg_frontend

# remove zips
rm -rf /tmp/*.zip

# compile caffe
# N.B.: No need to setup pycaffe
cd /webapps/visorgen/backend_dependencies/caffe/
cp Makefile.config.example Makefile.config
if [[ $(nvidia-smi) ]]; then
    echo "FOUND NVIDIA-SMI, will try to compile Caffe with GPU support !"
    # CUDA must be accessible, so define the environment variables below to suit your local setup. The same variables should be
    # available when actually running VIC.
    export PATH=/usr/local/cuda/bin:$PATH
    export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/cuda/lib64:/usr/local/lib
else
    echo "DID NOT FOUND NVIDIA-SMI, will compile Caffe for CPU only !"
    sed -i 's/# CPU_ONLY/CPU_ONLY/g' Makefile.config
fi
sed -i 's/INCLUDE_DIRS :=/INCLUDE_DIRS := \/usr\/include\/hdf5\/serial\/ /g' Makefile.config
sed -i 's/LIBRARY_DIRS :=/LIBRARY_DIRS := \/usr\/lib\/x86_64-linux-gnu\/hdf5\/serial\/ /g' Makefile.config
sed -i 's/# Configure build/CXXFLAGS += -std=c++11/g' Makefile
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

# compile and install vgg_classifier
cd /webapps/visorgen/vgg_classifier
mkdir build
cd build
cmake -DCMAKE_CXX_STANDARD=11 -DCaffe_DIR=/webapps/visorgen/backend_dependencies/caffe/ -DCaffe_INCLUDE_DIR="/webapps/visorgen/backend_dependencies/caffe/include;/webapps/visorgen/backend_dependencies/caffe/build/src" -DLiblinear_DIR=/webapps/visorgen/backend_dependencies/liblinear-210/ -Dcppnetlib_DIR=/webapps/visorgen/backend_dependencies/cpp-netlib-0.11-devel/build/ ../
make
make install

# config vgg_classifier
sed -i 's|<full_path_to_this_directory>|/webapps/visorgen/vgg_classifier|g' /webapps/visorgen/vgg_classifier/config.prototxt
sed -i 's|<full_path_to_base_folder_where_images_in_dsetpaths_sample.txt_are_located>|/webapps/visorgen/datasets/images/mydataset|g' /webapps/visorgen/vgg_classifier/config.prototxt
sed -i 's|<full_path_to_base_folder_where_images_in_negpaths_sample.txt_are_located>|/webapps/visorgen/datasets/negatives/mydataset|g' /webapps/visorgen/vgg_classifier/config.prototxt
sed -i 's|<full_path_to_dsetfeats_binaryproto_file_produced_by_cpuvisor_preproc>|/webapps/visorgen/backend_data/cpuvisor-srv/dsetfeats.binaryproto|g' /webapps/visorgen/vgg_classifier/config.prototxt
sed -i 's|<full_path_to_negpaths_binaryproto_file_produced_by_cpuvisor_preproc>|/webapps/visorgen/backend_data/cpuvisor-srv/negfeats.binaryproto|g' /webapps/visorgen/vgg_classifier/config.prototxt
sed -i 's|/webapps/visorgen/vgg_classifier/dsetpaths_sample.txt|/webapps/visorgen/backend_data/cpuvisor-srv/dsetpaths.txt|g' /webapps/visorgen/vgg_classifier/config.prototxt
sed -i 's|/webapps/visorgen/vgg_classifier/negpaths_sample.txt|/webapps/visorgen/backend_data/cpuvisor-srv/negpaths.txt|g' /webapps/visorgen/vgg_classifier/config.prototxt

# configure vgg_frontend
echo '%45yak9wu56^(@un!b+&022fdr!-1@92_u*gctw*cw4*@hfu5t' > /webapps/visorgen/secret_key_visorgen
cp -f /webapps/visorgen/vgg_frontend/visorgen/settings_cpuvisor-srv.py /webapps/visorgen/vgg_frontend/visorgen/settings.py
cp -f /webapps/visorgen/vgg_frontend/siteroot/static/scripts/add-getting-started-lb-vic.js /webapps/visorgen/vgg_frontend/siteroot/static/scripts/add-getting-started-lb.js
sed -i 's/"\/vgg_frontend"/"\/vic"/g' /webapps/visorgen/vgg_frontend/visorgen/settings.py

# configure default user in vgg_frontend
cd /webapps/visorgen/vgg_frontend/
python manage.py migrate
printf "import os\nfrom django.core.wsgi import get_wsgi_application\nos.environ['DJANGO_SETTINGS_MODULE']='visorgen.settings'\napplication = get_wsgi_application()\nfrom django.contrib.auth.models import User\nuser=User.objects.create_user('admin', password='vggadmin')\nuser.is_superuser=True\nuser.is_staff=True\nuser.save()" > super.py
python super.py
rm -f super.py
