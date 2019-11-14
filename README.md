vgg_frontend application
========================

Author:

 + Ernesto Coto, University of Oxford – <ecoto@robots.ox.ac.uk>

License: BSD (see LICENSE.md)

`vgg_frontend` is a web application that serves as a generic web engine to perform visual searches over an image dataset. It is based on an application created by the [VGG](http://www.robots.ox.ac.uk/~vgg/) group at the [University of Oxford](http://www.ox.ac.uk/) to perform visual searchers over a large dataset of images from [BBC News](http://www.robots.ox.ac.uk/~vgg/research/on-the-fly/).

It consists of two main components:

 + An image downloading service, included in this repository in the `vgg_img_downloader` folder: It corresponds to a reduced version of the [imsearch-tools](https://github.com/kencoken/imsearch-tools). The version provided in this repository includes only the `google_web` image downloading engine, which does not require any specific configuration and hence can be used by anyone. Should you need more image downloading engines (e.g. downloading from Bing or Flick), please use the original version and supply your own API keys, depending on which image provider you wish to use.
 + The web frontend, also included in this repository: It has been developed using **Django version 1.10**, under **Ubuntu 14.04.5 LTS**. Although it has been recently updated to **Ubuntu 16.04.6 LTS**. The provided version runs in `DEBUG` mode. Should you wish to deploy it to a production environment, please refer to [Django's documentation](https://docs.djangoproject.com/en/1.10/howto/deployment/).

Now, `vgg_frontend` can be used for **just displaying a list of images** or it can be attached to **at least ONE image backend engine**. In this last case, it is the backend engine who actually processes the images in the user's dataset, so `vgg_frontend` just serves as the web user interface for the backend engine.

The following applications are fully supported: [vgg_frontend for Display](https://gitlab.com/vgg/vgg_frontend/edit/master/README.md#vgg_frontend-for-display), [VGG Image Classification (VIC) engine](https://gitlab.com/vgg/vgg_frontend/edit/master/README.md#vgg-image-classification-vic-engine) and [VGG Face Finder (VFF) engine](https://gitlab.com/vgg/vgg_frontend/edit/master/README.md#vgg-face-finder-vff-engine).

#### *`vgg_frontend` for Display*

In this case, `vgg_frontend` can be used for just displaying a list of images associated with a text string. Any search functionality or administration tool will de disable. However, you can deploy it very quickly and have a simple tool for displaying pre-defined lists of images.

Download one of the deployment scripts whose name start with `install_vgg_frontend` from the `install` directory. Scripts are provided for macOS, Ubuntu and Windows. The script will download the code in this repository, configure it and create a set of directories.

Use the file `siteroot/controllers/retengine/utils/create_predefined_results_list.py` as a template to create your own pre-defined list. The list will be stored in a file with extension `.msgpack`. Place the file in the directory called `visorgen/frontend_data/searchdata/predefined_rankinglists/display` within the folder where `vgg_frontend` was deployed by the aforementioned script.

Read the [Dataset](https://gitlab.com/vgg/vgg_frontend#dataset) section to find out how to link your images to the application and how to define metadata.

Read the [Usage Instructions](https://gitlab.com/vgg/vgg_frontend/tree/master/install#usage-instructions) to find out how to start the application.

Once you start running `vgg_frontend` you can retrieve your pre-defined list by entering in the search bar the `query_text` you used to create the file.

#### *VGG Image Classification (VIC) engine*

`VIC` is a combination of the code in this repository and [vgg_classifier](https://gitlab.com/vgg/vgg_classifier). It is an application that serves as a web engine to perform image classification queries over an user-defined image dataset. More detailed information can be found at [VIC's VGG page](http://www.robots.ox.ac.uk/~vgg/software/vic/).

In order to use `VIC`, you can easily download and use a pre-built docker version available at [this repository's container registry](https://gitlab.com/vgg/vgg_frontend/container_registry). All you need to do is to use the docker service installed on your PC to download the image, by entering the following command:

	docker pull registry.gitlab.com/vgg/vgg_frontend/vic

There is also a docker image available at [DockerHub](https://hub.docker.com/r/oxvgg/vic/), which can be downloaded in a similar way, or via a GUI called [Kitematic](https://kitematic.com/).

If you are using the docker version, there are usage instructions and sample data for `VIC` at the [Docker deployment](http://www.robots.ox.ac.uk/~vgg/software/vic/#docker_version) section on [VIC's VGG page](http://www.robots.ox.ac.uk/~vgg/software/vic/).

For advanced users, deployment scripts for macOS and Ubuntu can be found in the `install` directory, with or without GPU support. The scripts will help you find out the software dependencies and configuration requirements.

Finally, advanced users can also build the docker image by using the files in the `Dockerfiles` directory. Use `vic-kitematic` for a version that is specifically tailored to work with [Kitematic](https://kitematic.com/). Otherwise, use `vic-base` to obtain a more flexible version.

If you are NOT using the docker version, read the [Dataset](https://gitlab.com/vgg/vgg_frontend#dataset) section to find out how to link your images to the application and how to define metadata. Also, read the [Usage Instructions](https://gitlab.com/vgg/vgg_frontend/tree/master/install#usage-instructions) to find out how to start the application.

#### *VGG Face Finder (VFF) engine*

`VFF` is a combination of the code in this repository and [vgg_face_search](https://gitlab.com/vgg/vgg_face_search). It is an application that serves as a web engine to perform queries over an user-defined image dataset with faces. More detailed information can be found at [VFF's VGG page](http://www.robots.ox.ac.uk/~vgg/software/vff/).

In order to use `VFF`, you can easily download and use a pre-built docker version available at [this repository's container registry](https://gitlab.com/vgg/vgg_frontend/container_registry). All you need to do is to use the docker service installed on your PC to download the image, by entering the following command:

	docker pull registry.gitlab.com/vgg/vgg_frontend/vff

There is also a docker image available at [DockerHub](https://hub.docker.com/r/oxvgg/vff/), which can be downloaded in a similar way, or via a GUI called [Kitematic](https://kitematic.com/).

If you are using the docker version, there are usage instructions and sample data for `VFF` at the [Docker deployment](http://www.robots.ox.ac.uk/~vgg/software/vff/#docker_version) section on [VFF's VGG page](http://www.robots.ox.ac.uk/~vgg/software/vff/).

For advanced users, deployment scripts for MS Windows, macOS and Ubuntu can be found in the `install` directory, with or without GPU support. The scripts will help you find out the software dependencies and configuration requirements.

Finally, advanced users can also build the docker image by using the files in the `Dockerfiles` directory. Use `vff-kitematic` for a version that is specifically tailored to work with [Kitematic](https://kitematic.com/). Otherwise, use `vff-base` to obtain a more flexible version.

If you are NOT using the docker version, read the [Dataset](https://gitlab.com/vgg/vgg_frontend#dataset) section to find out how to link your images to the application and how to define metadata. Also, read the [Usage Instructions](https://gitlab.com/vgg/vgg_frontend/tree/master/install#usage-instructions) to find out how to start the application.

Dataset
-------

If you have executed one of the scripts in the `install` folder, the application you chose should have been deployed either in `/webapps/` or at `$HOME` or at a directory of your choosing, let's hereby call that directory MY_FOLDER.

There should be a `MY_FOLDER/visorgen/datasets/images/mydataset` folder and a `MY_FOLDER/visorgen/datasets/metadata/mydataset` folder in your computer. Please check these folders were created.

Copy the images of your dataset to `MY_FOLDER/visorgen/datasets/images/mydataset`. The organization of your files inside this folder can include subdirectories, if necessary.

Create a CSV file of [Comma-separated values](https://en.wikipedia.org/wiki/Comma-separated_values) called `metadata.csv` and copy it to `/webapps/visorgen/datasets/metadata/mydataset`. Each line in the file will correspond to the metadata of one of your image files. The structure of the CSV is explained below. If you do not have any metadata for your images, the web application will simply not show any metadata information when displaying your images, but it will still work.

If you have deployed `vgg_frontend` for Display, there should be nothing else to setup, so read [Usage Instructions](https://gitlab.com/vgg/vgg_frontend/tree/master/install#usage-instructions) for instructions on how to start/stop the application.

For VIC, please refer this [document](http://www.robots.ox.ac.uk/~vgg/software/vic/downloads/docker/using_your_own_images.pdf) at VIC's VGG web page. Simply ignore the steps referring to starting/stopping the application with Kitematic and replace them with the instructions at [Usage Instructions](https://gitlab.com/vgg/vgg_frontend/tree/master/install#usage-instructions).

For VFF, please refer this [document](http://www.robots.ox.ac.uk/~vgg/software/vff/downloads/docker/using_your_own_images.pdf) at VFF's VGG web page. Simply ignore the steps referring to starting/stopping the application with Kitematic and replace them with the instructions at [Usage Instructions](https://gitlab.com/vgg/vgg_frontend/tree/master/install#usage-instructions).

VFF is also able to ingest video files, in which case you do not need to copy images in the `MY_FOLDER/visorgen/datasets/images/mydataset` folder. VFF will extract the images from the videos. More intructions are available in this [document](http://www.robots.ox.ac.uk/~vgg/software/vff/downloads/docker/using_your_own_images.pdf) at VFF's VGG web page.

Metadata Structure
------------------

Each line of the CSV file corresponds to a series of text strings, separated from each other by a comma (`,`) character. This kind of file can be created/edited with almost any modern spreadsheet application (MS Excel, LibreOffice Calc, etc.), therefore each line of the CSV corresponds to a `row` of the spreadsheet, and each `column` is formed by the comma-separated text values at each row.

The first row of the CSV should contain the titles of the columns, and there should be at least two columns. The title of the first column should be `filename`, and the title of the second column should be `file_attributes`.

The `filename` column should contain the path to the images, relative to the `MY_FOLDER/visorgen/datasets/images/mydataset` folder. The `file_attributes` column should contain a string in [JSON format](https://en.wikipedia.org/wiki/JSON). This string should correspond to a list of elements, similar to the one in this [example](https://en.wikipedia.org/wiki/JSON#Example). The following two elements are used by `vgg_frontend`:

 1. `caption`, which should be a short text string (less than 20 characters). This text will show up at the bottom of the image in the list of results of a query.
 2. `keywords`, which should be a comma-separated list of keywords (single-word strings that should not contain blank spaces). Each keyword will be displayed in the user interface and you will be able to use them to select the images you want to use as input for a query.

Any extra columns or extra `file_attributes` will be ignored by `vgg_frontend`, but they will be visible in the details page of each image.

There are three ways in which you can produce this file.

#### *Using VIA*

You can use the [VGG Image Annotator](http://www.robots.ox.ac.uk/~vgg/software/via/). Just load your images and create two `File Attributes` called `caption` and `keywords`. Use VIA to write the values of those attributes for each file. Once you are done, use the `Save as CSV` menu option to export these annotations to a CSV file. VIA will automatically add the `filename` column and save the file attributes in [JSON format](https://en.wikipedia.org/wiki/JSON). Place that CSV file inside `MY_FOLDER/visorgen/datasets/metadata/mydataset` and start/restart the web application.

#### *Using a spreadsheet application*

Add the column titles in the first row and add the filenames to the `filename` column. You can add the values of the `file_attributes` column just like any other string, but keep in mind that you must **use the proper JSON format**. For instance, remember that for each element, the name of the element should be enclosed in double-quotes, as well as the element value (because they will be text strings, in our case), see this [example](https://en.wikipedia.org/wiki/JSON#Example). **Avoid unnecessary line breaks, blank spaces and special characters in your list of keywords and captions**. Once you are done, place that CSV file inside `MY_FOLDER/visorgen/datasets/metadata/mydataset` and start/restart the web application.

#### *Using a text editor*

CSV files are just regular text files so you can use a standard text editor (e.g. Notepad) to create/edit the file. However, be very careful with the format of the text. Remember that the default [field delimiter](https://en.wikipedia.org/wiki/Delimiter-separated_values) for CSV is the double-quote and this will conflict with the JSON format, so you will need to [escape](https://en.wikipedia.org/wiki/Escape_character) the double-quotes. Once again, **avoid unnecessary line breaks, blank spaces and special characters in your list of keywords and captions**, or you will need to [escape](https://en.wikipedia.org/wiki/Escape_character) those characters. Once you are done, place that CSV file inside `MY_FOLDER/visorgen/datasets/metadata/mydataset` and start/restart the web application.
