import time
import os
import sys
from subprocess import Popen, PIPE
import threading
import pickle
import tempfile
import platform
import shutil

# Add the path to the vgg_face_search feature computation
file_dir = os.path.dirname(os.path.realpath(__file__))
COMPUTE_POSITIVE_FEATURES_SCRIPT = os.path.join(file_dir, '..' , '..', 'vgg_face_search', 'pipeline')
if 'Windows' in platform.system():
    COMPUTE_POSITIVE_FEATURES_SCRIPT = os.path.join( COMPUTE_POSITIVE_FEATURES_SCRIPT, 'start_pipeline.bat' )
else:
    COMPUTE_POSITIVE_FEATURES_SCRIPT = os.path.join( COMPUTE_POSITIVE_FEATURES_SCRIPT, 'start_pipeline.sh' )

def data_processing_pipeline_faces_images(inputListOfFrames, index, lock, DATASET_IM_BASE_PATH, DATASET_IM_PATHS, OUTPUT_FILE):
    """ Performs the ingestion of new IMAGE data into the backend search engine.
        The paths in inputListOfFrames must be RELATIVE to the DATASET_IM_BASE_PATH path. This method does not validate that.
        Arguments:
            inputListOfFrames: Python list of paths to the frame images.
            index: iteration number, for when this method is called multiple times. Used for naming the output log file.
            lock: python multi-threading lock object
            DATASET_IM_PATHS: Path to the file containing the location of all images previously ingested by the backend search engine.
            DATASET_IM_BASE_PATH: Base path to the images referenced by the backend search engine.
            OUTPUT_FILE: Path to the final output features file.
    """
    # Create/clear the log file
    LOG_OUTPUT_FILE = os.path.join( tempfile.gettempdir(), 'prepro_input_%d.log' % index )
    fout = open( LOG_OUTPUT_FILE, 'w', buffering=1)
    new_files_list = ""
    output = ""
    err = ""

    try:

        if inputListOfFrames:
            fout.write( ('DATA-PIPELINE [%s]: PREPROCESSING A LIST OF %d FRAMES\n') % ( time.strftime("%H:%M:%S"), len(inputListOfFrames) ) )
        else:
            raise Exception('Cannot process an empty list of frames !')

        # Frames path should be with respect to the DATASET_IM_PATHS folder
        frameList = inputListOfFrames
        frameList.sort()

        currentLineCount = 0
        newLineCount = 0

        ### LOCK
        # acquire lock to get exclusive access to the code below
        lock.acquire()
        try:
            # Create/modify frame list file (a.k.a. DATASET_IM_PATHS)
            fout.write( ('DATA-PIPELINE [%s]: INSERTING FRAME LIST INTO: %s\n') % (time.strftime("%H:%M:%S"), DATASET_IM_PATHS) )
            with open(DATASET_IM_PATHS, "a+") as datasetImgsFile:
                for counter, line in enumerate(datasetImgsFile):
                    currentLineCount = currentLineCount + 1
                fout.write( ('DATA-PIPELINE [%s]: NUMBER OF FRAMES IN CURRENT FRAME LIST FILE: %d\n') % (time.strftime("%H:%M:%S"), currentLineCount)  )
                newLineCount = currentLineCount
                for i in range(0, len(frameList) ):
                    newLineCount = newLineCount + 1
                    encodeFrameName =  frameList[i].encode("utf-8")
                    datasetImgsFile.write(encodeFrameName)
                    datasetImgsFile.write('\n')
            fout.write( ('DATA-PIPELINE [%s]: NUMBER OF FRAMES IN NEW FRAME LIST FILE: %d\n') % (time.strftime("%H:%M:%S"), newLineCount))
            # Now create a temp file with just the new frames
            new_files_list = os.path.join( tempfile.gettempdir(), 'faces_new_%d.log' % index )
            with open(new_files_list, "w") as newFiles:
                for i in range(0, len(frameList) ):
                    encodeFrameName =  frameList[i].encode("utf-8")
                    newFiles.write(encodeFrameName)
                    newFiles.write('\n')
        except Exception as e:
            fout.write( str(e) )
            pass

        # release lock to give the chance to another thread
        try:
            lock.release() # this is in a try because when invoked on an unlocked lock, a ThreadError is raised.
        except Exception as e:
            fout.write( str(e) )
            pass

        ### UNLOCK
        chunk_output_file = OUTPUT_FILE.replace('.pkl', '-%d_%d.pkl' % (currentLineCount,newLineCount) )
        pOpenCmd = [
                COMPUTE_POSITIVE_FEATURES_SCRIPT,
                'images',
                DATASET_IM_BASE_PATH,
                new_files_list, # use just the new files
                chunk_output_file
            ]
        fout.write( ('DATA-PIPELINE [%s]: %s\n') % ( time.strftime("%H:%M:%S"), str(pOpenCmd)) )
        p = Popen(pOpenCmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        output, err = p.communicate()
        if output:
            fout.write( ('DATA-PIPELINE [%s]: OUTPUT STREAM\n%s\n') % ( time.strftime("%H:%M:%S"), output) )
        if err:
            fout.write( ('DATA-PIPELINE [%s]: ERROR STREAM\n%s\n') % ( time.strftime("%H:%M:%S"), err) )

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
                        database.append( os.path.basename(chunk_output_file) )
                else:
                    database.append( os.path.basename(chunk_output_file) )
                # and save it again ...
                with open(OUTPUT_FILE, 'wb') as database_out:
                    pickle.dump(database, database_out, pickle.HIGHEST_PROTOCOL)
            except Exception as e:
                fout.write( str(e) )
                pass

        # release lock to give the chance to another thread
        try:
            if os.path.exists(chunk_output_file):
                lock.release() # this is in a try because when invoked on an unlocked lock, a ThreadError is raised.
        except Exception as e:
            fout.write( str(e) )
            pass

        fout.write( ('DATA-PIPELINE [%s]: FRAMES PROCESSING DONE\n') % ( time.strftime("%H:%M:%S")) )

    except Exception as e:
        # log the exception and leave
        fout.write('\n***********************************\n')
        fout.write('FACE-PIPELINE [%s]: EXCEPTION %s\n' % ( time.strftime("%H:%M:%S"), e.message ) )
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
    LOG_OUTPUT_FILE = os.path.join( tempfile.gettempdir(), 'prepro_input_%d.log' % index )
    fout = open( LOG_OUTPUT_FILE, 'w', buffering=1)
    new_files_list = ""
    output = ""
    err = ""

    try:

        if input_list_of_videos:
            fout.write( ('DATA-PIPELINE [%s]: PREPROCESSING A LIST OF %d VIDEOS\n') % ( time.strftime("%H:%M:%S"), len(input_list_of_videos) ) )
        else:
            raise Exception('Cannot process an empty list of videos !')

        video_list = input_list_of_videos
        video_list.sort()

        for video_path in video_list:

            video_base_name = os.path.basename(video_path)
            tmp_chunk_output_file =  os.path.join( tempfile.gettempdir() , video_base_name + '.pkl')
            pOpenCmd = [
                    COMPUTE_POSITIVE_FEATURES_SCRIPT,
                    'video',
                    video_path,
                    DATASET_IM_BASE_PATH,
                    tmp_chunk_output_file
                ]
            p = Popen(pOpenCmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
            output, err = p.communicate()
            splitted_output = None
            if err:
                fout.write( ('DATA-PIPELINE [%s]: ERROR STREAM\n%s\n') % ( time.strftime("%H:%M:%S"), err) )
            if output:
                fout.write( ('DATA-PIPELINE [%s]: OUTPUT STREAM\n%s\n') % ( time.strftime("%H:%M:%S"), output) )
                splitted_output = output.split('\n')

            if os.path.exists(tmp_chunk_output_file) and splitted_output:

                currentLineCount = 0
                newLineCount = 0

                ### LOCK
                # acquire lock to get exclusive access to the code below
                lock.acquire()
                try:
                    # Create/modify frame list file (a.k.a. DATASET_IM_PATHS)
                    fout.write( ('DATA-PIPELINE [%s]: INSERTING FRAME LIST INTO: %s\n') % (time.strftime("%H:%M:%S"), DATASET_IM_PATHS) )
                    with open(DATASET_IM_PATHS, "a+") as datasetImgsFile:
                        for counter, line in enumerate(datasetImgsFile):
                            currentLineCount = currentLineCount + 1
                        fout.write( ('DATA-PIPELINE [%s]: NUMBER OF FRAMES IN CURRENT FRAME LIST FILE: %d\n') % (time.strftime("%H:%M:%S"), currentLineCount)  )
                        newLineCount = currentLineCount
                        for line in splitted_output:
                            if len(line)>0 and ('.jpg' in line): # if COMPUTE_POSITIVE_FEATURES_SCRIPT was successful,
                                                                 # lines with added files must terminate in ".jpg"
                                line = line.strip()
                                newLineCount = newLineCount + 1
                                encodeFrameName = line.encode("utf-8")
                                datasetImgsFile.write(encodeFrameName)
                                datasetImgsFile.write('\n')

                    fout.write( ('DATA-PIPELINE [%s]: NUMBER OF FRAMES IN NEW FRAME LIST FILE: %d\n') % (time.strftime("%H:%M:%S"), newLineCount))
                    # copy tmp output features to features folder
                    chunk_output_file = OUTPUT_FILE.replace('.pkl', '-%d_%d.pkl' % (currentLineCount,newLineCount) )
                    shutil.move( tmp_chunk_output_file, chunk_output_file)

                    # append the new features to the database
                    database = []
                    if os.path.exists(OUTPUT_FILE):
                        # load the existing list ....
                        with open(OUTPUT_FILE, 'rb') as database_in:
                            database = pickle.load(database_in)
                            database.append( os.path.basename(chunk_output_file) )
                    else:
                        database.append( os.path.basename(chunk_output_file) )

                    # and save it again ...
                    with open(OUTPUT_FILE, 'wb') as database_out:
                        pickle.dump(database, database_out, pickle.HIGHEST_PROTOCOL)

                except Exception as e:
                    fout.write( str(e) )
                    pass

                # release lock to give the chance to another thread
                try:
                    lock.release() # this is in a try because when invoked on an unlocked lock, a ThreadError is raised.
                except Exception as e:
                    fout.write( str(e) )
                    pass

                ### UNLOCK

    except Exception as e:
        # log the exception and leave
        fout.write('\n***********************************\n')
        fout.write('FACE-PIPELINE [%s]: EXCEPTION %s\n' % ( time.strftime("%H:%M:%S"), e.message ) )
        fout.write(err)
        pass

    fout.close()

# Data pipeline definition
def data_processing_pipeline_faces(inputListOfFrames, input_type, index, lock, DATASET_IM_BASE_PATH, DATASET_IM_PATHS, OUTPUT_FILE):
    """ Performs the ingestion of new data into the backend search engine. The data can be videos or images (frames). The type of
        input should be indicated by the input_type variable.
        If the input type is 'images' and a python list of frames is input, the paths in the list must be RELATIVE to the
        DATASET_IM_BASE_PATH path. This method does not validate that.
        If the input type is 'videos' the list of input paths must contain the FULL paths to the videos. This method will extract
        frames from the video and automatically copy them in a sub-folder within DATASET_IM_BASE_PATH. The videos must be
        reachable within the system. This method does not validate that.
        Arguments:
            inputListOfFrames: Python list of paths to the frame images or video files.
            input_type: one of two strings: 'images' or 'videos', indicating the type of input referenced in inputListOfFrames.
            index: iteration number, for when this method is called multiple times. Used for naming the output log file.
            lock: python multi-threading lock object
            DATASET_IM_PATHS: Path to the file containing the location of all images previously ingested by the backend search engine.
            DATASET_IM_BASE_PATH: Base path to the images referenced by the backend search engine.
            OUTPUT_FILE: Path to the final output features file.
    """
    if input_type=='video':
        inputListOfVideos = inputListOfFrames
        data_processing_pipeline_faces_videos(inputListOfVideos, index, lock, DATASET_IM_BASE_PATH, DATASET_IM_PATHS, OUTPUT_FILE)

    if input_type=='images':
        data_processing_pipeline_faces_images(inputListOfFrames, index, lock, DATASET_IM_BASE_PATH, DATASET_IM_PATHS, OUTPUT_FILE)

#Test invocation for image ingestion
#lock = threading.Lock()
#inputListOfFrames = [ 'pic00001.jpg', 'pic00002.jpg', 'pic00005.jpg', 'pic00007.jpg']
#DATASET_IM_PATHS = '/webapps/visorgen/face_search/test/images.txt'
#DATASET_IM_BASE_PATH = '/webapps/visorgen/face_search/test/images'
#OUTPUT_FILE = '/webapps/visorgen/face_search/test/features/database.pkl'
#data_processing_pipeline_faces(inputListOfFrames, 'images', 0, lock, DATASET_IM_BASE_PATH, DATASET_IM_PATHS, OUTPUT_FILE)

#Test invocation for video ingestion
#lock = threading.Lock()
#inputListOfVideos = [ '/webapps/visorgen/face_search/test/videos/big_buck_bunny_240p_2mb.mp4']
#DATASET_IM_PATHS = '/webapps/visorgen/face_search/test/images.txt'
#DATASET_IM_BASE_PATH = '/webapps/visorgen/face_search/test/images'
#OUTPUT_FILE = '/webapps/visorgen/face_search/test/features/database.pkl'
#data_processing_pipeline_faces(inputListOfVideos, 'video', 0, lock, DATASET_IM_BASE_PATH, DATASET_IM_PATHS, OUTPUT_FILE)
