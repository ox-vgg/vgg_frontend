import time
import os
import sys
from subprocess import Popen, PIPE
import threading

# Add the path to the vgg_face_search feature computation
file_dir = os.path.dirname(os.path.realpath(__file__))
COMPUTE_POSITIVE_FEATURES_SCRIPT = os.path.join(file_dir,'../../vgg_face_search/pipeline/start_pipeline.sh' )

# Data pipeline definition
def data_processing_pipeline_faces(inputListOfFrames, lock, DATASET_IM_PATHS, DATASET_IM_BASE_PATH, OUTPUT_FILE):



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

        pOpenCmd = [
                COMPUTE_POSITIVE_FEATURES_SCRIPT,
                DATASET_IM_BASE_PATH,
                NEW_FILES_LIST, # use just the new files, the script will append them to the previous
                OUTPUT_FILE
            ]
        fout.write( ('FACE-PIPELINE [%s]: %s\n') % ( time.strftime("%H:%M:%S"), str(pOpenCmd)) )
        p = Popen(pOpenCmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        output, err = p.communicate()
        if output:
            fout.write( ('FACE-PIPELINE [%s]: OUTPUT STREAM\n%s\n') % ( time.strftime("%H:%M:%S"), output) )
        if err:
            fout.write( ('FACE-PIPELINE [%s]: ERROR STREAM\n%s\n') % ( time.strftime("%H:%M:%S"), err) )
        fout.write( ('FACE-PIPELINE [%s]: FRAMES PROCESSING DONE\n') % ( time.strftime("%H:%M:%S")) )

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
#OUTPUT_FILE = '/webapps/visorgen/face_search/test/features/database.pkl'
#data_processing_pipeline_faces(inputListOfFrames, lock, DATASET_IM_PATHS, DATASET_IM_BASE_PATH, OUTPUT_FILE)

