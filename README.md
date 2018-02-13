vgg_frontend application
========================

Author:

 + Ernesto Coto, University of Oxford – <ecoto@robots.ox.ac.uk>

License: BSD (see LICENSE.md)

`vgg_frontend` is a web application that serves as a generic web engine to perform visual searches over an image dataset. It is based on the original application created by the [VGG](http://www.robots.ox.ac.uk/~vgg/) group at the [University of Oxford](http://www.ox.ac.uk/), to perform visual searchers over a large dataset of images from [BBC News](http://www.robots.ox.ac.uk/~vgg/research/on-the-fly/).

It consists of two main components:

 + An image downloading service, included in this repository in the `vgg_img_downloader` folder.
 + The web frontend, also included in this repository, as a [Django](https://www.djangoproject.com/) project.

Now, `vgg_frontend` will work with the two previous components, but to make it really functional it needs to be used with **at least ONE image backend engine**. It is the backend engine who actually processes the images in the user's dataset. `vgg_frontend` servers as the web user interface for the backend engine.

The application in this repository comes pre-configured for either one of two backend engines: one `category` backend engine, and one `text` backend engine.

More details about the two components of `vgg_frontend` and the backend engines is presented below.

#### *The image downloading service*

Located in folder `vgg_img_downloader`, it corresponds to a reduced version of the tool created by [Ken Chatfield](https://github.com/kencoken/imsearch-tools). The version provided in this repository includes only the `google_web` image downloading engine, which does not require any specific configuration and hence can be used by anyone. Should you need more image downloading engines (e.g. downloading from Bing or Flick), please use the original version and supply your own API keys, depending on which image provider you wish to use.

#### *The web frontend*

The web frontend has been developed using **Django version 1.10**, under **Ubuntu 14.04.5 LTS**. The provided version runs in DEBUG mode. Should you wish to deploy it to a production environment, please refer to [Django's documentation](https://docs.djangoproject.com/en/1.10/howto/deployment/).

The following sections describe how to install and configure the `vgg_frontend` application to work with the aforementioned backend engines.

Docker Installation
-------------------

Installation via docker technology is possible, but only if the `category` backend engine is going to be used. The `vgg_frontend` with the `category` engine is what we call the `VGG Image Classification (VIC) engine`. You can read more about it in the corresponding [VGG page](http://www.robots.ox.ac.uk/~vgg/software/vic/).

All you need to do is to use the docker service installed on your PC to download the image, by entering the following command:

	docker pull registry.gitlab.com/vgg/vgg_frontend/vic

Alternatively, build the image using the Dockerfile at `Dockerfiles/vic`.

The downloaded (or built) docker image contains the code in this repository along with the actual [image classification backend](https://gitlab.com/vgg/vgg_classifier), but it does not contain any image dataset or preprocessed data, which have to be provided separately.

Usage instructions, along with sample data files for `VIC`, can be found at the [Docker deployment](http://www.robots.ox.ac.uk/~vgg/software/vic/#docker_version) section on [VIC's VGG page](http://www.robots.ox.ac.uk/~vgg/software/vic/).

Native Installation
-------------------

Download the script `install_ubuntu.sh` located in the `install` folder and run it in your computer (**Ubuntu 14.04.5 LTS**) using a sudoer user. The script will automatically download all necessary dependencies and copy the application in the `/webapps/visorgen/` folder.

Should you wish to install the application on a different folder, you will still find `install_ubuntu.sh` useful. The script shows you the libraries (and their versions) that are required to run the application. Follow the script carefully adapting each command to your needs.

There is also an experimental installer for macOS Sierra in `install_macos.sh`. Instead of running the full script, you might want to open it in a text editor and run one instruction at a time. The script installs the application in the `/$HOME/visorgen/` folder.

One additional step you need to do is to generate a [secret key](https://docs.djangoproject.com/en/1.10/ref/settings/#std:setting-SECRET_KEY). There are many websites that will allow you to generate a new key for Django, including [django-generate-secret-key](https://pypi.python.org/pypi/django-generate-secret-key/1.0.2). Once you have managed to generate the key, you need to store it the text file `/webapps/visorgen/secret_key_visorgen`. **This a requirement from Django which cannot be avoided, so the application will not start until the key is set in the file**.

#### *Dataset*

In you have executed the script, there should be a `/webapps/visorgen/datasets/images/mydataset` folder and a `/webapps/visorgen/datasets/metadata/mydataset` folder in your computer. Please check these folders were created.

Copy the images of your dataset to `/webapps/visorgen/datasets/images/mydataset`. The organization of your files inside this folder can include subdirectories, if necessary.

Create a CSV file of [Comma-separated values](https://en.wikipedia.org/wiki/Comma-separated_values) called `metadata.csv` and copy it to `/webapps/visorgen/datasets/metadata/mydataset`. Each line in the file will correspond to the metadata of one of your image files. The structure of the CSV is explained below. If you do not have any metadata for your images, the Visual Search application will simply not shown any metadata information when displaying your images, but it will still work.

#### *Metadata Structure*

Each line of the CSV file corresponds to a series of text strings, separated from each other by a comma (`,`) character. This kind of file can be created/edited with almost any modern spreadsheet application (MS Excel, LibreOffice Calc, etc.), therefore each line of the CSV corresponds to a `row` of the spreadsheet, and each text string corresponds to a value of a `cell` in the spreadsheet.

The CSV should have at least two columns. The first column should ALWAYS contain the path to the image, relative to the `/webapps/visorgen/datasets/images/mydataset` folder. The second column should contain a short string (less than 20 characters) describing the image. More columns with information can follow, at your discretion. For instance, if your image folder contains only two files called: `IMG_0000.JPG` and `IMG_0001.JPG`; the `metadata.csv` could look like this:

```
IMG_0000.JPG,1st Image,more_metadata_for_the_first_image
IMG_0001.JPG,2nd Image,more_metadata_for_the_second_image
```

The short description (2nd column) will show up at the bottom of the image in the list of results for a query. The third column will only be visible in the details page of each image.

If your images are stored within a subfolder of the image folder, such as: `dir1/IMG_0000.JPG` and `dir2/IMG_0001.JPG`, the content of `metadata.csv` should be:

```
dir1/IMG_0000.JPG,1st Image,more_metadata_for_the_first_image
dir2/IMG_0001.JPG,2nd Image,more_metadata_for_the_second_image
```

#### *Installing the `category` backend engine*

Download the script `install_vgg_classifier_ubuntu.sh` located in the `install` folder and run it in your computer (**Ubuntu 14.04.5 LTS**) using a sudoer user. The script will automatically download **and compile** all necessary dependencies and copy the application in the `/webapps/visorgen/vgg_classifier` folder. Before you can use this backend, you need to configure it and compute the features for your dataset. After that, you can start the backend, which will run as local service in your computer. Please refer to <https://gitlab.com/vgg/vgg_classifier> for instructions.

There is also an experimental installer for macOS Sierra in `install_vgg_classifier_macos.sh`. Instead of running the full script, you might want to open it in a text editor and run one instruction at a time. The script installs the application in the `/$HOME/visorgen/vgg_classifier` folder.

#### *Installing the `text` backend engine*

Download the script `install_text-backend_ubuntu.sh` located in the `install` folder and run it in your computer (**Ubuntu 14.04.5 LTS**) using a sudoer user. The script will automatically download **and compile** all necessary dependencies and copy the application in the `/webapps/visorgen/text_search` folder. Before you can use this backend, you need to configure it and compute the features for your dataset. Please refer to <https://gitlab.com/vgg/text_search> for usage instructions. **Please NOTE that this repository is not open-source yet !, so only an authorized user will be able to access it. Please contact us for more information.**

#### *Configuration*

The main configuration file for the frontend is `/webapps/visorgen/vgg_frontend/visorgen/settings.py`, which contains a set of variables. If you have used the installers provided, you only need to change the engines configuration, under the **Visor web site options**.

If you have installed **ONLY** the `category` backend, overwrite `/webapps/visorgen/vgg_frontend/visorgen/settings.py` with `/webapps/visorgen/vgg_frontend/visorgen/settings_cpuvisor-srv.py`.

If you have installed **ONLY** the `text` backend, overwrite `/webapps/visorgen/vgg_frontend/visorgen/settings.py` with `/webapps/visorgen/vgg_frontend/visorgen/settings_text.py`.

After this is done. The application should be ready to start.

#### *Usage Instructions*

Open a terminal and go to the folder where the Django application is located. If you have used the installers provided, that folder should be `/webapps/visorgen/visorgen`. The fist time you start the Django server, please enter the following commands:

	python manage.py migrate
	python manage.py createsuperuser

The last command will allow you to create a superuser, which you will use to enter the administration pages of the web application. **Note that these two commands are required only the first time the server is started**.

Use the command:

	python manage.py runserver

to start the Django server. By default, the server will start at `http://127.0.0.1:8000/vgg_frontend`. Open an Internet browser and visit that URL. If you have started the installed backends manually, you will be able to see the main page of the application.

However, if you see a message "Attempting to reconnect to backend...", then the application cannot contact at least one of the installed backends. In such a case, use the Internet browser to visit `http://127.0.0.1:8000/vgg_frontend/admintools`. You will be asked for your login credentials. Please enter the superuser credentials created with the commands above, and you will be redirected to the administration page.

In the administration page, visit the `Manage Backend Service tab`, select the engine you want to start and press the `Start` button. You will see a message and then you will be redirected back to the administration page. Click on the `Home` link at the top left corner of the page to go back to the home page. If the backend was successfully started, you will be able to see the home page of the application.

In the bottom-left corner of the home page, you will see a `Getting Started` link. Click on it and read through the explanation on how to use the web application.
