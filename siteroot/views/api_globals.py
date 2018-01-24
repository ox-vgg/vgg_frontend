from django.conf import settings
import os
from subprocess import Popen, PIPE


def start_backend_service(engine):
    """
        Body of the thread that runs the script to start the backend service
        Arguments:
            engine: keyword of the engine in the setting's engine dictionary
    """
    pOpenCmd = [ os.path.join( settings.MANAGE_SERVICE_SCRIPTS_BASE_PATH, 'start_backend_service.sh'), engine ]
    p = Popen(pOpenCmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    p.poll()


def stop_backend_service(engine):
    """
        Body of the thread that runs the script to stop the backend service
        Arguments:
            engine: keyword of the engine in the setting's engine dictionary
    """
    pOpenCmd = [ os.path.join( settings.MANAGE_SERVICE_SCRIPTS_BASE_PATH, 'stop_backend_service.sh'), engine ]
    p = Popen(pOpenCmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    p.poll()


def gather_pipeline_input(input_type, img_base_path, files, fileSystemEncodingNotUTF8, pipeline_frame_list):
    """
        Body of the thread that checks and acquires the list of files to input to the pipeline
        Arguments:
            input_type: The string 'dir' if a folder should be scanned. The string 'list' if a list of filepaths is provided.
            img_base_path: Full path to the folder of images. Used as the folder to be scanned when input_type is 'dir'. Used as
                           the base folder for the files indicated in the list of files when input_type is 'list'.
            files: List of files to be checked. It should be None when input_type is 'dir'.
            fileSystemEncodingNotUTF8: Boolena indicating the operating systems' string to is non-utf-8
        Returns:
            pipeline_frame_list: Output list of images to be processed in the pipeline. This is an OUTPUT argument.
    """
    fout = None
    pipeline_frame_list = []

    try:
        abort = False

        # Create/clear the log file
        LOG_OUTPUT_FILE = '/tmp/gather_pipeline_input.log'
        fout = open( LOG_OUTPUT_FILE, 'w',  buffering=1)
        fout.write( 'CHECK_PIPELINE_INPUT BEGIN\n' )
        fout.write( 'input_type: %s\n' % input_type )
        fout.write( 'img_base_path: %s\n' % img_base_path )
        fout.write( 'files: %s\n' % str(files) )

        if input_type == 'dir':

            for root, dirnames, filenames in os.walk( img_base_path ):
                if not abort:
                    for i in range(len(filenames)):
                        if not abort:
                            filename = filenames[i]
                            if filename.startswith('.'):
                                continue # skip hidden files, specially in macOS
                            root_str = root
                            if fileSystemEncodingNotUTF8:
                                root_str = str(root) # convert to the system's 'str' to avoid problems with the 'os' module in non-utf-8 systems
                            full_path = os.path.join( root_str , filename)
                            if os.path.isfile(full_path):
                                relative_path = os.path.join( root_str.replace( img_base_path ,'') , filename)
                                if relative_path.startswith("/"):
                                    relative_path = relative_path[1:]
                                # check file is an image...
                                filename, file_extension = os.path.splitext(relative_path)
                                if file_extension in settings.VALID_IMG_EXTENSIONS:
                                    # if it is, add it to the list
                                    if fileSystemEncodingNotUTF8:
                                        relative_path = relative_path.decode('utf-8') # if needed, convert from utf-8. It will be converted back by the pipeline.
                                    pipeline_frame_list.append(relative_path)
                                else:
                                    # otherwise, abort !. This might seem drastic, but it is better to
                                    # keep the image folder clean !.
                                    pipeline_frame_list = []
                                    abort = True

        if input_type == 'file':

            for frame_path in files:
                if not abort:
                    frame_path = frame_path.strip()
                    if frame_path.startswith('/'):
                        frame_path = frame_path[1:]
                    if not fileSystemEncodingNotUTF8:           # if NOT utf-8, convert before operations with the 'os' module,
                        frame_path = frame_path.decode('utf-8') # otherwise convert it later
                    full_frame_path = os.path.join( img_base_path, frame_path )
                    filename, file_extension = os.path.splitext(full_frame_path)
                    # Check frame exists
                    if not os.path.exists(full_frame_path):
                         # abort the process if the frame is not found
                         abort = True
                    # Check file is an image ...
                    elif file_extension in settings.VALID_IMG_EXTENSIONS:
                        # if it is, add it to the list
                        if fileSystemEncodingNotUTF8:
                            frame_path = frame_path.decode('utf-8') # if needed, convert from utf-8
                        pipeline_frame_list.append(frame_path)
                    else:
                        # otherwise, abort !. This might seem drastic, but it is better to
                        # keep the image folder clean !.
                        pipeline_frame_list = []
                        abort = True

        fout.write( 'CHECK_PIPELINE_INPUT END\n' )

    except Exception as e:
        # log the exception and leave
        if fout:
            fout.write( 'CHECK_PIPELINE_EXCEPTION %s\n' % e.message)
        pass

    if fout:
        fout.close()
