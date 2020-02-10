@echo off

REM This batch file has been tested in a clean Windows10 PC. Before running it, you will need to perform a few preliminary
REM steps. You will need to download and install some software (if you don't already have it) and set some environment
REM variables (if you don't already have them set).
REM 1- Create the directory where you want the application to be deployed, and copy this file inside that folder.
REM    Let's call that folder the INSTALL_FOLDER.
REM 2- Download wget.exe (https://eternallybored.org/misc/wget/) and copy it inside INSTALL_FOLDER
REM 3- Make sure you have Python 2.7 x64 installed and that you can execute 'pip' and 'easy_install' from the command line
REM 4- Install 'virtualenv', by entering 'pip install virtualenv' in the command line
REM 5- Install CMake and make sure you can access it from the command line
REM 6- Install Microsoft Visual C++ Compiler for Python 2.7
REM 7- The installation of DLib will most likely require compilation, and you will need a more modern compile, so please
REM    install the Visual C++ 2017 Build Tools (https://www.visualstudio.com/downloads/#build-tools-for-visual-studio-2017).
REM    Note that you only need the "Visual C++ build tools" regardless of all the other software offered by the installer.
REM 8- Start the x64 command prompt created by the Visual Studio installer, it should be called something like, for instance:
REM        x64 Native Tools Command Prompt for VS 2017
REM 9- From that command prompt, go to the INSTALL_FOLDER and run this batch file. All software will be download and setup for you.
REM    Note that a python virtual environment will be created inside INSTALL_FOLDER. You need to activate it before running the
REM    application, with:
REM        INSTALL_FOLDER\Scripts\activate
REM 10-Start the application from the command line. Go to INSTALL_FOLDER\vgg_frontend\ and type:
REM        python manage.py runserver

REM create all subdirs
mkdir backend_data\faces\features
mkdir backend_dependencies
mkdir datasets\images\mydataset
mkdir datasets\metadata\mydataset
mkdir frontend_data\curatedtrainimgs\faces
mkdir frontend_data\searchdata\classifiers\faces
mkdir frontend_data\searchdata\postrainanno\faces
mkdir frontend_data\searchdata\postrainfeats\faces
mkdir frontend_data\searchdata\predefined_rankinglists\faces
mkdir frontend_data\searchdata\rankinglists\faces
mkdir frontend_data\searchdata\uploadedimgs
mkdir tmp

REM download and extract vgg_frontend
wget https://gitlab.com/vgg/vgg_frontend/-/archive/master/vgg_frontend-master.zip -O vgg_frontend.zip
powershell.exe -nologo -noprofile -command "& { Add-Type -A 'System.IO.Compression.FileSystem'; [IO.Compression.ZipFile]::ExtractToDirectory('vgg_frontend.zip', '.'); }"
move vgg_frontend-* vgg_frontend

REM download and extract vgg_face_search
wget https://gitlab.com/vgg/vgg_face_search/-/archive/master/vgg_face_search-master.zip -O vgg_face_search.zip
powershell.exe -nologo -noprofile -command "& { Add-Type -A 'System.IO.Compression.FileSystem'; [IO.Compression.ZipFile]::ExtractToDirectory('vgg_face_search.zip', '.'); }"
move vgg_face_search-* vgg_face_search

REM Download models
wget http://www.robots.ox.ac.uk/~vgg/data/vgg_face2/256/resnet50_256.caffemodel -O resnet50_256.caffemodel
wget http://www.robots.ox.ac.uk/~vgg/data/vgg_face2/256/resnet50_256.prototxt -O resnet50_256.prototxt
move resnet50_256.caffemodel backend_data\faces\
move resnet50_256.prototxt backend_data\faces\

REM Download ffmpeg
wget https://ffmpeg.zeranoe.com/builds/win64/static/ffmpeg-4.1.1-win64-static.zip
powershell.exe -nologo -noprofile -command "& { Add-Type -A 'System.IO.Compression.FileSystem'; [IO.Compression.ZipFile]::ExtractToDirectory('ffmpeg-4.1.1-win64-static.zip', 'backend_dependencies'); }"
move backend_dependencies\ffmpeg-* backend_dependencies\ffmpeg
powershell.exe -nologo -noprofile -command "$mod='""'+$pwd.Path+'\backend_dependencies\ffmpeg\bin\ffmpeg"';$mod=$mod+'"""'; cat vgg_face_search\pipeline\start_pipeline.bat | %%{$_ -replace 'ffmpeg', $mod } | Out-File -encoding ascii vgg_face_search\pipeline\start_pipeline.replace.bat"
copy /Y vgg_face_search\pipeline\start_pipeline.replace.bat vgg_face_search\pipeline\start_pipeline.bat
del vgg_face_search\pipeline\start_pipeline.replace.bat

REM Create virtual environment
cd %~dp0
virtualenv .
call Scripts\activate

REM Install vgg_face_search dependencies
pip install setuptools==39.1.0
pip install simplejson==3.8.2
pip install Pillow==2.3.0
pip install numpy==1.14.0
pip install Cython==0.27.3
pip install matplotlib==2.1.0
pip install scipy==1.0.1
pip install protobuf==3.0.0
REM Download stdint.h, see https://stackoverflow.com/questions/44865576/python-scikit-image-install-failing-using-pip
wget https://raw.githubusercontent.com/mattn/gntp-send/master/include/msinttypes/stdint.h -O "%LOCALAPPDATA%\Programs\Common\Microsoft\Visual C++ for Python\9.0\VC\include\stdint.h"
pip install scikit-image==0.13.1
pip install easydict==1.7
pip install dlib==19.9.0

REM Install vgg_frontend additional dependencies
pip install django==1.10

REM Install vgg_img_downloader additional dependencies
pip install greenlet==0.4.10
pip install gevent==0.13.8
pip install Flask==0.10.1
pip install pyopenssl==17.5.0 pyasn1 ndg-httpsclient

REM Install vgg_frontend controller additional dependencies
pip install validictory==0.9.1
pip install msgpack-python==0.3.0
pip install requests==1.1.0
easy_install https://pypi.python.org/packages/02/91/553f174f52190474cb10061d7a451fb274fac78f1ff52ad5f64731206ce7/pyzmq-2.2.0-py2.7-win-amd64.egg
pip install gevent-zeromq==0.2.5
pip install Whoosh==2.7.4

REM Download static caffe for windows (Release version, CPU only, Python 2.7) from https://github.com/BVLC/caffe/tree/windows
wget "https://github.com/Coderx7/Caffe_1.0_Windows/releases/download/caffe_1.0_windows/caffe_cpu_x64_MSVC14_Py27_release.zip" -O caffe.zip
powershell.exe -nologo -noprofile -command "& { Add-Type -A 'System.IO.Compression.FileSystem'; [IO.Compression.ZipFile]::ExtractToDirectory('caffe.zip', 'backend_dependencies\caffe'); }"

REM delete all zips
del /Q *.zip

REM modify some vgg_face_search settings
cd %~dp0
powershell.exe -nologo -noprofile -command "$mod='DEPENDENCIES_PATH=''' + $pwd.Path + '\backend_dependencies''#';$mod=$mod -replace '\\','\\'; cat vgg_face_search\service\settings.py | %%{$_ -replace 'DEPENDENCIES_PATH', $mod } > vgg_face_search\service\settings.replace.py"
copy /Y vgg_face_search\service\settings.replace.py vgg_face_search\service\settings.py
powershell.exe -nologo -noprofile -command "cat vgg_face_search\service\settings.py | %%{$_ -replace 'GPU_FACE_DETECTION_CAFFE_MODEL', '#GPU_FACE_DETECTION_CAFFE_MODEL' } > vgg_face_search\service\settings.replace.py"
copy /Y vgg_face_search\service\settings.replace.py vgg_face_search\service\settings.py
powershell.exe -nologo -noprofile -command "$mod='DATASET_FEATS_FILE=''' + $pwd.Path + '\backend_data\faces\features\database.pkl''#';$mod=$mod -replace '\\','\\'; cat vgg_face_search\service\settings.py | %%{$_ -replace 'DATASET_FEATS_FILE', $mod } > vgg_face_search\service\settings.replace.py"
copy /Y vgg_face_search\service\settings.replace.py vgg_face_search\service\settings.py
powershell.exe -nologo -noprofile -command "$mod='FEATURES_CAFFE_MODEL=''' + $pwd.Path + '\backend_data\faces\resnet50_256.caffemodel''#';$mod=$mod -replace '\\','\\'; cat vgg_face_search\service\settings.py | %%{$_ -replace 'FEATURES_CAFFE_MODEL', $mod } > vgg_face_search\service\settings.replace.py"
copy /Y vgg_face_search\service\settings.replace.py vgg_face_search\service\settings.py
powershell.exe -nologo -noprofile -command "$mod='FEATURES_CAFFE_PROTOTXT=''' + $pwd.Path + '\backend_data\faces\resnet50_256.prototxt''#';$mod=$mod -replace '\\','\\'; cat vgg_face_search\service\settings.py | %%{$_ -replace 'FEATURES_CAFFE_PROTOTXT', $mod } > vgg_face_search\service\settings.replace.py"
echo $path = "vgg_face_search\service\settings.replace.py" > replaceends.ps1
echo (Get-Content $path -Raw).Replace("`r`n","`n") ^| Set-Content -NoNewline $path -Force >> replaceends.ps1
powershell.exe -nologo -noprofile -ExecutionPolicy ByPass -file replaceends.ps1
copy /Y vgg_face_search\service\settings.replace.py vgg_face_search\service\settings.py
del replaceends.ps1
del vgg_face_search\service\settings.replace.py

REM modify some vgg_frontend settings
cd %~dp0
powershell.exe -nologo -noprofile -command "$mod='BASE_DATA_DIR=''' + $pwd.Path + '''#';$mod=$mod -replace '\\','\\'; cat vgg_frontend\visorgen\settings_faces.py | %%{$_ -replace 'BASE_DATA_DIR =', $mod } > vgg_frontend\visorgen\settings.replace.py"
copy /Y vgg_frontend\visorgen\settings.replace.py vgg_frontend\visorgen\settings_faces.py
powershell.exe -nologo -noprofile -command "cat vgg_frontend\visorgen\settings_faces.py | %%{$_ -replace '/vgg_frontend', '/vff' } > vgg_frontend\visorgen\settings.replace.py"
copy /Y vgg_frontend\visorgen\settings.replace.py vgg_frontend\visorgen\settings_faces.py
powershell.exe -nologo -noprofile -command "cat vgg_frontend\visorgen\settings_faces.py | %%{$_ -replace 'memcached.MemcachedCache', 'filebased.FileBasedCache' } > vgg_frontend\visorgen\settings.replace.py"
copy /Y vgg_frontend\visorgen\settings.replace.py vgg_frontend\visorgen\settings_faces.py
powershell.exe -nologo -noprofile -command "$mod=$pwd.Path+'\tmp';$mod=$mod -replace '\\','\\'; cat vgg_frontend\visorgen\settings_faces.py | %%{$_ -replace '127.0.0.1:11211', $mod } > vgg_frontend\visorgen\settings.replace.py"
echo $path = "vgg_frontend\visorgen\settings.replace.py" > replaceends.ps1
echo (Get-Content $path -Raw).Replace("`r`n","`n") ^| Set-Content -NoNewline $path -Force >> replaceends.ps1
powershell.exe -nologo -noprofile -ExecutionPolicy ByPass -file replaceends.ps1
copy /Y vgg_frontend\visorgen\settings.replace.py vgg_frontend\visorgen\settings_faces.py
copy /Y vgg_frontend\visorgen\settings_faces.py vgg_frontend\visorgen\settings.py
copy /Y vgg_frontend\siteroot\static\scripts\add-getting-started-lb-vff.js vgg_frontend\siteroot\static\scripts\add-getting-started-lb.js
del replaceends.ps1
del vgg_frontend\visorgen\settings.replace.py

REM create Django's secret key
echo %45yak9wu56^^(@un!b+^&022fdr!-1@92_u*gctw*cw4*@hfu5t > secret_key_visorgen

REM create default user in vgg_frontend
cd %~dp0
cd vgg_frontend
python manage.py migrate
echo import os > super.py
echo from django.core.wsgi import get_wsgi_application >> super.py
echo os.environ['DJANGO_SETTINGS_MODULE']='visorgen.settings' >> super.py
echo application=get_wsgi_application() >> super.py
echo from django.contrib.auth.models import User >> super.py
echo user=User.objects.create_user('admin',password='vggadmin') >> super.py
(echo user.is_superuser=True && echo.user.is_staff=True) >> super.py
echo user.save() >> super.py
python super.py
del super.py
