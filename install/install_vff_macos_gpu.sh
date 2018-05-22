#!/bin/bash

# - This script has been tested in a clean macOS High Sierra 10.13.3
# - It assumes Homebrew is available in the system (https://brew.sh/).
# - If used to install pip and virtualenv, it will require a sudoer user.
# - All python dependencies are installed in a python virtual environment to avoid conflicts with pre-installed python packages
# - VGG_FACE_INSTALL_FOLDER/visorgen should not exist
# - It creates one user for the Admin Tools: login/passwd --> admin/vggadmin
# - It assumes the CUDA Toolkit and drivers are installed in your PC. Make sure you can compile and run the CUDA Toolkit Samples.
# - CUDA must be accesible, define the commented environment variables below to suit your local setup. The same variables should be
#   available when actually running VFF, and should be added to:
#     * $VGG_FACE_INSTALL_FOLDER/visorgen/vgg_face_search/service/start_backend_service.sh
#     * $VGG_FACE_INSTALL_FOLDER/visorgen/vgg_face_search/pipeline/start_pipeline.sh
#     * See also the last part of the script where $HOME/.profile is modified.
# - Compilation notes:
#   - Use Xcode CommandLineTools for macOS 10.12 (v8.1 or above)
#   - See https://github.com/CharlesShang/TFFRCNN/issues/21

#export PATH=/usr/local/cuda/bin:$PATH
#export CUDAHOME=/usr/local/cuda
VGG_FACE_INSTALL_FOLDER="$HOME"

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

# caffe dependencies
brew install -vd snappy leveldb gflags glog szip lmdb
brew install -vd hdf5 opencv
brew install -vd tesseract
brew install -vd protobuf
brew install -vd boost@1.59 boost-python@1.59
brew install -vd openblas
brew link --force boost@1.59
brew link --force boost-python@1.59

# create app folders
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
virtualenv .
source ./bin/activate
pip install setuptools==39.1.0

# register the numpy version used by opencv, so that python-opencv can be used in the virtualenv
BREW_NUMPY_VERSION=$(brew info numpy | grep Cellar/numpy | awk -F '[/| |_]' '{print $6}'  )

# register the protobuf installed by homebrew, so that pycaffe can be used in the virtualenv
PROTOBUF_NUMPY_VERSION=$(brew info protobuf | grep Cellar/protobuf | awk -F '[/| |_]' '{print $6}' )

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

# vgg_img_downloader dependencies
pip install gevent
pip install Flask==0.10.1
pip install pyopenssl==17.5.0 pyasn1 ndg-httpsclient

# controller dependencies
brew install -vd zeromq
pip install requests==1.1.0
pip install validictory==0.9.1
pip install msgpack-python==0.3.0
pip install gevent-zeromq

# backend dependencies
pip install simplejson==3.8.2
pip install Cython==0.27.3
pip install scipy==0.18.1
pip install matplotlib==2.1.0
pip install scikit-image==0.13.1
pip install easydict==1.7
pip install pyyaml==3.12
pip install six==1.11.0

# Download vgg_face_search git repo and create virtual environment
wget https://gitlab.com/vgg/vgg_face_search/-/archive/master/vgg_face_search-master.zip -O /tmp/vgg_face_search.zip
unzip /tmp/vgg_face_search.zip -d $VGG_FACE_INSTALL_FOLDER/visorgen/
mv $VGG_FACE_INSTALL_FOLDER/visorgen/vgg_face_search*  $VGG_FACE_INSTALL_FOLDER/visorgen/vgg_face_search

# download vgg_frontend repo
wget https://gitlab.com/vgg/vgg_frontend/-/archive/master/vgg_frontend-master.zip -O /tmp/vgg_frontend.zip
unzip /tmp/vgg_frontend.zip -d $VGG_FACE_INSTALL_FOLDER/visorgen/
mv $VGG_FACE_INSTALL_FOLDER/visorgen/vgg_frontend*  $VGG_FACE_INSTALL_FOLDER/visorgen/vgg_frontend

# download face-py-faster-rcnn and caffe-fast-rcnn
wget https://github.com/playerkk/face-py-faster-rcnn/archive/9d8c143e0ff214a1dcc6ec5650fb5045f3002c2c.zip -P /tmp
unzip /tmp/9d8c143e0ff214a1dcc6ec5650fb5045f3002c2c.zip -d $VGG_FACE_INSTALL_FOLDER/visorgen/backend_dependencies
mv $VGG_FACE_INSTALL_FOLDER/visorgen/backend_dependencies/face-py-faster-rcnn-* $VGG_FACE_INSTALL_FOLDER/visorgen/backend_dependencies/face-py-faster-rcnn
wget https://github.com/rbgirshick/caffe-fast-rcnn/archive/0dcd397b29507b8314e252e850518c5695efbb83.zip -P /tmp
unzip /tmp/0dcd397b29507b8314e252e850518c5695efbb83.zip -d $VGG_FACE_INSTALL_FOLDER/visorgen/backend_dependencies/face-py-faster-rcnn
rm -r $VGG_FACE_INSTALL_FOLDER/visorgen/backend_dependencies/face-py-faster-rcnn/caffe-fast-rcnn
mv $VGG_FACE_INSTALL_FOLDER/visorgen/backend_dependencies/face-py-faster-rcnn/caffe-fast-rcnn-* $VGG_FACE_INSTALL_FOLDER/visorgen/backend_dependencies/face-py-faster-rcnn/caffe-fast-rcnn

# download models
cd $VGG_FACE_INSTALL_FOLDER/visorgen/backend_data/faces
wget http://www.robots.ox.ac.uk/~vgg/data/vgg_face2/256/resnet50_256.caffemodel
wget http://www.robots.ox.ac.uk/~vgg/data/vgg_face2/256/resnet50_256.prototxt
wget http://supermoe.cs.umass.edu/%7Ehzjiang/data/vgg16_faster_rcnn_iter_80000.caffemodel

# download static ffmpeg
wget https://ffmpeg.zeranoe.com/builds/macos64/static/ffmpeg-20180411-9825f77-macos64-static.zip -P /tmp
unzip /tmp/ffmpeg-20180411-9825f77-macos64-static.zip -d $VGG_FACE_INSTALL_FOLDER/visorgen/backend_dependencies
mv $VGG_FACE_INSTALL_FOLDER/visorgen/backend_dependencies/ffmpeg*  $VGG_FACE_INSTALL_FOLDER/visorgen/backend_dependencies/ffmpeg
sed -i '.sed' "s|ffmpeg|${VGG_FACE_INSTALL_FOLDER}/visorgen/backend_dependencies/ffmpeg/bin/ffmpeg|g" $VGG_FACE_INSTALL_FOLDER/visorgen/vgg_face_search/pipeline/start_pipeline.sh

# remove all zips
rm -rf /tmp/*.zip

# compile face-py-faster-rcnn and caffe-fast-rcnn
cd $VGG_FACE_INSTALL_FOLDER/visorgen/backend_dependencies/face-py-faster-rcnn/lib
make
cd $VGG_FACE_INSTALL_FOLDER/visorgen/backend_dependencies/face-py-faster-rcnn/caffe-fast-rcnn
cp Makefile.config.example Makefile.config
sed -i '.sed' 's/# OPENCV_VERSION := 3/OPENCV_VERSION := 3/g' Makefile.config  # homebrew will install opencv3
sed -i '.sed' 's/BLAS := atlas/BLAS := open/g' Makefile.config
sed -i '.sed' 's/# BLAS_INCLUDE := $(/BLAS_INCLUDE := $(/g' Makefile.config
sed -i '.sed' 's/# BLAS_LIB := $(/BLAS_LIB := $(/g' Makefile.config
sed -i '.sed' 's/# PYTHON_INCLUDE +=/PYTHON_INCLUDE +=/g' Makefile.config
make all
make pycaffe

# compile shot detector
BREW_BOOST_ROOT=$(brew info boost@1.59 | grep Cellar/boost | awk '{print $1}' )
cd $VGG_FACE_INSTALL_FOLDER/visorgen/vgg_face_search/pipeline
mkdir build
cd build
cmake -DBOOST_ROOT=$BREW_BOOST_ROOT ../
make

# Make cv2 available in the virtualenv
CV2_LOCATION=$(brew info opencv | grep /usr/local/Cellar | cut -d' ' -f1)
ln -s $CV2_LOCATION/lib/python2.7/site-packages/cv2.so $VGG_FACE_INSTALL_FOLDER/visorgen/lib/python2.7/cv2.so

# configure vgg_face_search
sed -i '.sed' 's|CUDA_ENABLED = False|CUDA_ENABLED = True|g' $VGG_FACE_INSTALL_FOLDER/visorgen/vgg_face_search/service/settings.py
sed -i '.sed' "s|DATASET_FEATS_FILE|DATASET_FEATS_FILE='${VGG_FACE_INSTALL_FOLDER}/visorgen/backend_data/faces/features/database.pkl'#|g" $VGG_FACE_INSTALL_FOLDER/visorgen/vgg_face_search/service/settings.py
sed -i '.sed' "s|FEATURES_CAFFE_MODEL|FEATURES_CAFFE_MODEL='${VGG_FACE_INSTALL_FOLDER}/visorgen/backend_data/faces/resnet50_256.caffemodel'#|g" $VGG_FACE_INSTALL_FOLDER/visorgen/vgg_face_search/service/settings.py
sed -i '.sed' "s|FEATURES_CAFFE_PROTOTXT|FEATURES_CAFFE_PROTOTXT='${VGG_FACE_INSTALL_FOLDER}/visorgen/backend_data/faces/resnet50_256.prototxt'#|g" $VGG_FACE_INSTALL_FOLDER/visorgen/vgg_face_search/service/settings.py
sed -i '.sed' "s|GPU_FACE_DETECTION_CAFFE_MODEL|GPU_FACE_DETECTION_CAFFE_MODEL='${VGG_FACE_INSTALL_FOLDER}/visorgen/backend_data/faces/vgg16_faster_rcnn_iter_80000.caffemodel'#|g" $VGG_FACE_INSTALL_FOLDER/visorgen/vgg_face_search/service/settings.py
sed -i '.sed' "s|DEPENDENCIES_PATH|DEPENDENCIES_PATH='${VGG_FACE_INSTALL_FOLDER}/visorgen/backend_dependencies/'#|g" $VGG_FACE_INSTALL_FOLDER/visorgen/vgg_face_search/service/settings.py

# configure vgg_frontend
echo '%45yak9wu56^(@un!b+&022fdr!-1@92_u*gctw*cw4*@hfu5t' >  $VGG_FACE_INSTALL_FOLDER/visorgen/secret_key_visorgen
cp -f  $VGG_FACE_INSTALL_FOLDER/visorgen/vgg_frontend/visorgen/settings_faces.py  $VGG_FACE_INSTALL_FOLDER/visorgen/vgg_frontend/visorgen/settings.py
sed -i '.sed' 's/"\/vgg_frontend"/"\/vff"/g'  $VGG_FACE_INSTALL_FOLDER/visorgen/vgg_frontend/visorgen/settings.py
sed -i '.sed' "s|/webapps|${VGG_FACE_INSTALL_FOLDER}|g" $VGG_FACE_INSTALL_FOLDER/visorgen/vgg_frontend/visorgen/settings.py
sed -i '.sed' "s|/webapps|${VGG_FACE_INSTALL_FOLDER}|g" $VGG_FACE_INSTALL_FOLDER/visorgen/vgg_frontend/scripts/*.sh

# configure default user in vgg_frontend
cd $VGG_FACE_INSTALL_FOLDER/visorgen/vgg_frontend/
python manage.py migrate
printf "import os\nfrom django.core.wsgi import get_wsgi_application\nos.environ['DJANGO_SETTINGS_MODULE']='visorgen.settings'\napplication = get_wsgi_application()\nfrom django.contrib.auth.models import User\nuser=User.objects.create_user('admin', password='vggadmin')\nuser.is_superuser=True\nuser.is_staff=True\nuser.save()" > super.py
python super.py
rm -f super.py

# add dylb paths to caffe and cuda library dependencies.
# If preferred, instead of modifying $HOME/.profile, the 'export' command should be executed before calling python in:
#    $VGG_FACE_SRC_FOLDER/service/start_backend_service.sh
#    $VGG_FACE_SRC_FOLDER/pipeline/start_pipeline.sh
echo "export DYLD_LIBRARY_PATH=$DYLD_LIBRARY_PATH:$CUDAHOME/lib:$VGG_FACE_INSTALL_FOLDER/visorgen/backend_dependencies/face-py-faster-rcnn/caffe-fast-rcnn/build/lib:$BREW_BOOST_ROOT/lib" >> $HOME/.profile
source $HOME/.profile
