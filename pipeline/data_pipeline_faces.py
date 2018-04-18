__author__      = 'Ernesto Coto'
__copyright__   = 'April 2018'

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
COMPUTE_POSITIVE_FEATURES_SCRIPT = os.path.join(FILE_DIR, '..', '..', 'vgg_face_search', 'pipeline')
if 'Windows' in platform.system():
    COMPUTE_POSITIVE_FEATURES_SCRIPT = os.path.join(COMPUTE_POSITIVE_FEATURES_SCRIPT, 'start_pipeline.bat')
else:
    COMPUTE_POSITIVE_FEATURES_SCRIPT = os.path.join(COMPUTE_POSITIVE_FEATURES_SCRIPT, 'start_pipeline.sh')

def data_processing_pipeline_faces_images(input_list_of_frames, index, lock, DATASET_IM_BASE_PATH, DATASET_IM_PATHS, OUTPUT_FILE):
    """ Performs the ingestion of new IMAGE data into the backend search engine.
        The paths in input_list_of_frames must be RELATIVE to the DATASET_IM_BASE_PATH path. This method does not validate that.
        Arguments:
            input_list_of_frames: Python list of paths to the frame images.
            index: iteration number, for when this method is called multiple times. Used for naming the output log file.
            lock: python multi-threading lock object
            DATASET_IM_PATHS: Path to the file containing the location of all images previously ingested by the backend search engine.
            DATASET_IM_BASE_PATH: Base path to the images referenced by the backend search engine.
            OUTPUT_FILE: Path to the final output features file.
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

        # Frames path should be with respect to the DATASET_IM_PATHS folder
        frame_list = input_list_of_frames
        frame_list.sort()

        current_line_count = 0
        new_line_count = 0

        ### LOCK
        # acquire lock to get exclusive access to the code below
        lock.acquire()
        try:
            # Create/modify frame list file (a.k.a. DATASET_IM_PATHS)
            fout.write(('DATA-PIPELINE [%s]: INSERTING FRAME LIST INTO: %s\n') % (time.strftime("%H:%M:%S"), DATASET_IM_PATHS))
            with open(DATASET_IM_PATHS, "a+") as dataset_imgs_file:
                for counter, line in enumerate(dataset_imgs_file):
                    current_line_count = current_line_count + 1
                fout.write(('DATA-PIPELINE [%s]: NUMBER OF FRAMES IN CURRENT FRAME LIST FILE: %d\n') % (time.strftime("%H:%M:%S"), current_line_count))
                new_line_count = current_line_count
                for i in range(0, len(frame_list)):
                    new_line_count = new_line_count + 1
                    encode_frame_name = frame_list[i].encode("utf-8")
                    dataset_imgs_file.write(encode_frame_name)
                    dataset_imgs_file.write('\n')
            fout.write(('DATA-PIPELINE [%s]: NUMBER OF FRAMES IN NEW FRAME LIST FILE: %d\n') % (time.strftime("%H:%M:%S"), new_line_count))
            # Now create a temp file with just the new frames
            new_files_list = os.path.join(tempfile.gettempdir(), 'faces_new_%d.log' % index)
            with open(new_files_list, "w") as new_files:
                for i in range(0, len(frame_list)):
                    encode_frame_name = frame_list[i].encode("utf-8")
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
        chunk_output_file = OUTPUT_FILE.replace('.pkl', '-%d_%d.pkl' % (current_line_count, new_line_count))
        popen_cmd = [
                COMPUTE_POSITIVE_FEATURES_SCRIPT,
                'images',
                DATASET_IM_BASE_PATH,
                new_files_list, # use just the new files
                chunk_output_file
            ]
        fout.write(('DATA-PIPELINE [%s]: %s\n') % (time.strftime("%H:%M:%S"), str(popen_cmd)))
        popen_obj = Popen(popen_cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        output, err = popen_obj.communicate()
        if output:
            fout.write(('DATA-PIPELINE [%s]: OUTPUT STREAM\n%s\n') % (time.strftime("%H:%M:%S"), output))
        if err:
            fout.write(('DATA-PIPELINE [%s]: ERROR STREAM\n%s\n') % (time.strftime("%H:%M:%S"), err))

        if os.path.exists(chunk_output_file):
            # if the file was created successfully
            ### LOCK
            lock.acquire()
            try:
                database = []
                if os.path.exists(OUTPUT_FILE):
                    # load the existing list ....
                    with open(OUTPUT_FILE, 'rb') as database_in:
                        database = pickle.load(database_in)
                        database.append(os.path.basename(chunk_output_file))
                else:
                    database.append(os.path.basename(chunk_output_file))
                # and save it again ...
                with open(OUTPUT_FILE, 'wb') as database_out:
                    pickle.dump(database, database_out, pickle.HIGHEST_PROTOCOL)
            except Exception as e:
                fout.write(str(e))
                pass

        # release lock to give the chance to another thread
        try:
            if os.path.exists(chunk_output_file):
                lock.release() # this is in a try because when invoked on an unlocked lock, a ThreadError is raised.
        except Exception as e:
            fout.write(str(e))
            pass

        fout.write(('DATA-PIPELINE [%s]: FRAMES PROCESSING DONE\n') % (time.strftime("%H:%M:%S")))

    except Exception as e:
        # log the exception and leave
        fout.write('\n***********************************\n')
        fout.write('FACE-PIPELINE [%s]: EXCEPTION %s\n' % (time.strftime("%H:%M:%S"), e.message))
        fout.write(err)
        pass

    fout.close()

def data_processing_pipeline_faces_videos(input_list_of_videos, index, lock, DATASET_IM_BASE_PATH, DATASET_IM_PATHS, OUTPUT_FILE):
    """ Performs the ingestion of new VIDEO data into the backend search engine.
        The input_list_of_videos must contain the FULL paths to the videos. This method will extract frames from the video and
        automatically copy them in a sub-folder within DATASET_IM_BASE_PATH. The videos must be reachable within the system.
        This method does not validate that.
        Arguments:
            input_list_of_videos: Python list of paths to the video files.
            index: iteration number, for when this method is called multiple times. Used for naming the output log file.
            lock: python multi-threading lock object
            DATASET_IM_PATHS: Path to the file containing the location of all images previously ingested by the backend search engine.
            DATASET_IM_BASE_PATH: Base path to the images referenced by the backend search engine.
            OUTPUT_FILE: Path to the final output features file.
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
            tmp_chunk_output_file = os.path.join(tempfile.gettempdir(), video_base_name + '.pkl')
            popen_cmd = [
                    COMPUTE_POSITIVE_FEATURES_SCRIPT,
                    'video',
                    video_path,
                    DATASET_IM_BASE_PATH,
                    tmp_chunk_output_file
                ]
            popen_obj = Popen(popen_cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
            output, err = popen_obj.communicate()
            splitted_output = None
            if err:
                fout.write(('DATA-PIPELINE [%s]: ERROR STREAM\n%s\n') % (time.strftime("%H:%M:%S"), err))
            if output:
                fout.write(('DATA-PIPELINE [%s]: OUTPUT STREAM\n%s\n') % (time.strftime("%H:%M:%S"), output))
                splitted_output = output.split('\n')

            if os.path.exists(tmp_chunk_output_file) and splitted_output:

                current_line_count = 0
                new_line_count = 0

                ### LOCK
                # acquire lock to get exclusive access to the code below
                lock.acquire()
                try:
                    # Create/modify frame list file (a.k.a. DATASET_IM_PATHS)
                    fout.write(('DATA-PIPELINE [%s]: INSERTING FRAME LIST INTO: %s\n') % (time.strftime("%H:%M:%S"), DATASET_IM_PATHS))
                    with open(DATASET_IM_PATHS, "a+") as dataset_imgs_file:
                        for counter, line in enumerate(dataset_imgs_file):
                            current_line_count = current_line_count + 1
                        fout.write(('DATA-PIPELINE [%s]: NUMBER OF FRAMES IN CURRENT FRAME LIST FILE: %d\n') % (time.strftime("%H:%M:%S"), current_line_count))
                        new_line_count = current_line_count
                        for line in splitted_output:
                            if len(line) > 0 and ('.jpg' in line): # if COMPUTE_POSITIVE_FEATURES_SCRIPT was successful,
                                                                   # lines with added files must terminate in ".jpg"
                                line = line.strip()
                                new_line_count = new_line_count + 1
                                encode_frame_name = line.encode("utf-8")
                                dataset_imgs_file.write(encode_frame_name)
                                dataset_imgs_file.write('\n')

                    fout.write(('DATA-PIPELINE [%s]: NUMBER OF FRAMES IN NEW FRAME LIST FILE: %d\n') % (time.strftime("%H:%M:%S"), new_line_count))
                    # copy tmp output features to features folder
                    chunk_output_file = OUTPUT_FILE.replace('.pkl', '-%d_%d.pkl' % (current_line_count, new_line_count))
                    shutil.move(tmp_chunk_output_file, chunk_output_file)

                    # append the new features to the database
                    database = []
                    if os.path.exists(OUTPUT_FILE):
                        # load the existing list ....
                        with open(OUTPUT_FILE, 'rb') as database_in:
                            database = pickle.load(database_in)
                            database.append(os.path.basename(chunk_output_file))
                    else:
                        database.append(os.path.basename(chunk_output_file))

                    # and save it again ...
                    with open(OUTPUT_FILE, 'wb') as database_out:
                        pickle.dump(database, database_out, pickle.HIGHEST_PROTOCOL)

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

    except Exception as e:
        # log the exception and leave
        fout.write('\n***********************************\n')
        fout.write('FACE-PIPELINE [%s]: EXCEPTION %s\n' % (time.strftime("%H:%M:%S"), str(e)))
        fout.write(err)
        pass

    fout.close()

# Data pipeline definition
def data_processing_pipeline_faces(input_list_of_frames, input_type, index, lock, DATASET_IM_BASE_PATH, DATASET_IM_PATHS, OUTPUT_FILE):
    """ Performs the ingestion of new data into the backend search engine. The data can be videos or images (frames). The type of
        input should be indicated by the input_type variable.
        If the input type is 'images' and a python list of frames is input, the paths in the list must be RELATIVE to the
        DATASET_IM_BASE_PATH path. This method does not validate that.
        If the input type is 'videos' the list of input paths must contain the FULL paths to the videos. This method will extract
        frames from the video and automatically copy them in a sub-folder within DATASET_IM_BASE_PATH. The videos must be
        reachable within the system. This method does not validate that.
        Arguments:
            input_list_of_frames: Python list of paths to the frame images or video files.
            input_type: one of two strings: 'images' or 'videos', indicating the type of input referenced in input_list_of_frames.
            index: iteration number, for when this method is called multiple times. Used for naming the output log file.
            lock: python multi-threading lock object
            DATASET_IM_PATHS: Path to the file containing the location of all images previously ingested by the backend search engine.
            DATASET_IM_BASE_PATH: Base path to the images referenced by the backend search engine.
            OUTPUT_FILE: Path to the final output features file.
    """
    if input_type == 'video':
        input_list_of_videos = input_list_of_frames
        data_processing_pipeline_faces_videos(input_list_of_videos, index, lock, DATASET_IM_BASE_PATH, DATASET_IM_PATHS, OUTPUT_FILE)

    if input_type == 'images':
        data_processing_pipeline_faces_images(input_list_of_frames, index, lock, DATASET_IM_BASE_PATH, DATASET_IM_PATHS, OUTPUT_FILE)

#Test invocation for image ingestion
#lock = threading.Lock()
#input_list_of_frames = [ 'pic00001.jpg', 'pic00002.jpg', 'pic00005.jpg', 'pic00007.jpg']
#DATASET_IM_PATHS = '/webapps/visorgen/face_search/test/images.txt'
#DATASET_IM_BASE_PATH = '/webapps/visorgen/face_search/test/images'
#OUTPUT_FILE = '/webapps/visorgen/face_search/test/features/database.pkl'
#data_processing_pipeline_faces(input_list_of_frames, 'images', 0, lock, DATASET_IM_BASE_PATH, DATASET_IM_PATHS, OUTPUT_FILE)

#Test invocation for video ingestion
#lock = threading.Lock()
#inputListOfVideos = [ '/webapps/visorgen/face_search/test/videos/big_buck_bunny_240p_2mb.mp4']
#DATASET_IM_PATHS = '/webapps/visorgen/face_search/test/images.txt'
#DATASET_IM_BASE_PATH = '/webapps/visorgen/face_search/test/images'
#OUTPUT_FILE = '/webapps/visorgen/face_search/test/features/database.pkl'
#data_processing_pipeline_faces(inputListOfVideos, 'video', 0, lock, DATASET_IM_BASE_PATH, DATASET_IM_PATHS, OUTPUT_FILE)
