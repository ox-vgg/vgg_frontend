__author__      = 'Ernesto Coto'
__copyright__   = 'Nov 2016'

# Imports
import os
from subprocess import Popen, PIPE
import threading
import time
import tempfile

# Some constants
CPUVISOR_BIN_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'vgg_classifier', 'bin')
cpuvisor_preproc = os.path.join(CPUVISOR_BIN_PATH, 'cpuvisor_preproc')
cpuvisor_append_chunk = os.path.join(CPUVISOR_BIN_PATH, 'cpuvisor_append_chunk')

def preproc_chunk_thread(start_index, end_index, lock, feat_type, CONFIG_PROTO_PATH):
    """ Performs the ingestion of a set of images (a chunk)
        Arguments:
            start_index: start index (inclusive) of the set in the DATASET_IM_PATHS defined in the CONFIG_PROTO_PATH
            end_index: end index (exclusive) of the set in the DATASET_IM_PATHS defined in the CONFIG_PROTO_PATH
            lock: python multi-threading lock object
            feat_type: one of two strings: 'positive' or 'negative', indicating the type of feature to compute
            CONFIG_PROTO_PATH: Path to the config.prototxt file of the backend search engine.
    """

    fout = None

    try:

        # Create/clear the log file
        LOG_OUTPUT_FILE = os.path.join(tempfile.gettempdir(), 'chunk_%d-%d.log' % (start_index, end_index))
        fout = open(LOG_OUTPUT_FILE, 'w', buffering=1)
        fout.write(('DATA-PIPELINE [%s]: PREPROCESSING CHUNK %d-%d\n') % (time.strftime("%H:%M:%S"), start_index, end_index))

        # check feature type
        feat_type_param = '-dsetfeats'
        if feat_type == 'negative':
            feat_type_param = '-negfeats'
        fout.write(('DATA-PIPELINE [%s]: FEATURE TYPE %s\n') % (time.strftime("%H:%M:%S"), str(feat_type)))

        # execute cpuvisor_preproc
        popen_cmd = [cpuvisor_preproc, '-config_path', CONFIG_PROTO_PATH, feat_type_param, '-startidx', str(start_index), '-endidx', str(end_index)]
        fout.write(('DATA-PIPELINE [%s]: EXECUTING %s\n') % (time.strftime("%H:%M:%S"), str(popen_cmd)))
        popen_obj = Popen(popen_cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        output, err = popen_obj.communicate()
        output = output.decode()
        err = err.decode()
        #fout.write(err)
        # extract filename from cpuvisor_preproc output
        # NB: We use STDERR for the code below because google::InitGoogleLogging is
        #     not used in the cpuvisor_* executables,
        #     hence sending the output logs to STDERR
        last_path_index = err.rfind('.binaryproto')
        first_path_index = err.rfind(' ', 0, last_path_index) + 1
        new_chunk_file = err[first_path_index:last_path_index] + '.binaryproto'
        new_chunk_file = new_chunk_file.strip()

        ### LOCK
        # acquire lock to get exclusive access to the code below
        lock.acquire()

        # only execute append if the positive features are being computed
        if feat_type != 'negative':
            # execute cpuvisor_append_chunk
            fout.write(('DATA-PIPELINE [%s]: APPENDING %s TO CURRENT CHUNK INDEX\n') % (time.strftime("%H:%M:%S"), new_chunk_file))
            popen_cmd = [cpuvisor_append_chunk, '-config_path', CONFIG_PROTO_PATH, '-chunk_file', new_chunk_file]
            fout.write(('DATA-PIPELINE [%s]: EXECUTING %s\n') % (time.strftime("%H:%M:%S"), str(popen_cmd)))
            popen_obj = Popen(popen_cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
            output, err = popen_obj.communicate()
            output = output.decode()
            err = err.decode()
            #fout.write(err)

    except Exception as e:
        # log the exception and leave
        if fout:
            fout.write(('DATA-PIPELINE [%s]: EXCEPTION %s\n') % (time.strftime("%H:%M:%S"), str(e)))
        pass

    # release lock to give the chance to another thread
    try:
        lock.release() # this is in a try beacuse when invoked on an unlocked lock, a ThreadError is raised.
    except Exception as e:
        fout.write(str(e))
        pass
        ### UNLOCK

    if fout:
        fout.close()

def data_processing_pipeline_cpuvisor(input_list_of_frames, index, lock, feat_type, DATASET_IM_BASE_PATH, DATASET_IM_PATHS, CONFIG_PROTO_PATH, PREPROC_CHUNK_SIZE):
    """ Performs the ingestion of new data into the backend search engine.
        If a python list of frames is input, the paths must be with respect to the DATASET_IM_BASE_PATH path. This method does not validate that.
        Arguments:
            input_list_of_frames: Python list of paths to the frame images
            index: iteration number, for when this method is called multiple times. Used for naming the output log file.
            lock: python multi-threading lock object
            feat_type: one of two strings: 'positive' or 'negative', indicating the type of feature to compute
            CONFIG_PROTO_PATH: Path to the config.prototxt file of the backend search engine.
            PREPROC_CHUNK_SIZE: Size of the chunks in which list of frames will be divided.
            DATASET_IM_BASE_PATH: Base path to the images referenced by the backend search engine.
            DATASET_IM_PATHS: Path to the file containing the location of all images previously ingested by the backend search engine.
    """

    # Create/clear the log file
    LOG_OUTPUT_FILE = os.path.join(tempfile.gettempdir(), 'prepro_input_%d.log' % index)
    fout = open(LOG_OUTPUT_FILE, 'w', buffering=1)

    try:

        if input_list_of_frames:
            fout.write(('DATA-PIPELINE [%s]: PREPROCESSING A LIST OF %d FRAMES\n') % (time.strftime("%H:%M:%S"), len(input_list_of_frames)))
        else:
            raise Exception('Cannot process an empty list of frames !')

        # Frame path should be with respect to the DATASET_IM_PATHS folder
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
            current_line_count = 0
            if os.path.exists(DATASET_IM_PATHS):
                with open(DATASET_IM_PATHS, "r") as dataset_imgs_file:
                    for counter, line in enumerate(dataset_imgs_file):
                        current_line_count = current_line_count + 1
            fout.write(('DATA-PIPELINE [%s]: NUMBER OF FRAMES IN CURRENT FRAME LIST FILE: %d\n') % (time.strftime("%H:%M:%S"), current_line_count))
            with open(DATASET_IM_PATHS, "a+") as dataset_imgs_file:
                new_line_count = current_line_count
                for i in range(0, len(frame_list)):
                    new_line_count = new_line_count + 1
                    encode_frame_name = frame_list[i]
                    dataset_imgs_file.write(encode_frame_name)
                    dataset_imgs_file.write('\n')
            fout.write(('DATA-PIPELINE [%s]: NUMBER OF FRAMES IN NEW FRAME LIST FILE: %d\n') % (time.strftime("%H:%M:%S"), new_line_count))
        except Exception as e:
            fout.write(str(e))
            pass

        # release lock to give the chance to another thread
        try:
            lock.release() # this is in a try beacuse when invoked on an unlocked lock, a ThreadError is raised.
        except Exception as e:
            fout.write(str(e))
            pass

        ### UNLOCK

        # Start processing chunks
        start_index = current_line_count
        chunk_size = min(PREPROC_CHUNK_SIZE, new_line_count-current_line_count)

        # Use a common lock to guarantee each thread has exclusive access to the DATASET_IM_PATHS file
        local_threads_map = {}
        while start_index < new_line_count:
            end_index = min(start_index + chunk_size, new_line_count)
            fout.write(('DATA-PIPELINE [%s]: STARTING PROCESSING THREAD FOR CHUNK %d-%d\n') % (time.strftime("%H:%M:%S"), start_index, end_index))
            chunk_thread = threading.Thread(target=preproc_chunk_thread, args=(start_index, end_index, lock, feat_type, CONFIG_PROTO_PATH))
            chunk_thread.start()
            local_threads_map[str(chunk_thread.ident)] = chunk_thread
            start_index = end_index

        # check the status of the threads
        finished_thread_counter = 0
        while finished_thread_counter < len(local_threads_map):
            local_counter = 0
            for thread_id in local_threads_map:
                if not local_threads_map[thread_id].is_alive():
                    local_counter = local_counter + 1
            fout.write(('DATA-PIPELINE [%s]: NUMBER OF THREADS FINISHED: %d\n') % (time.strftime("%H:%M:%S"), local_counter))
            time.sleep(2)
            finished_thread_counter = local_counter

        fout.write(('DATA-PIPELINE [%s]: ALL DONE WITH LIST OF %d FRAMES\n') % (time.strftime("%H:%M:%S"), len(input_list_of_frames)))

    except Exception as e:
        # log the exception and leave
        fout.write('\n***********************************\n')
        fout.write('DATA-PIPELINE [%s]: EXCEPTION %s\n' % (time.strftime("%H:%M:%S"), str(e)))
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
    #print 'Processing chuck %d-%d' % (chunk_start, chunk_start+CHUNK_SIZE-1)
    #data_processing_pipeline(all_lines[index] , index, lock, 'positive', DATASET_IM_BASE_PATH, DATASET_IM_PATHS + '.copy', CONFIG_PROTO_PATH, CHUNK_SIZE)
