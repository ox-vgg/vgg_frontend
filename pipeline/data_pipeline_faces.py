import time
import os
import sys
from subprocess import Popen, PIPE
import threading

# Get the path to this file
file_dir = os.path.dirname(os.path.realpath(__file__))

# Set MATLAB absolute path
MATLAB_RUN_TIME = '/usr/local/matlab/MCR_R2015b/v90'

# Set some relative paths
COMPUTE_POSITIVE_FEATURES_MATLAB_SCRIPT = os.path.join(file_dir,'../../face_search/pipeline/compute_pos_features/for_redistribution_files_only/run_compute_pos_features.sh')
COMPUTE_NEGATIVE_FEATURES_MATLAB_SCRIPT = os.path.join(file_dir,'../../face_search/pipeline/compute_neg_features/for_redistribution_files_only/run_compute_neg_features.sh')
FACE_TOOLS_PATH = os.path.join(file_dir,'../../face_search/tools')

# Enable/disable use of GPU for feature computation
USE_GPU_FLAG = '0' # Set to zero to disable

# Data pipeline definition
def data_processing_pipeline_faces(inputListOfFrames, lock, feat_type, DATASET_IM_PATHS, DATASET_IM_BASE_PATH, OUTPUT_MAT_FILE):

    PQ_ENCODER_CONTAINER = os.path.join(os.path.dirname(OUTPUT_MAT_FILE), 'pq_norm_pad.mat')

    # Create/clear the log file
    LOG_OUTPUT_FILE = '/tmp/prepro_input.log'
    NEW_FILES_LIST = '/tmp/faces_new.log'
    fout = open( LOG_OUTPUT_FILE, 'w', buffering=1)
    output = ""
    err = ""

    try:

        if inputListOfFrames:
            fout.write( ('DATA-PIPELINE [%s]: PREPROCESSING A LIST OF %d FRAMES\n') % ( time.strftime("%H:%M:%S"), len(inputListOfFrames) ) )
        else:
            raise Exception('Cannot process an empty list of frames !')

        # Frame path should be with respect to the DATASET_IM_PATHS folder
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
            with open(NEW_FILES_LIST, "w") as newFiles:
                for i in range(0, len(frameList) ):
                    encodeFrameName =  frameList[i].encode("utf-8")
                    newFiles.write(encodeFrameName)
                    newFiles.write('\n')
        except Exception as e:
            fout.write( str(e) )
            pass

        # release lock to give the chance to another thread
        try:
            lock.release() # this is in a try beacuse when invoked on an unlocked lock, a ThreadError is raised.
        except Exception as e:
            fout.write( str(e) )
            pass

        ### UNLOCK

        if feat_type == 'negative':

            pOpenCmd = [
                COMPUTE_NEGATIVE_FEATURES_MATLAB_SCRIPT,
                MATLAB_RUN_TIME,
                NEW_FILES_LIST, # use just the new files, the script will append them to the previous
                DATASET_IM_BASE_PATH,
                FACE_TOOLS_PATH,
                USE_GPU_FLAG,
                OUTPUT_MAT_FILE
            ]

        else:

            pOpenCmd = [
                COMPUTE_POSITIVE_FEATURES_MATLAB_SCRIPT,
                MATLAB_RUN_TIME,
                NEW_FILES_LIST, # use just the new files, the script will append them to the previous
                DATASET_IM_BASE_PATH,
                FACE_TOOLS_PATH,
                OUTPUT_MAT_FILE,
                PQ_ENCODER_CONTAINER,
                USE_GPU_FLAG
            ]

        fout.write( ('FACE-PIPELINE [%s]: %s\n') % ( time.strftime("%H:%M:%S"), str(pOpenCmd)) )
        p = Popen(pOpenCmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        output, err = p.communicate()
        if output:
            fout.write( ('FACE-PIPELINE [%s]: OUTPUT STREAM\n%s\n') % ( time.strftime("%H:%M:%S"), output) )
        if err:
            fout.write( ('FACE-PIPELINE [%s]: ERROR STREAM\n%s\n') % ( time.strftime("%H:%M:%S"), err) )
        fout.write( ('FACE-PIPELINE [%s]: VIDEO PROCESSING DONE\n') % ( time.strftime("%H:%M:%S")) )

    except Exception as e:
        # log the exception and leave
        fout.write('\n***********************************\n')
        fout.write('FACE-PIPELINE [%s]: EXCEPTION %s\n' % ( time.strftime("%H:%M:%S"), e.message ) )
        fout.write(err)
        pass

    fout.close()

#Test invocation
#lock = threading.Lock()
#inputListOfFrames = [ 'pic00001.jpg', 'pic00002.jpg', 'pic00005.jpg', 'pic00007.jpg']
#DATASET_IM_PATHS = '/webapps/visorgen/face_search/test/images.txt'
#DATASET_IM_BASE_PATH = '/webapps/visorgen/face_search/test/images'
#OUTPUT_MAT_FILE = '/webapps/visorgen/face_search/test/features/out.mat'
#feat_type = 'positive'
#data_processing_pipeline_faces(inputListOfFrames, lock, feat_type,m DATASET_IM_PATHS, DATASET_IM_BASE_PATH, OUTPUT_MAT_FILE)

