#!/bin/bash

# - This script is to be run in a clean Ubuntu 16 LTS machine, by a sudoer user.
# - The directory /webapps/ should not exist
# - Note that a python virtual environment is created on /webapps/, so you need
#   to activate the environment before running the service
# - If you have a GPU and NVIDIA drivers in your PC, then PyTorch should support GPU automatically.
#   Otherwise, please refer to the PyTorch web page https://pytorch.org/ for specific installation instructions.

# update repositories
sudo apt-get update
sudo apt-get install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt-get update

# install apt-get dependencies
sudo apt-get install -y python-pip python3-pip
sudo apt-get install -y python-dev python3.6-dev
sudo apt-get install -y wget unzip cmake screen
sudo apt-get install -y memcached libevent-dev pkg-config
sudo apt-get install -y libz-dev libjpeg-dev libfreetype6-dev
sudo apt-get install -y openjdk-8-jdk ant
sudo apt-get install -y --no-install-recommends libboost-all-dev

# install virtualenv
sudo pip install configparser==4.0.2
sudo pip install virtualenv==20.0.7
pip install --upgrade pip
pip install zipp

# create main folder and virtualenv
sudo mkdir /webapps/
sudo chmod 777 /webapps/
mkdir /webapps/visorgen
mkdir /webapps/visorgen/backend_data /webapps/visorgen/backend_data/text
mkdir /webapps/visorgen/backend_data/text/images.index /webapps/visorgen/backend_data/text/text_detections
mkdir /webapps/visorgen/datasets  /webapps/visorgen/datasets/images/  /webapps/visorgen/datasets/images/mydataset
mkdir /webapps/visorgen/datasets/metadata/  /webapps/visorgen/datasets/metadata/mydataset
mkdir /webapps/visorgen/frontend_data  /webapps/visorgen/frontend_data/searchdata/ /webapps/visorgen/frontend_data/curatedtrainimgs
mkdir /webapps/visorgen/frontend_data/searchdata/classifiers
mkdir /webapps/visorgen/frontend_data/searchdata/postrainanno
mkdir /webapps/visorgen/frontend_data/searchdata/postrainfeats
mkdir /webapps/visorgen/frontend_data/searchdata/postrainimgs
mkdir /webapps/visorgen/frontend_data/searchdata/rankinglists
mkdir /webapps/visorgen/frontend_data/searchdata/uploadedimgs
mkdir /webapps/visorgen/backend_dependencies
cd /webapps/visorgen
virtualenv -p python3.6 .
source ./bin/activate

# download and setup vgg_text_search
wget https://gitlab.com/vgg/vgg_text_search/-/archive/master/vgg_text_search-master.zip -O /tmp/vgg_text_search.zip
unzip /tmp/vgg_text_search.zip -d /webapps/visorgen/
mv /webapps/visorgen/vgg_text_search*  /webapps/visorgen/vgg_text_search
sed -i "s|LUCENE_INDEX|LUCENE_INDEX = '/webapps/visorgen/backend_data/text/images.index' #|g" /webapps/visorgen/vgg_text_search/service/settings.py
sed -i "s|TEXT_RESULTS_DIR|TEXT_RESULTS_DIR = '/webapps/visorgen/backend_data/text/text_detections' #|g" /webapps/visorgen/vgg_text_search/service/settings.py
sed -i "s|DEPENDENCIES_PATH|DEPENDENCIES_PATH='/webapps/visorgen/backend_dependencies' #|g" /webapps/visorgen/vgg_text_search/service/settings.py
sed -i "s|ffmpeg|/webapps/visorgen/backend_dependencies/ffmpeg/ffmpeg|g" /webapps/visorgen/vgg_text_search/pipeline/start_pipeline.sh

# Install Yang Liu's Text-Detect-Recognize and download static ffmpeg
wget https://github.com/ox-vgg/Text-Detect-Recognize/archive/master.zip -O /tmp/text-detect-master.zip
unzip /tmp/text-detect-master.zip -d /webapps/visorgen/backend_dependencies/
mv /webapps/visorgen/backend_dependencies/Text-Detect-Recognize* /webapps/visorgen/backend_dependencies/Text-Detect-Recognize
rm -rf /webapps/visorgen/backend_dependencies/Text-Detect-Recognize/detection/pixel_link/pylib
wget https://github.com/dengdan/pylib/archive/python3.zip -O /tmp/pylib.zip
unzip /tmp/pylib.zip -d /webapps/visorgen/backend_dependencies/Text-Detect-Recognize/detection/pixel_link/
mv /webapps/visorgen/backend_dependencies/Text-Detect-Recognize/detection/pixel_link/pylib* /webapps/visorgen/backend_dependencies/Text-Detect-Recognize/detection/pixel_link/pylib
wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz -O /tmp/ffmpeg-release-amd64-static.tar.xz
tar -xf /tmp/ffmpeg-release-amd64-static.tar.xz -C /webapps/visorgen/backend_dependencies/
mv /webapps/visorgen/backend_dependencies/ffmpeg* /webapps/visorgen/backend_dependencies/ffmpeg

# download vgg_frontend repo
wget https://gitlab.com/vgg/vgg_frontend/-/archive/master/vgg_frontend-master.zip -O /tmp/vgg_frontend.zip
unzip /tmp/vgg_frontend.zip -d /webapps/visorgen/
mv /webapps/visorgen/vgg_frontend*  /webapps/visorgen/vgg_frontend

# Django dependencies
pip install django==1.10
pip install python-memcached

# frontend dependencies
pip install protobuf==3.0.0
pip install Pillow==6.1.0
pip install Whoosh==2.7.4
pip install simplejson==3.8.2

# vgg_img_downloader dependencies
pip install greenlet==0.4.15
pip install gevent==1.1.0
pip install Flask==0.10.1
pip install pyopenssl==17.5.0 pyasn1 ndg-httpsclient

# controller dependencies
pip install validictory==0.9.1
pip install msgpack-python==0.3.0
pip install requests==2.2.1
pip install pyzmq==17.1.2

# install python vgg_text_search additional dependencies
pip install tensorflow==1.1.0 setproctitle==1.1.10 matplotlib==3.1.1 opencv-python==4.1.1.26 cython==0.29.14 tqdm==4.37.0
pip install torch==1.1.0 torchvision==0.3.0
pip install scipy==1.1.0 imgaug==0.3.0 tensorboardx==1.9 editdistance==0.5.3

# download and install JCC and pylucene
wget https://archive.apache.org/dist/lucene/pylucene/pylucene-8.1.1-src.tar.gz -P /tmp
cd /tmp
tar -xvzf pylucene-8.1.1-src.tar.gz
cd /tmp/pylucene-8.1.1/jcc/
sed -i 's|java-8-oracle|java-8-openjdk-amd64|g' setup.py
python setup.py build
python setup.py install
cd /tmp/pylucene-8.1.1
sed -i 's|# Linux     (Debian Jessie 64-bit, Python 3.4.2|\nPREFIX_PYTHON=/webapps/visorgen\nANT=JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64 /usr/bin/ant\nPYTHON=$(PREFIX_PYTHON)/bin/python3\nJCC=$(PYTHON) -m jcc --shared\nNUM_FILES=10\n#|g' Makefile
make
make install

# Compile shot detector
cd /webapps/visorgen/vgg_text_search/pipeline
mkdir build
cd build
cmake -DBoost_INCLUDE_DIR=/usr/include/ ../
make

# remove all zips
rm -rf /tmp/*.zip
rm -rf /tmp/*.tar*
rm -rf /tmp/pylucene-8.1.1/

# configure vgg_frontend
echo '%45yak9wu56^(@un!b+&022fdr!-1@92_u*gctw*cw4*@hfu5t' > /webapps/visorgen/secret_key_visorgen
cp -f /webapps/visorgen/vgg_frontend/visorgen/settings_text.py /webapps/visorgen/vgg_frontend/visorgen/settings.py
cp -f /webapps/visorgen/vgg_frontend/siteroot/static/scripts/add-getting-started-lb-vts.js /webapps/visorgen/vgg_frontend/siteroot/static/scripts/add-getting-started-lb.js
sed -i 's/"\/vgg_frontend"/"\/vts"/g' /webapps/visorgen/vgg_frontend/visorgen/settings.py

# configure default user in vgg_frontend
cd /webapps/visorgen/vgg_frontend/
python manage.py migrate
printf "import os\nfrom django.core.wsgi import get_wsgi_application\nos.environ['DJANGO_SETTINGS_MODULE']='visorgen.settings'\napplication = get_wsgi_application()\nfrom django.contrib.auth.models import User\nuser=User.objects.create_user('admin', password='vggadmin')\nuser.is_superuser=True\nuser.is_staff=True\nuser.save()" > super.py
python super.py
rm -f super.py

# Download models from https://drive.google.com/drive/folders/1PuLCYVG457UOFzWHz4GuerTzWABZR0b6
# The contents of pixel_link_vgg_4s.zip should be unzip to:
#    /webapps/visorgen/backend_dependencies/Text-Detect-Recognize/detection/pixel_link/model
# The 0_480000.pth file should be copied to:
#    /webapps/visorgen/backend_dependencies/Text-Detect-Recognize/recognition/attention_net/model
