Deployment scripts and usage
============================

These scripts are meant for local deployment on your computer of the applications listed here. This means that they will download and install third-party software and data in your computer, as well as compile and configure source code. The scripts are experimental and are intended for **Software Developers**. Regular users are strongly advised to use the docker version of the applications listed here to install them on their computers.

In all cases, you will need a C++ compiler and Python 2.7 installed on your system. For GPU support you will need the NVIDIA drivers and the CUDA Toolkit in your system. Please be aware that the scripts for GPU might fail depending on your particular CUDA setup (version, location of the CUDA library in your system, etc.). cuDNN is not used anywhere so if you want, for instance, Caffe with cuDNN, you will need to reconfigure and recompile Caffe by yourself.

All scripts contain requirements and some instructions at the beginning of the file. Please read them before attempting the deployment.

All scripts create a default 'admin' user in the system. Check the last lines of the scripts for the password.

Applications
------------

#### *VGG Image Classification (VIC) engine*

`VIC` is a combination of the code in this repository and [vgg_classifier](https://gitlab.com/vgg/vgg_classifier).

`VIC` is an application that serves as a web engine to perform image classification queries over an user-defined image dataset. More detailed information can be found at <http://www.robots.ox.ac.uk/~vgg/software/vic/>.

Deployment scripts are provided for macOS High Sierra 10.13.3 and Ubuntu 16, with or without GPU support.

#### *VGG Face Finder (VFF) engine*

`VFF` is a combination of the code in this repository and [vgg_face_search](https://gitlab.com/vgg/vgg_face_search).

`VFF` is an application that serves as a web engine to perform queries over an user-defined image dataset with faces. More detailed information can be found at <http://www.robots.ox.ac.uk/~vgg/software/vff/>.

Deployment scripts are provided for macOS High Sierra 10.13.3, Ubuntu 16 and Windows10 x64; with or without GPU support.

The GPU version uses [face-py-faster-rcnn](https://github.com/playerkk/face-py-faster-rcnn/) for the face detection, while the CPU-only version uses [facenet](https://github.com/davidsandberg/facenet/).

For Windows, none of these detectors are supported and instead the standard frontal-face detector of [Dlib](http://dlib.net/imaging.html) is used. You can easily change the code in `vgg_face_search\service\face_detection_dlib.py` to use Dlib's `cnn_face_detector` to get better results. In such a case, GPU support would be useful, so you will need to compile Dlib with GPU support.

#### *`vgg_frontend` for Display*


The scripts will deploy the code in this repository without any backend engine. It can be used to retrieve a pre-defined list of images associated with a text string.

Deployment scripts are provided for macOS High Sierra 10.13.3, Ubuntu 16 and Windows10 x64.

Configuration
-------------

If you have executed one of the scripts in the `install` folder, the application you chose should have been deployed either in `/webapps/` or at `$HOME` or at a directory of your choosing, let's hereby call that directory `MY_FOLDER`.

The main configuration file for the frontend is `MY_FOLDER/visorgen/vgg_frontend/visorgen/settings.py`, which contains a set of variables. You should have no need to change these variables unless you want to customize the application. **Be sure you know what you are doing** before changing the settings.

You can also change *some* configuration from the administration tools, see the next section.

Usage Instructions
------------------

#### *Starting the application*

Open a terminal and go to the `MY_FOLDER/visorgen/vgg_frontend/` folder, then enter the command:

	python manage.py runserver

to start the Django server. By default, the server will start at `http://127.0.0.1:8000/vgg_frontend`. Open an Internet browser and visit that URL. If you have started the installed search-engine backend manually (for `VIC` and `VFF`), you will be able to see the main page of the application.

However, if you see a message "Attempting to reconnect to backend...", then the application cannot contact the installed search-engine backend. In such a case, use your Internet browser to visit `http://127.0.0.1:8000/vgg_frontend/admintools`. You will be asked for login credentials. Please enter the 'admin' credentials created with the scripts above, and you will be redirected to the administration tools page.

In the administration tools, visit the `Manage Backend Service tab`, select the engine you want to start and press the `Start` button. You will see a message and then you will be redirected back to the administration tools page. Click on the `Home` link at the top left corner of the page to go back to the homepage. If the backend was successfully started, you will be able to see the home page of the application.

In the bottom-left corner of the home page, you will see a `Getting Started` link. Click on it and read through the explanation on how to use the web application.

#### *Stopping the application*

In order to stop the application, **stop the search-engine backend before stopping `vgg_frontend`**. In the administration tools, visit the `Manage Backend Service tab`, select the engine you want to stop and press the `Stop` button.

After this, just interrupt the Django server. In macOS/Linux this can be done simply with Control+C. In Windows, use Control+Break.

After stopping the application, any configuration changes you have done in the `Global Server Configuration tab` will be lost. However, all your cached text queries will be available the next time you start the application.
