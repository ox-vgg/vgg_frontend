from django.conf import settings
import os
import string
import re
import requests
import json
import csv
import tempfile
import platform
from subprocess import Popen, PIPE
from PIL import Image

def start_backend_service(engine):
    """
        Body of the thread that runs the script to start the backend service
        Arguments:
            engine: keyword of the engine in the setting's engine dictionary
    """
    if 'Windows' in platform.system():
        popen_cmd = [os.path.join(settings.MANAGE_SERVICE_SCRIPTS_BASE_PATH, 'start_backend_service.bat'), engine]
    else:
        popen_cmd = [os.path.join(settings.MANAGE_SERVICE_SCRIPTS_BASE_PATH, 'start_backend_service.sh'), engine]
    popen_obj = Popen(popen_cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    popen_obj.poll()


def stop_backend_service(engine):
    """
        Body of the thread that runs the script to stop the backend service
        Arguments:
            engine: keyword of the engine in the setting's engine dictionary
    """
    if 'Windows' in platform.system():
        popen_cmd = [os.path.join(settings.MANAGE_SERVICE_SCRIPTS_BASE_PATH, 'stop_backend_service.bat'), engine]
    else:
        popen_cmd = [os.path.join(settings.MANAGE_SERVICE_SCRIPTS_BASE_PATH, 'stop_backend_service.sh'), engine]
    popen_obj = Popen(popen_cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    popen_obj.poll()


def download_manifest(manifest_url, pipeline_frame_list, img_base_path, metadata_dir):
    """
        Downloads an IIIF Manifest file form the specified URL. Downloads the images
        specified in the manifest and includes them for processing. Also downloads
        the metadata associated with the manifest and appends it to the existing
        metadata file.
        Arguments:
            manifest_url: URL to the IIIF manifest file
            img_base_path: Full path to the folder of images. Used as the base where to create an image subfolder
                           where to download the new images into.
            pipeline_frame_list: Pointer to the list of frames to be added. This is an OUT parameter,
                                 so any previous content will be erased.
            metadata_dir: Full path to the folder containing the CSV metadata file. The file is updated with
                          the metadata obtained from the IIIF manifest.
        Returns:
            A string with records of the output generated during the process. This is made to be printed to stdout or a file.
    """
    out_str = ''
    try:
        pattern = re.compile('[^a-zA-Z0-9_]')
        string_accepted = pattern.sub('', string.printable)
        images_counter = 0
        images_metadata = []
        manifest_metadata = {}

        response = requests.get(manifest_url, allow_redirects=True, verify=False)
        document = response.json()
        destination_folder_name = ''.join(filter(lambda afunc: afunc in string_accepted, document['@id']))
        destination_folder_path = os.path.join(img_base_path, destination_folder_name)
        if os.path.exists(destination_folder_path):
            raise Exception("An image folder for this JSON document already exists. Aborting !")
        else:
            os.mkdir(destination_folder_path)

        if 'label' in document:
            manifest_metadata['label'] =  document['label']
        if 'attribution' in document:
            manifest_metadata['attribution'] =  document['attribution']
        if 'description' in document:
            manifest_metadata['description'] =  document['description']
        if 'metadata' in document:
            for entry in document['metadata']:
                if entry['label'] not in manifest_metadata.keys():
                    manifest_metadata[ entry['label'] ] = entry['value']
                else:
                    manifest_metadata[ entry['label'] ] += ' || ' + entry['value']

        iterable = {}
        if document['@type'] == "sc:Manifest":
            iterable = document
        if document['@type'] == "sc:Sequence":
            iterable['sequences'] = []
            iterable['sequences'].append( {'canvases': document['canvases'] } )
        if document['@type'] == "sc:Canvas":
            iterable['sequences'] = []
            iterable['sequences'].append( {'canvases': [] } )
            iterable['sequences'][0]['canvases'].append( {'images': document['images'] } )


        for sequence in iterable['sequences']:
            for canvas in sequence['canvases']:
                canvas_label = None
                if 'label' in canvas:
                    canvas_label =  canvas['label']
                for image in canvas['images']:
                    destination_file_path = None
                    image_url = None
                    try:
                        if 'resource' in image and ( ('format' in image['resource'] and 'image' in image['resource']['format']) or
                            ('@type' in image['resource'] and image['resource']['@type']=='dctypes:Image' ) ):
                            scale_image = False
                            if 'service' in image['resource']:
                                image_url = image['resource']['service']['@id'] + '/full/' + str(settings.IIIF_IMAGE_MAX_WIDTH) + ',/0/default'
                                head_response = requests.head(image_url, allow_redirects=True, verify=False)
                                if head_response.status_code != 200:
                                    response = requests.get(image['resource']['service']['@id'], allow_redirects=True, verify=False)
                                    service_document = response.json()
                                    if len(service_document['profile']) > 1:
                                        service_profiles = service_document['profile'][1:] # 0 is always a compliance URL
                                        if 'formats' in service_profiles[0]:
                                            image_format = service_profiles[0]['formats'][0] # just use the first format
                                            image_url = image_url + '.' + image_format
                                        else:
                                            image_url = image['resource']['@id']
                                    else:
                                        image_url = image['resource']['@id']
                            else:
                                image_url = image['resource']['@id']
                                scale_image = True

                            destination_file_path = os.path.join(destination_folder_path, str(images_counter) )
                            r = requests.get(image_url, allow_redirects=True, verify=False)
                            open(destination_file_path, 'wb').write(r.content)
                            if scale_image:
                                img = Image.open(destination_file_path)
                                imW, imH = img.size
                                scale = float(settings.IIIF_IMAGE_MAX_WIDTH)/imW
                                img.thumbnail((int(imW*scale), int(imH*scale)), resample=Image.BICUBIC)
                                img.save(destination_file_path  + '.jpg', 'JPEG') # always store jpg
                                os.remove(destination_file_path)
                            else:
                                img = Image.open(destination_file_path)
                                img.save(destination_file_path  + '.jpg', 'JPEG') # always store jpg
                                os.remove(destination_file_path)

                            pipeline_frame_list.append( os.path.join(destination_folder_name, str(images_counter)  + '.jpg' ))
                            # save metadata of current image
                            img_metadata = { 'filename': os.path.join(destination_folder_name, str(images_counter) + '.jpg') }
                            img_metadata['file_attributes'] = manifest_metadata.copy()
                            if canvas_label:
                                img_metadata['file_attributes']['caption'] = canvas_label
                                img_metadata['file_attributes']['keywords'] = canvas_label

                            images_metadata.append(img_metadata)
                            images_counter = images_counter + 1

                    except Exception as e:
                        # remove the file if it was not successfully processed
                        if destination_file_path and os.path.exists(destination_file_path):
                            os.remove(destination_file_path)
                        out_str = out_str + 'Exception while accessing image with url %s, skipping. Problem: %s\n' % (image_url, str(e))
                        pass

        out_str = out_str + 'Images processed from input JSON: %d\n' % images_counter
        if metadata_dir:
            metadata_file = None
            metadata_file_handler = None
            found_a_csv = False
            for afile in os.listdir(metadata_dir):
                if afile and afile.endswith(".csv"):
                    metadata_file = os.path.join(metadata_dir, afile)
                    found_a_csv = True
                    break
            if found_a_csv:
                metadata_file_handler = open(metadata_file, 'a')
            else:
                metadata_file = os.path.join(metadata_dir, 'metadata.csv')
                metadata_file_handler = open(metadata_file, 'w')
                metadata_file_handler.write('#filename,file_attributes\n')

            out_str = out_str + 'Saving metadata from JSON to: %s\n' % metadata_file
            csv_writer = csv.writer(metadata_file_handler, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            for item in images_metadata:
                csv_writer.writerow( [item['filename'], json.dumps(item['file_attributes']) ] )

    except Exception as e:
        out_str = out_str + 'Exception while processing manifest at url %s, skipping. Problem: %s\n' % (manifest_url, str(e))
        pass

    return out_str


def gather_pipeline_input(input_type, img_base_path, files, file_system_encoding_not_UTF8, pipeline_frame_list, metadata_dir=None):
    """
        Body of the thread that checks and acquires the list of files to input to the pipeline
        Arguments:
            input_type: The string 'dir' if a folder should be scanned. The string 'list' if a list of filepaths is provided.
            img_base_path: Full path to the folder of images. Used as the folder to be scanned when input_type is 'dir'. Used as
                           the base folder for the files indicated in the list of files when input_type is 'list'.
            files: List of files to be checked. It should be None when input_type is 'dir'.
                   if input_type is 'json', it should contain only one item, specifying the json file to be processed.
                   if input_type is 'url', it should contain only one item, specifying the URL to the file to be downloaded and processed.
            file_system_encoding_not_UTF8: Boolean indicating the operating systems' string to is non-utf-8
            pipeline_frame_list: Pointer to the list of frames to be added. This is OUT parameter, so any previous content will be erased.
            metadata_dir: Full path to the folder containing the CSV metadata file
        Returns:
            pipeline_frame_list: Output list of images to be processed in the pipeline. This is an OUTPUT argument.
    """
    fout = None
    del pipeline_frame_list[:]

    try:
        abort = False

        # Create/clear the log file
        LOG_OUTPUT_FILE = os.path.join(tempfile.gettempdir(), 'gather_pipeline_input.log')
        fout = open(LOG_OUTPUT_FILE, 'w', buffering=1)
        fout.write('CHECK_PIPELINE_INPUT BEGIN\n')
        fout.write('input_type: %s\n' % input_type)
        fout.write('img_base_path: %s\n' % img_base_path)
        fout.write('files: %s\n' % str(files))

        if input_type == 'dir':

            for root, dirnames, filenames in os.walk(img_base_path):
                if not abort:
                    for i in range(len(filenames)):
                        if not abort:
                            filename = filenames[i]
                            if filename.startswith('.'):
                                continue # skip hidden files, specially in macOS
                            root_str = root
                            if file_system_encoding_not_UTF8:
                                root_str = str(root) # convert to the system's 'str' to avoid problems with the 'os' module in non-utf-8 systems
                            full_path = os.path.join(root_str, filename)
                            if os.path.isfile(full_path):
                                relative_path = os.path.join(root_str.replace(img_base_path, ''), filename)
                                if relative_path.startswith("/"):
                                    relative_path = relative_path[1:]
                                # check file is an image...
                                filename, file_extension = os.path.splitext(relative_path)
                                if file_extension.lower() in settings.VALID_IMG_EXTENSIONS:
                                    # if it is, add it to the list
                                    if file_system_encoding_not_UTF8:
                                        relative_path = relative_path.decode('utf-8') # if needed, convert from utf-8. It will be converted back by the pipeline.
                                    pipeline_frame_list.append(relative_path)
                                else:
                                    # otherwise, abort !. This might seem drastic, but it is better to
                                    # keep the image folder clean !.
                                    del pipeline_frame_list[:]
                                    abort = True

        if input_type == 'file':

            for frame_path in files:
                if not abort:
                    frame_path = frame_path.strip()
                    if frame_path == '':
                        continue
                    if frame_path.startswith('/'):
                        frame_path = frame_path[1:]
                    if not file_system_encoding_not_UTF8:       # if NOT utf-8, convert before operations with the 'os' module,
                        frame_path = frame_path.decode('utf-8') # otherwise convert it later
                    full_frame_path = os.path.join(img_base_path, frame_path)
                    filename, file_extension = os.path.splitext(full_frame_path)
                    # Check frame exists
                    if not os.path.exists(full_frame_path):
                        # abort the process if the frame is not found
                        abort = True
                    # Check file is an image ...
                    elif file_extension.lower() in settings.VALID_IMG_EXTENSIONS:
                        # if it is, add it to the list
                        if file_system_encoding_not_UTF8:
                            frame_path = frame_path.decode('utf-8') # if needed, convert from utf-8
                        pipeline_frame_list.append(frame_path)
                    else:
                        # otherwise, abort !. This might seem drastic, but it is better to
                        # keep the image folder clean !.
                        del pipeline_frame_list[:]
                        abort = True

        # IIIF input treatment starts here
        document = None
        if input_type == 'json':
            with open(files[0], 'r') as jsonf:
                document = json.load(jsonf)

        if input_type == 'url':
            url = files[0]
            response = requests.get(url, allow_redirects=True, verify=False)
            document = response.json()

        if document is not None:
            if document['@type'] in [ "sc:Collection" ]:
                for manifest in document['manifests']:
                    out_str = download_manifest(manifest['@id'], pipeline_frame_list, img_base_path, metadata_dir)
                    fout.write('%s' % out_str)
            elif document['@type'] in [ "sc:Manifest", "sc:Sequence", "sc:Canvas"]:
                out_str = download_manifest(document['@id'], pipeline_frame_list, img_base_path, metadata_dir)
                fout.write('%s' % out_str)

        fout.write('CHECK_PIPELINE_INPUT END\n')

    except Exception as e:
        # log the exception and leave
        if fout:
            fout.write('CHECK_PIPELINE_EXCEPTION %s\n' % e.message)
        pass

    if fout:
        fout.close()
