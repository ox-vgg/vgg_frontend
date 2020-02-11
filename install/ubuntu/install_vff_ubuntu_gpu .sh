#!/bin/bash

# - This script is to be run in a clean Ubuntu 16 LTS machine, by a sudoer user.
# - VGG_FACE_INSTALL_FOLDER/visorgen should not exist
# - It creates one user for the Admin Tools: login/passwd --> admin/vggadmin
# - All python dependencies are installed in a python virtual environment to avoid conflicts with pre-installed python packages
# - It assumes the CUDA Toolkit and drivers are installed in your PC. Make sure you can compile and run the CUDA Toolkit Samples.
# - CUDA must be accesible, define the environment variables commented below to suit your local setup. The same variables should be
#   available when actually running VFF, and should be added to:
#     * $VGG_FACE_INSTALL_FOLDER/visorgen/vgg_face_search/service/start_backend_service.sh
#     * $VGG_FACE_INSTALL_FOLDER/visorgen/vgg_face_search/pipeline/start_pipeline.sh

#export PATH=/usr/local/cuda/bin:$PATH
#export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/cuda/lib64:/usr/local/lib
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
sudo apt-get install -y python-opencv python-tk

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
pip install setuptools==39.1.0
pip install simplejson==3.8.2
pip install Pillow==6.1.0
pip install numpy==1.13.3
pip install Cython==0.27.3
pip install scipy==0.18.1
pip install matplotlib==2.1.0
pip install scikit-image==0.13.1
pip install protobuf==3.0.0
pip install easydict==1.7
pip install pyyaml==3.12

# frontend dependencies
pip install django==1.10
sudo apt-get install -y memcached
pip install python-memcached
pip install Whoosh==2.7.4

# vgg_img_downloader dependencies
sudo apt-get install -y libevent-dev
pip install greenlet==0.4.15
pip install gevent==0.13.8
pip install Flask==0.10.1
pip install pyopenssl==17.5.0 pyasn1 ndg-httpsclient

# controller dependencies
sudo apt-get install -y libzmq-dev
pip install validictory==0.9.1
pip install msgpack-python==0.3.0
pip install requests==2.2.1
pip install pyzmq==17.1.2

# make cv2 available in the virtualenv
cp /usr/lib/python2.7/dist-packages/cv2*.so $VGG_FACE_INSTALL_FOLDER/visorgen/lib/python2.7/cv2.so

# dependencies for start/stop scripts
sudo apt-get install -y screen

# For the "PROTOCOL_SSLv3" change, see https://github.com/mistio/mist-ce/issues/434#issuecomment-86484952
sed -i 's|PROTOCOL_SSLv3|PROTOCOL_SSLv23|g' $VGG_FACE_INSTALL_FOLDER/visorgen/lib/python2.7/site-packages/gevent/ssl.py
sed -i 's|ssl.PROTOCOL_SSLv3|#ssl.PROTOCOL_SSLv3|g' $VGG_FACE_INSTALL_FOLDER/visorgen/lib/python2.7/site-packages/requests/packages/urllib3/contrib/pyopenssl.py

# download face-py-faster-rcnn and caffe-fast-rcnn
wget https://github.com/playerkk/face-py-faster-rcnn/archive/9d8c143e0ff214a1dcc6ec5650fb5045f3002c2c.zip -P /tmp
unzip /tmp/9d8c143e0ff214a1dcc6ec5650fb5045f3002c2c.zip -d $VGG_FACE_INSTALL_FOLDER/visorgen/backend_dependencies/
mv $VGG_FACE_INSTALL_FOLDER/visorgen/backend_dependencies/face-py-faster-rcnn-* $VGG_FACE_INSTALL_FOLDER/visorgen/backend_dependencies/face-py-faster-rcnn
wget https://github.com/rbgirshick/caffe-fast-rcnn/archive/0dcd397b29507b8314e252e850518c5695efbb83.zip -P /tmp
unzip /tmp/0dcd397b29507b8314e252e850518c5695efbb83.zip -d $VGG_FACE_INSTALL_FOLDER/visorgen/backend_dependencies/face-py-faster-rcnn
rm -r $VGG_FACE_INSTALL_FOLDER/visorgen/backend_dependencies/face-py-faster-rcnn/caffe-fast-rcnn
mv $VGG_FACE_INSTALL_FOLDER/visorgen/backend_dependencies/face-py-faster-rcnn/caffe-fast-rcnn-* $VGG_FACE_INSTALL_FOLDER/visorgen/backend_dependencies/face-py-faster-rcnn/caffe-fast-rcnn

# download SENet modifications to caffe (Sep 2017) and apply them
wget https://github.com/lishen-shirley/SENet/archive/c8f7b4e311fc9b5680047e14648fde86fb23cb17.zip -P /tmp
unzip /tmp/c8f7b4e311fc9b5680047e14648fde86fb23cb17.zip -d $VGG_FACE_INSTALL_FOLDER/visorgen/backend_dependencies/
mv $VGG_FACE_INSTALL_FOLDER/visorgen/backend_dependencies/SENet* $VGG_FACE_INSTALL_FOLDER/visorgen/backend_dependencies/SENet
cp -v $VGG_FACE_INSTALL_FOLDER/visorgen/backend_dependencies/SENet/include/caffe/layers/* $VGG_FACE_INSTALL_FOLDER/visorgen/backend_dependencies/face-py-faster-rcnn/caffe-fast-rcnn/include/caffe/layers/
cp -v $VGG_FACE_INSTALL_FOLDER/visorgen/backend_dependencies/SENet/src/caffe/layers/* $VGG_FACE_INSTALL_FOLDER/visorgen/backend_dependencies/face-py-faster-rcnn/caffe-fast-rcnn/src/caffe/layers/

# download vgg_face_search repo
cd $VGG_FACE_INSTALL_FOLDER/visorgen/
wget https://gitlab.com/vgg/vgg_face_search/-/archive/master/vgg_face_search-master.zip -O /tmp/vgg_face_search.zip
unzip /tmp/vgg_face_search.zip -d $VGG_FACE_INSTALL_FOLDER/visorgen/
mv $VGG_FACE_INSTALL_FOLDER/visorgen/vgg_face_search*  $VGG_FACE_INSTALL_FOLDER/visorgen/vgg_face_search

# download models
cd $VGG_FACE_INSTALL_FOLDER/visorgen/backend_data/faces
wget http://www.robots.ox.ac.uk/~vgg/data/vgg_face2/256/senet50_256.caffemodel
wget http://www.robots.ox.ac.uk/~vgg/data/vgg_face2/256/senet50_256.prototxt
wget http://supermoe.cs.umass.edu/%7Ehzjiang/data/vgg16_faster_rcnn_iter_80000.caffemodel

# download vgg_frontend repo
wget https://gitlab.com/vgg/vgg_frontend/-/archive/master/vgg_frontend-master.zip -O /tmp/vgg_frontend.zip
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

# compile face-py-faster-rcnn and caffe-fast-rcnn
cd $VGG_FACE_INSTALL_FOLDER/visorgen/backend_dependencies/face-py-faster-rcnn/lib
make
cd $VGG_FACE_INSTALL_FOLDER/visorgen/backend_dependencies/face-py-faster-rcnn/caffe-fast-rcnn
cp Makefile.config.example Makefile.config
sed -i 's/# WITH_PYTHON_LAYER/WITH_PYTHON_LAYER/g' Makefile.config
sed -i 's/\/usr\/include\/python2.7/\/usr\/include\/python2.7 \/usr\/local\/lib\/python2.7\/dist-packages\/numpy\/core\/include/g' Makefile.config
sed -i 's/INCLUDE_DIRS :=/INCLUDE_DIRS := \/usr\/include\/hdf5\/serial\/ /g' Makefile.config
sed -i 's/LIBRARY_DIRS :=/LIBRARY_DIRS := \/usr\/lib\/x86_64-linux-gnu\/hdf5\/serial\/ /g' Makefile.config
sed -i 's/# Configure build/CXXFLAGS += -std=c++11/g' Makefile
make all
make pycaffe

# compile shot detector
cd $VGG_FACE_INSTALL_FOLDER/visorgen/vgg_face_search/pipeline
mkdir build
cd build
cmake -DBoost_INCLUDE_DIR=/usr/include/ ../
make

# configure vgg_face_search
sed -i 's|CUDA_ENABLED = False|CUDA_ENABLED = True|g' $VGG_FACE_INSTALL_FOLDER/visorgen/vgg_face_search/service/settings.py
sed -i "s|DATASET_FEATS_FILE|DATASET_FEATS_FILE='${VGG_FACE_INSTALL_FOLDER}/visorgen/backend_data/faces/features/database.pkl'#|g" $VGG_FACE_INSTALL_FOLDER/visorgen/vgg_face_search/service/settings.py
sed -i "s|FEATURES_CAFFE_MODEL|FEATURES_CAFFE_MODEL='${VGG_FACE_INSTALL_FOLDER}/visorgen/backend_data/faces/resnet50_256.caffemodel'#|g" $VGG_FACE_INSTALL_FOLDER/visorgen/vgg_face_search/service/settings.py
sed -i "s|FEATURES_CAFFE_PROTOTXT|FEATURES_CAFFE_PROTOTXT='${VGG_FACE_INSTALL_FOLDER}/visorgen/backend_data/faces/resnet50_256.prototxt'#|g" $VGG_FACE_INSTALL_FOLDER/visorgen/vgg_face_search/service/settings.py
sed -i "s|GPU_FACE_DETECTION_CAFFE_MODEL|GPU_FACE_DETECTION_CAFFE_MODEL='${VGG_FACE_INSTALL_FOLDER}/visorgen/backend_data/faces/vgg16_faster_rcnn_iter_80000.caffemodel'#|g" $VGG_FACE_INSTALL_FOLDER/visorgen/vgg_face_search/service/settings.py
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
