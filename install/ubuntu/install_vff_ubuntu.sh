#!/bin/bash

# - This script is to be run in a clean Ubuntu 16 LTS machine, by a sudoer user.
# - The directory /webapps/ should not exist.
# - A python3 virtualenv is created in /webapps/visorgen/ which needs to be activated to run the application.
# - If you have a GPU and NVIDIA drivers in your PC, then PyTorch should support GPU automatically.
#   Otherwise, please refer to the PyTorch web page https://pytorch.org/ for specific installation instructions.
# - It creates one user for the Admin Tools: login/passwd --> admin/vggadmin
# - Start the application with /webapps/visorgen/vgg_frontend/scripts/ start_all_django.sh faces

# update repositories
sudo apt-get update

# install all apt-get dependencies
sudo apt-get install -y python-pip python3-pip
sudo apt-get install -y python-dev python3-dev
sudo apt-get install -y memcached libevent-dev pkg-config
sudo apt-get install -y libz-dev libjpeg-dev libfreetype6-dev
sudo apt-get install -y libzmq-dev wget unzip cmake screen
sudo apt-get install -y --no-install-recommends libboost-all-dev

# install virtualenv
sudo pip install configparser==4.0.2
sudo pip install virtualenv==20.0.7
pip install --upgrade pip
pip install zipp

# create main folders
sudo mkdir /webapps/
sudo chmod 777 /webapps/
mkdir /webapps/visorgen
mkdir /webapps/visorgen/backend_data /webapps/visorgen/backend_data/faces /webapps/visorgen/backend_data/faces/features
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
virtualenv -p python3 .
source ./bin/activate

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

# vgg_face_search dependencies
pip install torch==1.1.0
pip install PyWavelets==1.1.1
pip install torchvision==0.3.0
pip install scipy==1.2.0
pip install scikit-image==0.14.2
pip install matplotlib==2.1.0
pip install opencv-python==4.2.0.32

# download vgg_face_search repo
wget https://gitlab.com/vgg/vgg_face_search/-/archive/master/vgg_face_search-master.zip -O /tmp/vgg_face_search.zip
unzip /tmp/vgg_face_search.zip -d /webapps/visorgen/
mv /webapps/visorgen/vgg_face_search*  /webapps/visorgen/vgg_face_search

# download vgg_frontend repo
wget https://gitlab.com/vgg/vgg_frontend/-/archive/master/vgg_frontend-master.zip -O /tmp/vgg_frontend.zip
unzip /tmp/vgg_frontend.zip -d /webapps/visorgen/
mv /webapps/visorgen/vgg_frontend*  /webapps/visorgen/vgg_frontend

# download static ffmpeg
wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz -O /tmp/ffmpeg-release-amd64-static.tar.xz
tar -xf /tmp/ffmpeg-release-amd64-static.tar.xz -C /webapps/visorgen/backend_dependencies/
mv /webapps/visorgen/backend_dependencies/ffmpeg*  /webapps/visorgen/backend_dependencies/ffmpeg
sed -i "s|ffmpeg|/webapps/visorgen/backend_dependencies/ffmpeg/ffmpeg|g" /webapps/visorgen/vgg_face_search/pipeline/start_pipeline.sh

# download Pytorch_Retinaface (Dec 2019)
wget https://github.com/biubug6/Pytorch_Retinaface/archive/96b72093758eeaad985125237a2d9d34d28cf768.zip -P /tmp
unzip /tmp/96b72093758eeaad985125237a2d9d34d28cf768.zip -d /webapps/visorgen/backend_dependencies/
mv /webapps/visorgen/backend_dependencies/Pytorch_Retinaface* /webapps/visorgen/backend_dependencies/Pytorch_Retinaface
mkdir /webapps/visorgen/backend_dependencies/Pytorch_Retinaface/weights

# download models
wget http://www.robots.ox.ac.uk/~vgg/data/vgg_face2/models/pytorch/senet50_256_pytorch.tar.gz -P /tmp/
tar -xvzf /tmp/senet50_256_pytorch.tar.gz -C /webapps/visorgen/backend_data/faces/
cd /webapps/visorgen/backend_dependencies/Pytorch_Retinaface/weights
wget http://www.robots.ox.ac.uk/~vgg/software/vff/downloads/models/Pytorch_Retinaface/Resnet50_Final.pth

# compile shot detector
cd /webapps/visorgen/vgg_face_search/pipeline
mkdir build
cd build
cmake -DBoost_INCLUDE_DIR=/usr/include/ ../
make

# configure vgg_face_search
sed -i "s|DATASET_FEATS_FILE|DATASET_FEATS_FILE='/webapps/visorgen/backend_data/faces/features/database.pkl'#|g" /webapps/visorgen/vgg_face_search/service/settings.py
sed -i "s|DEPENDENCIES_PATH|DEPENDENCIES_PATH='/webapps/visorgen/backend_dependencies/'#|g" /webapps/visorgen/vgg_face_search/service/settings.py
sed -i "s|FEATURES_MODEL_WEIGHTS|FEATURES_MODEL_WEIGHTS ='/webapps/visorgen/backend_data/faces/senet50_256.pth'#|g" /webapps/visorgen/vgg_face_search/service/settings.py
sed -i "s|FEATURES_MODEL_DEF|FEATURES_MODEL_DEF ='/webapps/visorgen/backend_data/faces/senet50_256.py'#|g" /webapps/visorgen/vgg_face_search/service/settings.py
sed -i "s|FACE_DETECTION_MODEL|FACE_DETECTION_MODEL ='/webapps/visorgen/backend_dependencies/Pytorch_Retinaface/weights/Resnet50_Final.pth'#|g" /webapps/visorgen/vgg_face_search/service/settings.py
IS_CUDA_AVAILABLE=$(python -c "import torch; print(str(torch.cuda.is_available()))")
sed -i "s|CUDA_ENABLED|CUDA_ENABLED = ${IS_CUDA_AVAILABLE}#|g" /webapps/visorgen/vgg_face_search/service/settings.py
cd /webapps/visorgen/backend_dependencies/Pytorch_Retinaface/
python -c "from models.retinaface import RetinaFace; from data import cfg_re50; RetinaFace(cfg=cfg_re50, phase = 'test')"

# configure vgg_frontend
echo '%45yak9wu56^(@un!b+&022fdr!-1@92_u*gctw*cw4*@hfu5t' > /webapps/visorgen/secret_key_visorgen
cp -f /webapps/visorgen/vgg_frontend/visorgen/settings_faces.py /webapps/visorgen/vgg_frontend/visorgen/settings.py
cp -f /webapps/visorgen/vgg_frontend/siteroot/static/scripts/add-getting-started-lb-vff.js /webapps/visorgen/vgg_frontend/siteroot/static/scripts/add-getting-started-lb.js
sed -i 's/"\/vgg_frontend"/"\/vff"/g' /webapps/visorgen/vgg_frontend/visorgen/settings.py

# configure default user in vgg_frontend
cd /webapps/visorgen/vgg_frontend/
python manage.py migrate
printf "import os\nfrom django.core.wsgi import get_wsgi_application\nos.environ['DJANGO_SETTINGS_MODULE']='visorgen.settings'\napplication = get_wsgi_application()\nfrom django.contrib.auth.models import User\nuser=User.objects.create_user('admin', password='vggadmin')\nuser.is_superuser=True\nuser.is_staff=True\nuser.save()" > super.py
python super.py
rm -f super.py

