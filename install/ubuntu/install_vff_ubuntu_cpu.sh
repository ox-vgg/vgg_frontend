#!/bin/bash

# - This script is to be run in a clean Ubuntu 14.04 LTS machine, by a sudoer user.
# - VGG_FACE_INSTALL_FOLDER/visorgen should not exist
# - Caffe is compiled for CPU use only.
# - It creates one user for the Admin Tools: login/passwd --> admin/vggadmin
# - All python dependencies are installed in a python virtual environment to avoid conflicts with pre-installed python packages

VGG_FACE_INSTALL_FOLDER="$HOME"

# update repositories
sudo apt-get update

# pip and python dependencies
sudo apt-get install -y python-pip
sudo apt-get install -y python-dev

# Caffe dependencies
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

# Other dependencies and utils
sudo apt-get install -y wget unzip
sudo apt-get install -y gfortran
sudo apt-get install -y libz-dev libjpeg-dev libfreetype6-dev
sudo apt-get install -y libxml2-dev libxslt1-dev
sudo apt-get install -y python-opencv

# create main folders and virtual environment
mkdir $VGG_FACE_INSTALL_FOLDER/visorgen/
chmod 777 $VGG_FACE_INSTALL_FOLDER/visorgen/
mkdir $VGG_FACE_INSTALL_FOLDER/visorgen/backend_data $VGG_FACE_INSTALL_FOLDER/visorgen/backend_data/faces $VGG_FACE_INSTALL_FOLDER/visorgen/backend_data/faces/features
mkdir $VGG_FACE_INSTALL_FOLDER/visorgen/datasets  $VGG_FACE_INSTALL_FOLDER/visorgen/datasets/images/  $VGG_FACE_INSTALL_FOLDER/visorgen/datasets/images/mydataset
mkdir $VGG_FACE_INSTALL_FOLDER/visorgen/datasets/metadata/  $VGG_FACE_INSTALL_FOLDER/visorgen/datasets/metadata/mydataset
mkdir $VGG_FACE_INSTALL_FOLDER/visorgen/datasets/negatives/  $VGG_FACE_INSTALL_FOLDER/visorgen/datasets/negatives/mydataset
mkdir $VGG_FACE_INSTALL_FOLDER/visorgen/frontend_data  $VGG_FACE_INSTALL_FOLDER/visorgen/frontend_data/searchdata/ $VGG_FACE_INSTALL_FOLDER/visorgen/frontend_data/curatedtrainimgs
mkdir $VGG_FACE_INSTALL_FOLDER/visorgen/frontend_data/searchdata/classifiers
mkdir $VGG_FACE_INSTALL_FOLDER/visorgen/frontend_data/searchdata/postrainanno
mkdir $VGG_FACE_INSTALL_FOLDER/visorgen/frontend_data/searchdata/postrainfeats
mkdir $VGG_FACE_INSTALL_FOLDER/visorgen/frontend_data/searchdata/postrainimgs
mkdir $VGG_FACE_INSTALL_FOLDER/visorgen/frontend_data/searchdata/rankinglists
mkdir $VGG_FACE_INSTALL_FOLDER/visorgen/frontend_data/searchdata/uploadedimgs
mkdir $VGG_FACE_INSTALL_FOLDER/visorgen/backend_dependencies
cd $VGG_FACE_INSTALL_FOLDER/visorgen/
sudo pip install virtualenv
virtualenv .
source ./bin/activate

# backend python dependencies
pip install --upgrade pip
pip install setuptools==39.1.0
pip install simplejson==3.8.2
pip install Pillow==2.3.0
pip install numpy==1.13.3
pip install lxml==4.1.1
pip install scipy==0.18.1
pip install matplotlib==2.1.0
pip install protobuf==3.0.0
pip install scikit-image==0.13.1
pip install scikit-learn==0.19.1
pip install https://storage.googleapis.com/tensorflow/linux/cpu/tensorflow-1.4.0-cp27-none-linux_x86_64.whl

# frontend dependencies
pip install django==1.10
sudo apt-get install -y memcached
pip install python-memcached
pip install Whoosh==2.7.4

# vgg_img_downloader dependencies
sudo apt-get install -y libevent-dev
pip install greenlet==0.4.10
pip install gevent==0.13.8
pip install Flask==0.10.1
pip install pyopenssl==17.5.0 pyasn1 ndg-httpsclient

# controller dependencies
sudo apt-get install -y libzmq-dev
pip install validictory==0.9.1
pip install msgpack-python==0.3.0
pip install requests==1.1.0
pip install gevent-zeromq==0.2.5

# make cv2 available in the virtualenv
ln -s /usr/lib/python2.7/dist-packages/cv2.so $VGG_FACE_INSTALL_FOLDER/visorgen/lib/python2.7/cv2.so

# dependencies for start/stop scripts
sudo apt-get install -y screen

# download caffe
wget https://github.com/BVLC/caffe/archive/1.0.zip -P /tmp
unzip /tmp/1.0.zip -d $VGG_FACE_INSTALL_FOLDER/visorgen/backend_dependencies/
mv $VGG_FACE_INSTALL_FOLDER/visorgen/backend_dependencies/caffe* $VGG_FACE_INSTALL_FOLDER/visorgen/backend_dependencies/caffe

# download SENet modifications to caffe (Sep 2017) and apply them
wget https://github.com/lishen-shirley/SENet/archive/c8f7b4e311fc9b5680047e14648fde86fb23cb17.zip -P /tmp
unzip /tmp/c8f7b4e311fc9b5680047e14648fde86fb23cb17.zip -d $VGG_FACE_INSTALL_FOLDER/visorgen/backend_dependencies/
mv $VGG_FACE_INSTALL_FOLDER/visorgen/backend_dependencies/SENet* $VGG_FACE_INSTALL_FOLDER/visorgen/backend_dependencies/SENet
cp -v $VGG_FACE_INSTALL_FOLDER/visorgen/backend_dependencies/SENet/include/caffe/layers/* $VGG_FACE_INSTALL_FOLDER/visorgen/backend_dependencies/caffe/include/caffe/layers/
cp -v $VGG_FACE_INSTALL_FOLDER/visorgen/backend_dependencies/SENet/src/caffe/layers/* $VGG_FACE_INSTALL_FOLDER/visorgen/backend_dependencies/caffe/src/caffe/layers/

# download davidsandberg's facenet (Dec 2017)
wget https://github.com/davidsandberg/facenet/archive/28d3bf2fa7254037229035cac398632a5ef6fc24.zip -P /tmp
unzip /tmp/28d3bf2fa7254037229035cac398632a5ef6fc24.zip -d $VGG_FACE_INSTALL_FOLDER/visorgen/backend_dependencies/
mv $VGG_FACE_INSTALL_FOLDER/visorgen/backend_dependencies/facenet* $VGG_FACE_INSTALL_FOLDER/visorgen/backend_dependencies/facenet

# download vgg_face_search repo
cd $VGG_FACE_INSTALL_FOLDER/visorgen/
wget https://gitlab.com/vgg/vgg_face_search/-/archive/master/vgg_face_search-master.zip -O /tmp/vgg_face_search.zip
unzip /tmp/vgg_face_search.zip -d $VGG_FACE_INSTALL_FOLDER/visorgen/
mv $VGG_FACE_INSTALL_FOLDER/visorgen/vgg_face_search*  $VGG_FACE_INSTALL_FOLDER/visorgen/vgg_face_search

# download models
cd $VGG_FACE_INSTALL_FOLDER/visorgen/backend_data/faces
wget http://www.robots.ox.ac.uk/~vgg/data/vgg_face2/256/senet50_256.caffemodel
wget http://www.robots.ox.ac.uk/~vgg/data/vgg_face2/256/senet50_256.prototxt

# download vgg_frontend repo (REMOVE - DEVELOP) !!!
wget https://gitlab.com/vgg/vgg_frontend/-/archive/develop/vgg_frontend-develop.zip -O /tmp/vgg_frontend.zip
unzip /tmp/vgg_frontend.zip -d $VGG_FACE_INSTALL_FOLDER/visorgen/
mv $VGG_FACE_INSTALL_FOLDER/visorgen/vgg_frontend*  $VGG_FACE_INSTALL_FOLDER/visorgen/vgg_frontend

# download static ffmpeg
wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz -O /tmp/ffmpeg-release-amd64-static.tar.xz
tar -xf /tmp/ffmpeg-release-amd64-static.tar.xz -C $VGG_FACE_INSTALL_FOLDER/visorgen/backend_dependencies/
mv $VGG_FACE_INSTALL_FOLDER/visorgen/backend_dependencies/ffmpeg*  $VGG_FACE_INSTALL_FOLDER/visorgen/backend_dependencies/ffmpeg
sed -i "s|ffmpeg|${VGG_FACE_INSTALL_FOLDER}/visorgen/backend_dependencies/ffmpeg/ffmpeg|g" $VGG_FACE_INSTALL_FOLDER/visorgen/vgg_face_search/pipeline/start_pipeline.sh

# remove all zips
rm -rf /tmp/*.zip
rm -rf /tmp/*.tar*

# compile caffe
cd $VGG_FACE_INSTALL_FOLDER/visorgen/backend_dependencies/caffe
cp Makefile.config.example Makefile.config
sed -i 's/# CPU_ONLY/CPU_ONLY/g' Makefile.config
sed -i 's/\/usr\/include\/python2.7/\/usr\/include\/python2.7 \/usr\/local\/lib\/python2.7\/dist-packages\/numpy\/core\/include/g' Makefile.config
make all
make pycaffe

# compile shot detector
cd $VGG_FACE_INSTALL_FOLDER/visorgen/vgg_face_search/pipeline
mkdir build
cd build
cmake -DBoost_INCLUDE_DIR=/usr/include/ ../
make

# configure vgg_face_search
sed -i "s|DATASET_FEATS_FILE|DATASET_FEATS_FILE='${VGG_FACE_INSTALL_FOLDER}/visorgen/backend_data/faces/features/database.pkl'#|g" $VGG_FACE_INSTALL_FOLDER/visorgen/vgg_face_search/service/settings.py
sed -i "s|FEATURES_CAFFE_MODEL|FEATURES_CAFFE_MODEL='${VGG_FACE_INSTALL_FOLDER}/visorgen/backend_data/faces/resnet50_256.caffemodel'#|g" $VGG_FACE_INSTALL_FOLDER/visorgen/vgg_face_search/service/settings.py
sed -i "s|FEATURES_CAFFE_PROTOTXT|FEATURES_CAFFE_PROTOTXT='${VGG_FACE_INSTALL_FOLDER}/visorgen/backend_data/faces/resnet50_256.prototxt'#|g" $VGG_FACE_INSTALL_FOLDER/visorgen/vgg_face_search/service/settings.py
sed -i "s|GPU_FACE_DETECTION_CAFFE_MODEL|#GPU_FACE_DETECTION_CAFFE_MODEL|g" $VGG_FACE_INSTALL_FOLDER/visorgen/vgg_face_search/service/settings.py
sed -i "s|DEPENDENCIES_PATH|DEPENDENCIES_PATH='${VGG_FACE_INSTALL_FOLDER}/visorgen/backend_dependencies/'#|g" $VGG_FACE_INSTALL_FOLDER/visorgen/vgg_face_search/service/settings.py
sed -i "s|resnet50_256|senet50_256|g" $VGG_FACE_INSTALL_FOLDER/visorgen/vgg_face_search/service/settings.py

# configure vgg_frontend
echo '%45yak9wu56^(@un!b+&022fdr!-1@92_u*gctw*cw4*@hfu5t' > $VGG_FACE_INSTALL_FOLDER/visorgen/secret_key_visorgen
cp -f $VGG_FACE_INSTALL_FOLDER/visorgen/vgg_frontend/visorgen/settings_faces.py $VGG_FACE_INSTALL_FOLDER/visorgen/vgg_frontend/visorgen/settings.py
cp -f $VGG_FACE_INSTALL_FOLDER/visorgen/vgg_frontend/siteroot/static/scripts/add-getting-started-lb-vff.js $VGG_FACE_INSTALL_FOLDER/visorgen/vgg_frontend/siteroot/static/scripts/add-getting-started-lb.js
sed -i 's/"\/vgg_frontend"/"\/vff"/g' $VGG_FACE_INSTALL_FOLDER/visorgen/vgg_frontend/visorgen/settings.py
sed -i "s|/webapps|${VGG_FACE_INSTALL_FOLDER}|g" $VGG_FACE_INSTALL_FOLDER/visorgen/vgg_frontend/visorgen/settings.py
sed -i "s|/webapps|${VGG_FACE_INSTALL_FOLDER}|g" $VGG_FACE_INSTALL_FOLDER/visorgen/vgg_frontend/scripts/*.sh

# configure default user in vgg_frontend
cd $VGG_FACE_INSTALL_FOLDER/visorgen/vgg_frontend/
python manage.py migrate
printf "import os\nfrom django.core.wsgi import get_wsgi_application\nos.environ['DJANGO_SETTINGS_MODULE']='visorgen.settings'\napplication = get_wsgi_application()\nfrom django.contrib.auth.models import User\nuser=User.objects.create_user('admin', password='vggadmin')\nuser.is_superuser=True\nuser.is_staff=True\nuser.save()" > super.py
python super.py
rm -f super.py
