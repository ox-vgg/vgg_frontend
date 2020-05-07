@echo off

REM This batch file has been tested in a clean Windows10 PC. Before running it, you will need to perform a few preliminary
REM steps. You will need to download and install some software (if you don't already have it) and set some environment
REM variables (if you don't already have them set).
REM 1- Create the directory where you want the application to be deployed, and copy this file inside that folder.
REM    Let's call that folder the INSTALL_FOLDER.
REM 2- Download wget.exe (https://eternallybored.org/misc/wget/) and copy it inside INSTALL_FOLDER
REM 3- Make sure you have Python 3.7 x64 installed and that you can execute 'pip'.
REM    Here we assume Python 3.7 is installed C:\Python37\
REM 4- Install 'virtualenv', by entering 'pip install virtualenv' in the command line.
REM    You will need at least virtualenv 20.0.4.
REM 5- From that command prompt, go to the INSTALL_FOLDER and run this batch file. All other software will be download and setup for you.
REM    Note that a python virtual environment will be created inside INSTALL_FOLDER. You need to activate it before running the
REM    application, with:
REM        INSTALL_FOLDER\Scripts\activate
REM 6 -Start the application from the command line. Go to INSTALL_FOLDER\vgg_frontend\ and type:
REM        python manage.py runserver

REM create all subdirs
mkdir backend_data
mkdir backend_dependencies
mkdir datasets\images\mydataset
mkdir datasets\metadata\mydataset
mkdir frontend_data\curatedtrainimgs\display
mkdir frontend_data\searchdata\classifiers\display
mkdir frontend_data\searchdata\postrainanno\display
mkdir frontend_data\searchdata\postrainfeats\display
mkdir frontend_data\searchdata\predefined_rankinglists\display
mkdir frontend_data\searchdata\rankinglists\display
mkdir frontend_data\searchdata\uploadedimgs
mkdir tmp

REM Create virtual environment. Change the path to the Python executable if needed.
cd %~dp0
virtualenv -p C:\Python37\python.exe --prompt "(vgg_frontend) " .
call Scripts\activate

REM download and extract vgg_frontend
wget https://gitlab.com/vgg/vgg_frontend/-/archive/master/vgg_frontend-master.zip -O vgg_frontend.zip
powershell.exe -nologo -noprofile -command "& { Add-Type -A 'System.IO.Compression.FileSystem'; [IO.Compression.ZipFile]::ExtractToDirectory('vgg_frontend.zip', '.'); }"
move vgg_frontend-* vgg_frontend

REM Install vgg_frontend additional dependencies
pip install django==1.10
pip install protobuf==3.0.0
pip install Pillow==6.1.0
pip install simplejson==3.8.2

REM Install vgg_frontend controller additional dependencies
pip install validictory==0.9.1
pip install msgpack-python==0.3.0
pip install requests==2.2.1
pip install pyzmq==17.1.2
pip install Whoosh==2.7.4

REM delete all zips
del /Q *.zip

REM modify some vgg_frontend settings
cd %~dp0
powershell.exe -nologo -noprofile -command "$mod='BASE_DATA_DIR=''' + $pwd.Path + '''#';$mod=$mod -replace '\\','\\'; cat vgg_frontend\visorgen\settings_display.py | %%{$_ -replace 'BASE_DATA_DIR =', $mod } > vgg_frontend\visorgen\settings.replace.py"
copy /Y vgg_frontend\visorgen\settings.replace.py vgg_frontend\visorgen\settings_display.py
powershell.exe -nologo -noprofile -command "cat vgg_frontend\visorgen\settings_display.py | %%{$_ -replace 'memcached.MemcachedCache', 'filebased.FileBasedCache' } > vgg_frontend\visorgen\settings.replace.py"
copy /Y vgg_frontend\visorgen\settings.replace.py vgg_frontend\visorgen\settings_display.py
powershell.exe -nologo -noprofile -command "$mod=$pwd.Path+'\tmp';$mod=$mod -replace '\\','\\'; cat vgg_frontend\visorgen\settings_display.py | %%{$_ -replace '127.0.0.1:11211', $mod } > vgg_frontend\visorgen\settings.replace.py"
echo $path = "vgg_frontend\visorgen\settings.replace.py" > replaceends.ps1
echo (Get-Content $path -Raw).Replace("`r`n","`n") ^| Set-Content -NoNewline $path -Force >> replaceends.ps1
powershell.exe -nologo -noprofile -ExecutionPolicy ByPass -file replaceends.ps1
copy /Y vgg_frontend\visorgen\settings.replace.py vgg_frontend\visorgen\settings_display.py
copy /Y vgg_frontend\visorgen\settings_display.py vgg_frontend\visorgen\settings.py
del replaceends.ps1
del vgg_frontend\visorgen\settings.replace.py

REM create Django's secret key
echo %45yak9wu56^^(@un!b+^&022fdr!-1@92_u*gctw*cw4*@hfu5t > secret_key_visorgen

REM create default user in vgg_frontend
cd %~dp0
cd vgg_frontend
python manage.py migrate
cd ..
rmdir tmp
