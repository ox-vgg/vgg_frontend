__author__      = 'Ernesto Coto'
__copyright__   = 'March 2020'

import time
import os
from subprocess import Popen, PIPE
import threading
import pickle
import tempfile
import platform
import shutil

# Add the path to the vgg_face_search feature computation
FILE_DIR = os.path.dirname(os.path.realpath(__file__))
COMPUTE_POSITIVE_FEATURES_SCRIPT = os.path.join(FILE_DIR, '..', '..', 'vgg_text_search', 'pipeline')

# Some useful constants
if 'Windows' in platform.system():
    COMPUTE_POSITIVE_FEATURES_SCRIPT = "Not supported yet"
else:
    COMPUTE_POSITIVE_FEATURES_SCRIPT = os.path.join(COMPUTE_POSITIVE_FEATURES_SCRIPT, 'start_pipeline.sh')

def data_processing_pipeline_text_images(input_list_of_frames, index, lock, DATASET_IM_BASE_PATH):
    """ Performs the ingestion of new IMAGE data into the backend search engine.
        The paths in input_list_of_frames must be RELATIVE to the DATASET_IM_BASE_PATH path. This method does not validate that.
        Arguments:
            input_list_of_frames: Python list of paths to the frame images.
            index: iteration number, for when this method is called multiple times. Used for naming the output log file.
            lock: python multi-threading lock object
            DATASET_IM_BASE_PATH: Base path to the images referenced by the backend search engine.
    """
    # Create/clear the log file
    LOG_OUTPUT_FILE = os.path.join(tempfile.gettempdir(), 'prepro_input_%d.log' % index)
    fout = open(LOG_OUTPUT_FILE, 'w', buffering=1)
    new_files_list = ""
    output = ""
    err = ""

    try:

        if input_list_of_frames:
            fout.write(('DATA-PIPELINE [%s]: PREPROCESSING A LIST OF %d FRAMES\n') % (time.strftime("%H:%M:%S"), len(input_list_of_frames)))
        else:
            raise Exception('Cannot process an empty list of frames !')

        # Frames path should be with respect to the DATASET_IM_BASE_PATH folder
        frame_list = input_list_of_frames
        frame_list.sort()

        current_line_count = 0
        new_line_count = 0

        ### LOCK
        # acquire lock to get exclusive access to the code below
        lock.acquire()
        try:
            # Create a temp file with just the new frames
            new_files_list = os.path.join(tempfile.gettempdir(), 'text_new_%d.log' % index)
            with open(new_files_list, "w") as new_files:
                for i in range(0, len(frame_list)):
                    encode_frame_name = frame_list[i]
                    new_files.write(encode_frame_name)
                    new_files.write('\n')
        except Exception as e:
            fout.write(str(e))
            pass

        # release lock to give the chance to another thread
        try:
            lock.release() # this is in a try because when invoked on an unlocked lock, a ThreadError is raised.
        except Exception as e:
            fout.write(str(e))
            pass

        ### UNLOCK
        popen_cmd = [
                COMPUTE_POSITIVE_FEATURES_SCRIPT,
                'images',
                DATASET_IM_BASE_PATH,
                new_files_list # use just the new files
            ]
        fout.write(('DATA-PIPELINE [%s]: %s\n') % (time.strftime("%H:%M:%S"), str(popen_cmd)))
        popen_obj = Popen(popen_cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        output, err = popen_obj.communicate()
        output = output.decode()
        err = err.decode()
        success = False
        if output:
            fout.write(('DATA-PIPELINE [%s]: OUTPUT STREAM\n%s\n') % (time.strftime("%H:%M:%S"), output))
            # Beware that this is very particular of this pipeline
            success = output.endswith("Finished.\n")
        if err:
            fout.write(('DATA-PIPELINE [%s]: ERROR STREAM\n%s\n') % (time.strftime("%H:%M:%S"), err))

        if success:
            fout.write(('DATA-PIPELINE [%s]: FOUND "Finished.\\n" in output. The pipeline seems to be successful\n') % time.strftime("%H:%M:%S"))

        fout.write(('\nDATA-PIPELINE [%s]: FRAMES PROCESSING DONE\n') % (time.strftime("%H:%M:%S")))

    except Exception as e:
        # log the exception and leave
        fout.write('\n***********************************\n')
        fout.write('DATA-PIPELINE [%s]: EXCEPTION %s\n' % (time.strftime("%H:%M:%S"), str(e)))
        fout.write(err)
        pass

    fout.close()


def data_processing_pipeline_text_videos(input_list_of_videos, index, lock, DATASET_IM_BASE_PATH):
    """ Performs the ingestion of new VIDEO data into the backend search engine.
        The input_list_of_videos must contain the FULL paths to the videos. This method will extract frames from the video and
        automatically copy them in a sub-folder within DATASET_IM_BASE_PATH. The videos must be reachable within the system.
        This method does not validate that.
        Arguments:
            input_list_of_videos: Python list of paths to the video files.
            index: iteration number, for when this method is called multiple times. Used for naming the output log file.
            lock: python multi-threading lock object
            DATASET_IM_BASE_PATH: Base path to the images referenced by the backend search engine.
    """

    # Create/clear the log file
    LOG_OUTPUT_FILE = os.path.join(tempfile.gettempdir(), 'prepro_input_%d.log' % index)
    fout = open(LOG_OUTPUT_FILE, 'w', buffering=1)
    new_files_list = ""
    output = ""
    err = ""

    try:

        if input_list_of_videos:
            fout.write(('DATA-PIPELINE [%s]: PREPROCESSING A LIST OF %d VIDEOS\n') % (time.strftime("%H:%M:%S"), len(input_list_of_videos)))
        else:
            raise Exception('Cannot process an empty list of videos !')

        video_list = input_list_of_videos
        video_list.sort()

        for video_path in video_list:

            video_base_name = os.path.basename(video_path)
            popen_cmd = [
                    COMPUTE_POSITIVE_FEATURES_SCRIPT,
                    'video',
                    video_path,
                    DATASET_IM_BASE_PATH
                ]
            fout.write(('DATA-PIPELINE [%s]: %s\n') % (time.strftime("%H:%M:%S"), str(popen_cmd)))
            popen_obj = Popen(popen_cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
            output, err = popen_obj.communicate()
            output = output.decode()
            err = err.decode()
            success = None
            if err:
                fout.write(('DATA-PIPELINE [%s]: ERROR STREAM\n%s\n') % (time.strftime("%H:%M:%S"), err))
            if output:
                fout.write(('DATA-PIPELINE [%s]: OUTPUT STREAM\n%s\n') % (time.strftime("%H:%M:%S"), output))
                # Beware that this is very particular of this pipeline
                success = output.endswith("Finished.\n")

            if success:
                fout.write(('DATA-PIPELINE [%s]: FOUND "Finished.\\n" in output. The pipeline seems to be successful\n') % time.strftime("%H:%M:%S"))


    except Exception as e:
        # log the exception and leave
        fout.write('\n***********************************\n')
        fout.write('DATA-PIPELINE [%s]: EXCEPTION %s\n' % (time.strftime("%H:%M:%S"), str(e)))
        fout.write(err)
        pass

    fout.close()


def clear_data(DATASET_DATA_BASE_PATH):
    """
        Clears the data produced by data_processing_pipeline()
        Arguments:
            DATASET_DATA_BASE_PATH:  Base path of data files required/generated by the backend search engine.
        Returns:
            A string with an error message if an exception is raised. It returns a blank string otherwise.
    """
    # for the text engine, just clear up the entire backend folder
    err = ''
    for filename in os.listdir(DATASET_DATA_BASE_PATH):
        file_path = os.path.join(DATASET_DATA_BASE_PATH, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                # keep the first-level folders but delete anything inside them
                for filename2 in os.listdir(file_path):
                    file_path2 = os.path.join(file_path, filename2)
                    if os.path.isfile(file_path2) or os.path.islink(file_path2):
                        os.unlink(file_path2)
                    elif os.path.isdir(file_path2):
                        shutil.rmtree(file_path2)
        except Exception as e:
            err = err + str(e) + ' '
            pass

    return err


def data_processing_pipeline(input_list_of_frames, input_type, index, lock, DATASET_IM_BASE_PATH, DATASET_DATA_BASE_PATH=None,
                             CONFIG_PROTO_PATH = None, PREPROC_CHUNK_SIZE = None):
    """ Performs the ingestion of new data into the backend search engine. The data can be videos or images (frames). The type of
        input should be indicated by the input_type variable.
        If the input type is 'images' and a python list of frames is input, the paths in the list must be RELATIVE to the
        DATASET_IM_BASE_PATH path. This method does not validate that.
        If the input type is 'videos' the list of input paths must contain the FULL paths to the videos. This method will extract
        frames from the video and automatically copy them in a sub-folder within DATASET_IM_BASE_PATH. The videos must be
        reachable within the system. This method does not validate that.
        Mandatory arguments:
            input_list_of_frames: Python list of paths to the frame images or video files.
            input_type: one of two strings: 'images' or 'videos', indicating the type of input referenced in input_list_of_frames.
            index: iteration number, for when this method is called multiple times. Used for naming the output log file.
            lock: python multi-threading lock object
            DATASET_IM_BASE_PATH: Base path to the images referenced by the backend search engine.
        Optional arguments:
            DATASET_DATA_BASE_PATH: Not used.
            CONFIG_PROTO_PATH: Not used.
            PREPROC_CHUNK_SIZE: Not used.
    """
    if not DATASET_IM_BASE_PATH.endswith(os.path.sep):
        DATASET_IM_BASE_PATH = DATASET_IM_BASE_PATH + os.path.sep

    if input_type == 'video':
        input_list_of_videos = input_list_of_frames
        data_processing_pipeline_text_videos(input_list_of_videos, index, lock, DATASET_IM_BASE_PATH)

    if input_type == 'images':
        data_processing_pipeline_text_images(input_list_of_frames, index, lock, DATASET_IM_BASE_PATH)

#Test invocation for image ingestion
#lock = threading.Lock()
#input_list_of_frames = [ 'pic00001.jpg', 'pic00002.jpg', 'pic00005.jpg', 'pic00007.jpg']
#DATASET_IM_BASE_PATH = '/webapps/visorgen/text_search/test/images'
#OUTPUT_FILE = 'None'
#data_processing_pipeline(input_list_of_frames, 'images', 0, lock, DATASET_IM_BASE_PATH)

#Test invocation for video ingestion
#lock = threading.Lock()
#inputListOfVideos = [ '/webapps/visorgen/text_search/test/videos/big_buck_bunny_240p_2mb.mp4']
#DATASET_IM_BASE_PATH = '/webapps/visorgen/text_search/test/images'
#OUTPUT_FILE = 'None'
#data_processing_pipeline(inputListOfVideos, 'video', 0, lock, DATASET_IM_BASE_PATH)
