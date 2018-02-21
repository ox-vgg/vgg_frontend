import time
import os
import sys
from subprocess import Popen, PIPE
import threading
import pickle

# Add the path to the vgg_face_search feature computation
file_dir = os.path.dirname(os.path.realpath(__file__))
COMPUTE_POSITIVE_FEATURES_SCRIPT = os.path.join(file_dir,'../../vgg_face_search/pipeline/start_pipeline.sh' )

# Data pipeline definition
def data_processing_pipeline_faces(inputListOfFrames, index, lock, DATASET_IM_BASE_PATH, DATASET_IM_PATHS, OUTPUT_FILE):

    # Create/clear the log file
    LOG_OUTPUT_FILE = '/tmp/prepro_input_%d.log' % index
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
            new_files_list = '/tmp/faces_new_%d.log' % index
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
            # if the file was created sucessfully
            ### LOCK
            lock.acquire()
            try:
                database = []
                if os.path.exists(OUTPUT_FILE):
                    # load the existing list ....
                    with open(OUTPUT_FILE, 'rb') as database_in:
                        database = pickle.load(database_in)
                        database.append(chunk_output_file)
                else:
                    database.append(chunk_output_file)
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

#Test invocation
#lock = threading.Lock()
#inputListOfFrames = [ 'pic00001.jpg', 'pic00002.jpg', 'pic00005.jpg', 'pic00007.jpg']
#DATASET_IM_PATHS = '/webapps/visorgen/face_search/test/images.txt'
#DATASET_IM_BASE_PATH = '/webapps/visorgen/face_search/test/images'
#OUTPUT_FILE = '/webapps/visorgen/face_search/test/features/database.pkl'
#data_processing_pipeline_faces(inputListOfFrames, 0, lock, DATASET_IM_PATHS, DATASET_IM_BASE_PATH, OUTPUT_FILE)

