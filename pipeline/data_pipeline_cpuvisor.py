__author__      = 'Ernesto Coto'
__copyright__   = 'Nov 2016'

# Imports
import os
import sys
from subprocess import Popen, PIPE
import threading
import time
import tempfile

# Some constants
CPUVISOR_BIN_PATH = os.path.join(os.path.dirname(__file__), '..' , '..', 'vgg_classifier', 'bin')
cpuvisor_preproc = os.path.join(CPUVISOR_BIN_PATH,'cpuvisor_preproc')
cpuvisor_append_chunk = os.path.join(CPUVISOR_BIN_PATH,'cpuvisor_append_chunk')

def preproc_chunk_thread(startIndex, endIndex, lock, feat_type, CONFIG_PROTO_PATH):

    fout = None

    try:

        # Create/clear the log file
        LOG_OUTPUT_FILE = os.path.join( tempfile.gettempdir(), 'chunk_%d-%d.log' % (startIndex, endIndex) )
        fout = open( LOG_OUTPUT_FILE, 'w',  buffering=1)
        fout.write( ('DATA-PIPELINE [%s]: PREPROCESSING CHUNK %d-%d\n') % (time.strftime("%H:%M:%S"),startIndex, endIndex) )

        # check feature type
        feat_type_param = '-dsetfeats'
        if feat_type == 'negative':
            feat_type_param = '-negfeats'
        fout.write( ('DATA-PIPELINE [%s]: FEATURE TYPE %s\n') % ( time.strftime("%H:%M:%S"), str(feat_type) ))

        # execute cpuvisor_preproc
        pOpenCmd = [cpuvisor_preproc, '-config_path', CONFIG_PROTO_PATH, feat_type_param, '-startidx', str(startIndex), '-endidx', str(endIndex)]
        fout.write( ('DATA-PIPELINE [%s]: EXECUTING %s\n') % ( time.strftime("%H:%M:%S"), str(pOpenCmd) ))
        p = Popen(pOpenCmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        output, err = p.communicate()
        #fout.write(err)
        # extract filename from cpuvisor_preproc output
        # NB: We use STDERR for the code below because google::InitGoogleLogging is
        #     not used in the cpuvisor_* executables,
        #     hence sending the output logs to STDERR
        lastPathIndex = err.rfind('.binaryproto')
        firstPathIndex = err.rfind(' ', 0, lastPathIndex) + 1
        newChunkFile = err[firstPathIndex:lastPathIndex] + '.binaryproto'
        newChunkFile = newChunkFile.strip()

        ### LOCK
        # acquire lock to get exclusive access to the code below
        lock.acquire()

        # only execute append if the positive features are being computed
        if feat_type != 'negative':
            # execute cpuvisor_append_chunk
            fout.write( ('DATA-PIPELINE [%s]: APPENDING %s TO CURRENT CHUNK INDEX\n') % ( time.strftime("%H:%M:%S"), newChunkFile) )
            pOpenCmd = [cpuvisor_append_chunk, '-config_path', CONFIG_PROTO_PATH, '-chunk_file', newChunkFile ]
            fout.write( ('DATA-PIPELINE [%s]: EXECUTING %s\n') % ( time.strftime("%H:%M:%S"), str(pOpenCmd) ))
            p = Popen(pOpenCmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
            output, err = p.communicate()
            #fout.write(err)

    except Exception as e:
        # log the exception and leave
        if fout:
            fout.write( ('DATA-PIPELINE [%s]: EXCEPTION %s\n') % ( time.strftime("%H:%M:%S"), e.message))
        pass

    # release lock to give the chance to another thread
    try:
        lock.release() # this is in a try beacuse when invoked on an unlocked lock, a ThreadError is raised.
    except Exception as e:
        fout.write( str(e) )
        pass
        ### UNLOCK

    if fout:
        fout.close()

def data_processing_pipeline_cpuvisor(inputListOfFrames, index, lock, feat_type, DATASET_IM_BASE_PATH, DATASET_IM_PATHS, CONFIG_PROTO_PATH, PREPROC_CHUNK_SIZE):
    """ Performs the ingestion of new data into the backend search engine.
        If a python list of frames is input, the paths must be with respect to the DATASET_IM_BASE_PATH path. This method does not validate that.
        Arguments:
            inputListOfFrames: Python list of paths to the frame images
            index: iteration number, for when this method is called multiple times. Used for naming the output log file.
            lock: python multi-threading lock object
            feat_type: one of two strings: 'positive' or 'negative', indicating que type of feature to compute
            CONFIG_PROTO_PATH: Path to the config.prototxt file of the backend search engine.
            PREPROC_CHUNK_SIZE: Size of the chunks in which list of frames will be divided.
            DATASET_IM_BASE_PATH: Base path to the images referenced by the backend search  engine.
            DATASET_IM_PATHS: Path to the file containing the location of all images previously ingested by the backend search engine.
    """

    # Create/clear the log file
    LOG_OUTPUT_FILE = os.path.join( tempfile.gettempdir(), 'prepro_input_%d.log' % index )
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

        # Start processing chunks
        startIndex = currentLineCount
        chunk_size = min(PREPROC_CHUNK_SIZE, newLineCount-currentLineCount)

        # Use a common lock to guarantee each thread has exclusive access to the DATASET_IM_PATHS file
        local_threads_map = {}
        while (startIndex < newLineCount):
            endIndex = min(startIndex + chunk_size, newLineCount)
            fout.write( ('DATA-PIPELINE [%s]: STARTING PROCESSING THREAD FOR CHUNK %d-%d\n') % (time.strftime("%H:%M:%S"), startIndex, endIndex) )
            t = threading.Thread(target=preproc_chunk_thread, args=(startIndex, endIndex, lock, feat_type, CONFIG_PROTO_PATH) )
            t.start()
            local_threads_map[str(t.ident)] = t
            startIndex = endIndex

        # check the status of the threads
        finishedThreadCounter = 0
        while (finishedThreadCounter < len(local_threads_map)):
            localCounter = 0
            for thread_id in local_threads_map:
                if not local_threads_map[thread_id].is_alive():
                    localCounter = localCounter + 1
            fout.write(  ('DATA-PIPELINE [%s]: NUMBER OF THREADS FINISHED: %d\n') % (time.strftime("%H:%M:%S"),localCounter) )
            time.sleep(2)
            finishedThreadCounter = localCounter

        fout.write( ('DATA-PIPELINE [%s]: ALL DONE WITH LIST OF %d FRAMES\n') % ( time.strftime("%H:%M:%S"), len(inputListOfFrames)) )

    except Exception as e:
        # log the exception and leave
        fout.write('\n***********************************\n')
        fout.write('DATA-PIPELINE [%s]: EXCEPTION %s\n' % ( time.strftime("%H:%M:%S"), e.message ) )
        fout.write(err)
        pass

    fout.close()

######### The code below can be useful for testing or to perform data ingestion via the command-line
#lock = threading.Lock()
#CONFIG_PROTO_PATH= 'something'
#DATASET_IM_BASE_PATH = 'something'
#DATASET_IM_PATHS = 'something'
#CHUNK_SIZE = 50000 # divide the list of paths in smaller chunks
#all_lines = []
#group = []
#with open(DATASET_IM_PATHS) as fin:
    #for line in fin:
        #if len(line)>0:
            #line = line.replace('\n','')
            #if len(group)<CHUNK_SIZE:
                #group.append(line)
            #else:
                #all_lines.append(group)
                #group=[]
                #group.append(line)

#all_lines.append(group)
#for index in range(len(all_lines)):
    #chunk_start = CHUNK_SIZE*int(index)
    #print 'Processing chuck %d-%d' % ( chunk_start, chunk_start+CHUNK_SIZE-1)
    #data_processing_pipeline( all_lines[index] , index, lock, 'positive', DATASET_IM_BASE_PATH, DATASET_IM_PATHS + '.copy', CONFIG_PROTO_PATH, CHUNK_SIZE)
