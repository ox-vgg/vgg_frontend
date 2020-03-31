@echo off

REM This batch file has been tested in a clean Windows10 PC. Before running it, you will need to perform a few preliminary
REM steps. You will need to download and install some software (if you don't already have it) and set some environment
REM variables (if you don't already have them set).
REM 1- Create the directory where you want the application to be deployed, and copy this file inside that folder.
REM    Let's call that folder the INSTALL_FOLDER.
REM 2- Download wget.exe (https://eternallybored.org/misc/wget/) and copy it inside INSTALL_FOLDER
REM 3- Make sure you have Python 3.7 x64 installed and that you can execute 'pip'.
REM    Here we assume Python 3.7 is installed C:\Python37\
REM 4- Install 'virtualenv', by entering 'pip install virtualenv' in the command line
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

REM Create virtual environment. Change the path to the Python executable if needed.
cd %~dp0
virtualenv -p C:\Python37\python.exe --prompt "(vff) " .
call Scripts\activate

REM download and extract vgg_frontend
wget https://gitlab.com/vgg/vgg_frontend/-/archive/master/vgg_frontend-master.zip -O vgg_frontend.zip
powershell.exe -nologo -noprofile -command "& { Add-Type -A 'System.IO.Compression.FileSystem'; [IO.Compression.ZipFile]::ExtractToDirectory('vgg_frontend.zip', '.'); }"
move vgg_frontend-* vgg_frontend

REM download and extract vgg_face_search
wget https://gitlab.com/vgg/vgg_face_search/-/archive/master/vgg_face_search-master.zip -O vgg_face_search.zip
powershell.exe -nologo -noprofile -command "& { Add-Type -A 'System.IO.Compression.FileSystem'; [IO.Compression.ZipFile]::ExtractToDirectory('vgg_face_search.zip', '.'); }"
move vgg_face_search-* vgg_face_search

REM download Pytorch_Retinaface (Dec 2019)
wget https://github.com/biubug6/Pytorch_Retinaface/archive/96b72093758eeaad985125237a2d9d34d28cf768.zip -O Pytorch_Retinaface.zip
powershell.exe -nologo -noprofile -command "& { Add-Type -A 'System.IO.Compression.FileSystem'; [IO.Compression.ZipFile]::ExtractToDirectory('Pytorch_Retinaface.zip', '.'); }"
move Pytorch_Retinaface-* backend_dependencies\Pytorch_Retinaface
mkdir  backend_dependencies\Pytorch_Retinaface\weights

REM download models
wget http://www.robots.ox.ac.uk/~vgg/software/vff/downloads/models/senet50_256_pytorch.zip
powershell.exe -nologo -noprofile -command "& { Add-Type -A 'System.IO.Compression.FileSystem'; [IO.Compression.ZipFile]::ExtractToDirectory('senet50_256_pytorch.zip', 'backend_data\faces\'); }"
wget http://www.robots.ox.ac.uk/~vgg/software/vff/downloads/models/Pytorch_Retinaface/Resnet50_Final.pth -O backend_dependencies\Pytorch_Retinaface\weights\Resnet50_Final.pth

REM Download ffmpeg
wget https://ffmpeg.zeranoe.com/builds/win64/static/ffmpeg-4.1.1-win64-static.zip
powershell.exe -nologo -noprofile -command "& { Add-Type -A 'System.IO.Compression.FileSystem'; [IO.Compression.ZipFile]::ExtractToDirectory('ffmpeg-4.1.1-win64-static.zip', 'backend_dependencies'); }"
move backend_dependencies\ffmpeg-* backend_dependencies\ffmpeg
powershell.exe -nologo -noprofile -command "$mod='""'+$pwd.Path+'\backend_dependencies\ffmpeg\bin\ffmpeg"';$mod=$mod+'"""'; cat vgg_face_search\pipeline\start_pipeline.bat | %%{$_ -replace 'ffmpeg', $mod } | Out-File -encoding ascii vgg_face_search\pipeline\start_pipeline.replace.bat"
copy /Y vgg_face_search\pipeline\start_pipeline.replace.bat vgg_face_search\pipeline\start_pipeline.bat
del vgg_face_search\pipeline\start_pipeline.replace.bat

REM Django dependencies
pip install django==1.10
pip install python-memcached

REM frontend dependencies
pip install protobuf==3.0.0
pip install Pillow==6.1.0
pip install Whoosh==2.7.4
pip install simplejson==3.8.2

REM vgg_img_downloader dependencies
pip install greenlet==0.4.15
pip install gevent==1.3.0
pip install Flask==0.10.1
pip install pyopenssl==17.5.0 pyasn1 ndg-httpsclient

REM controller dependencies
pip install validictory==0.9.1
pip install msgpack-python==0.3.0
pip install requests==2.2.1
pip install pyzmq==17.1.2

REM vgg_face_search dependencies
REM Note that torch is installed for CPU only !!!
pip install https://download.pytorch.org/whl/cpu/torch-1.1.0-cp37-cp37m-win_amd64.whl
pip install PyWavelets==1.1.1
pip install https://download.pytorch.org/whl/cpu/torchvision-0.3.0-cp37-cp37m-win_amd64.whl
pip install https://3f23b170c54c2533c070-1c8a9b3114517dc5fe17b7c3f8c63a43.ssl.cf2.rackcdn.com/scipy-1.2.0-cp37-cp37m-win_amd64.whl
pip install scikit-image==0.14.2
pip install opencv-python==4.2.0.32
pip install matplotlib==2.2.2

REM delete all zips
del /Q *.zip
del /Q *.gz

REM modify some vgg_face_search settings
REM Note that the CUDA_ENABLED setting is not changed !.
cd %~dp0
powershell.exe -nologo -noprofile -command "$mod='DEPENDENCIES_PATH=''' + $pwd.Path + '\backend_dependencies''#';$mod=$mod -replace '\\','\\'; cat vgg_face_search\service\settings.py | %%{$_ -replace 'DEPENDENCIES_PATH', $mod } > vgg_face_search\service\settings.replace.py"
copy /Y vgg_face_search\service\settings.replace.py vgg_face_search\service\settings.py
powershell.exe -nologo -noprofile -command "$mod='DATASET_FEATS_FILE=''' + $pwd.Path + '\backend_data\faces\features\database.pkl''#';$mod=$mod -replace '\\','\\'; cat vgg_face_search\service\settings.py | %%{$_ -replace 'DATASET_FEATS_FILE', $mod } > vgg_face_search\service\settings.replace.py"
copy /Y vgg_face_search\service\settings.replace.py vgg_face_search\service\settings.py
powershell.exe -nologo -noprofile -command "$mod='FEATURES_MODEL_WEIGHTS=''' + $pwd.Path + '\backend_data\faces\senet50_256.pth''#';$mod=$mod -replace '\\','\\'; cat vgg_face_search\service\settings.py | %%{$_ -replace 'FEATURES_MODEL_WEIGHTS', $mod } > vgg_face_search\service\settings.replace.py"
copy /Y vgg_face_search\service\settings.replace.py vgg_face_search\service\settings.py
powershell.exe -nologo -noprofile -command "$mod='FEATURES_MODEL_DEF=''' + $pwd.Path + '\backend_data\faces\senet50_256.py''#';$mod=$mod -replace '\\','\\'; cat vgg_face_search\service\settings.py | %%{$_ -replace 'FEATURES_MODEL_DEF', $mod } > vgg_face_search\service\settings.replace.py"
copy /Y vgg_face_search\service\settings.replace.py vgg_face_search\service\settings.py
powershell.exe -nologo -noprofile -command "$mod='FACE_DETECTION_MODEL=''' + $pwd.Path + '\backend_dependencies\Pytorch_Retinaface\weights\Resnet50_Final.pth''#';$mod=$mod -replace '\\','\\'; cat vgg_face_search\service\settings.py | %%{$_ -replace 'FACE_DETECTION_MODEL', $mod } > vgg_face_search\service\settings.replace.py"
copy /Y vgg_face_search\service\settings.replace.py vgg_face_search\service\settings.py
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
cd ..
rmdir tmp
