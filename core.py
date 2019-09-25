from sys import platform
from pathlib import Path
from threading import Thread
from queue import Queue
from subprocess import Popen, PIPE
from enum import Enum
import prctl

import threading
import datetime
import subprocess
import logging
import time
import os
#import meta_search

# Priority queue for sending data/info/messages to threads
message_Logging_Queue = Queue()
subprocessQueue = Queue()
subprocessCommandQueue = Queue()
disk_Check_Queue = Queue()

# Queues to pass data/results back from subprocess/diskCheck threads
subprocessResultsQueue = Queue()
diskCheckResultsQueue = Queue()
returned_Data_Queue = Queue()

# Setting up logging config
logging.basicConfig(level=logging.DEBUG,format='(%(threadName)-10s) %(message)s',)


## App configs

# Home path
USER_HOME = str(Path.home())

platform_lunix = False

# Application debug log file
DEFAULT_OUTPUT_FILE_NAME = 'debug.log'
# MakeMkvcon progress log (rip %)
DEFUALT_PROGRESS_FILE = 'progress.log'
# MakeMkvcon Messages log (Basically its log file)
DEFAULT_MESSAGES_FILE ='messages.log'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Root logs directory
DEFAULT_OUTPUT_LOG_DIR = os.path.join(BASE_DIR, 'logs/')
# Devices sub directory
DEFAULT_DEVICES_LOG_DIR = DEFAULT_OUTPUT_LOG_DIR+'devices/'
# Jobs sub directory
DEFAULT_JOBS_LOG_DIR = DEFAULT_OUTPUT_LOG_DIR+'jobs/'
# MakeKkvcon Message file log
DEFAULT_OUTPUT_FILE_PATH = DEFAULT_OUTPUT_LOG_DIR
DEFAULT_MESSAGES_FILE_RELATIVE_PATH = DEFAULT_OUTPUT_FILE_PATH+DEFAULT_MESSAGES_FILE
# MakeMkvcon Progress file log
DEFAULT_PROGRESS_FILE_DIR = DEFAULT_OUTPUT_FILE_PATH
DEFAULT_PROGRESS_FILE_RELATIVE_PATH = DEFAULT_PROGRESS_FILE_DIR+DEFUALT_PROGRESS_FILE

test_message_file = "--messages=/media/phantom/My Files/Documents/Python Projects/Emgee_Core/logs/messages.log"
test_progress_file = "--progress=/media/phantom/My Files/Documents/Python Projects/Emgee_Core/logs/progress.log"
test_profile_file = "--profile=/media/phantom/My Files/Documents/Python Projects/Emgee_Core/phantoms.mmcp.xml"

# Setting custom profile for makemkv to use
makeMkv_profile_dir = BASE_DIR
makeMkv_profile_file = 'phantoms.mmcp.xml' #This is some profile to match your ripping requirements
makeMkv_profile_options = '--profile=' + makeMkv_profile_dir+'/'+makeMkv_profile_file

# Setting --progress & --messages command args for makemkv to use
makeMkv_progress_command = '--progress="'+DEFAULT_PROGRESS_FILE_RELATIVE_PATH+'"'
makeMkv_messages_option = '--messages="'+DEFAULT_MESSAGES_FILE_RELATIVE_PATH+'"'

# Setting MakeMkv target media folder
makeMkv_media_dest_dir = '/media/media/Rips'


# Command to rip first title on dev:/dev/sr01 using profile
# makemkvcon --profile=makeMkv_profile_dir + makeMkv_profile_file+"mkv dev:/dev/sr0 0 /media/media/Rips"


# Search parameters:
search_bluray = True
search_Dvd = True
search_Cd = True
search_altDvd = True

global found_bray
global found_dvd

found_alt_dvd = False
found_cd = False

# Device objects
br_Device_Object = None
dvd_Device_Object = None
cd_Device_Object = None

# Device Arrays
BR_Device_List = {}
DVD_Device_List = {}
CD_Device_List = {}

titles = []
found_titles = {}
titles_cached = {} # { drive_path: True/False if scanned, }

# Formatting / Debug log values
app_log_mesg = "|Media_Grabber| "
make_log_mesg = "<<Makemkvcon>> "
handbrake_log_mesg = "<<[Handbrake>]> "

CLEAR_LOGS_ONSTART = True
CLEAR_DRIVE_LOGS_ONSTART = True


# Inserted disc
newDisc = ''

# Exit variables

SHUTDOWN_TRIGGERED = False

def get_current_timestamp_footer():
    # End notes on log files upon app exit
    CURRENT_TIMESTAMP = get_current_timestamp()
    LOG_FILE_EXIT_FOOTER = "=== Media Grabber (Emgee) application exit @ " + CURRENT_TIMESTAMP + " ==="
    return LOG_FILE_EXIT_FOOTER

def get_current_timestamp():
    # Used to get timestamp
    return str(datetime.datetime.now())

# def return_str_tracks(dictionary):
#     titles = dict(dictionary).keys()
#     all_titles_str = ""
#     for title in titles:
#         all_titles_str += title
#         title_value = dict(dictionary).get(title)
#         all_titles_str += "\n "+title_value
#     return all_titles_str


class disc_metaData(object):

    MEDIA_TYPE = ["Blu-ray disc","DVD","CD"]
    MEDIA_CONTENT = ["MOVIE","TV","MUSIC", "OTHER"]
    class MEDIA_TYPE(Enum):
        BR = "Blu-ray disc"
        DVD = "DVD"
        CD = "CD"

    class CINFO_INDEX(Enum):
        Media_Type = 1
        Media_Title = 2
        Media_Lang = 28
        Media_Lang_Name = 29
        Media_Title_Name = 30

    class TINFO_INDEX(Enum):
        Track_Title = 2
        Track_Chapters = 8
        Track_length = 9
        Track_file_size = 10
        Track_file_name = 27
        Track_Lang = 28
        Track_Lang_Name = 29

    def __init__(self, result):
        self.MediaType_Found = False
        self.raw = result
        self.title_tracks_number = 0
        self.main_title_index = -1
        self.video_tracks = {}
        self.sound_tracks = {}
        self.disc_info_raw = []
        self.media_type = ""
        self.movie_name = ""
        self.series_name = ""
        #Disc meta data
        self.name = ""
        self.lang = ""
        #Below for Movie meta data
        self.movie_durration = ""
        self.movie_length = ""
        self.movie_chapters = ""
        self.movie_size = ""
        self.movie_file_name = ""
        self.movie_main_lang = ""
        print(self.raw)
        self.meta_parse(self.raw)

    def get_All_Movie_sTracks(self):
        if self.main_title_index is not -1:
            return self.sound_tracks.get("Title:"+str(self.main_title_index))
        raise ValueError("The Main Title has not been set!",str(self.main_title_index))


    def get_movie_Name(self):
        return self.movie_name

    def get_movie_Chapters(self):
        return self.movie_chapters

    def get_movie_Length(self):
        return self.movie_length

    def get_movie_Size(self):
        return self.movie_size

    def get_movie_File_Name(self):
        return self.movie_file_name

    def get_movie_Lang(self):
        return self.movie_main_lang

    def get_Media_Type(self):
        print("Media type found to be:",str(self.media_type))
        return self.media_type

    def update_Main_Title(self, title_num):
        self.main_title_index = title_num
        line_count = 0
        track_lines = dict(self.get_VideoTrackObject().get("Title:" + title_num)).values()
        for line in track_lines:
            #print("line_count:",line_count,line)
            index_value = int(str(line).split(':')[1].split(',')[1])
            meta_value = str(line).split(',')[-1]
            #print(">>>>>>>> index_value:",index_value,"meta_value:",meta_value)

            if int(index_value) is int(self.TINFO_INDEX.Track_Title.value):
                self.movie_name = meta_value.replace('"', '')
                print("Movie name:", self.movie_name)

            elif int(index_value) is int(self.TINFO_INDEX.Track_Chapters.value):
                self.movie_chapters = meta_value.replace('"', '')
                print("Movie chapters:", self.movie_chapters)

            elif int(index_value) is int(self.TINFO_INDEX.Track_length.value):
                self.movie_length = meta_value.replace('"', '')
                print("Movie length:", self.movie_length)

            elif int(index_value) is int(self.TINFO_INDEX.Track_file_size.value):
                self.movie_size = meta_value.replace('"', '')
                print("Movie file size:", self.movie_size)

            elif int(index_value) is int(self.TINFO_INDEX.Track_file_name.value):
                self.movie_file_name = meta_value.replace('"', '')
                print("Movie file name:", self.movie_file_name)

            elif int(index_value) is int(self.TINFO_INDEX.Track_Lang.value):
                self.movie_main_lang = meta_value.replace('"', '')
                print("Movie lang:", self.movie_main_lang)

            line_count += 1


    def meta_parse(self, data):
        temp_vList = {}
        temp_sList = {}
        split_lines = data.split("\n")
        MAX_LINES = len(split_lines)
        index = 0
        while index < MAX_LINES:
            # First check "MSG:" and string "Operation successfully completed"
            line = split_lines[index]

            if str(split_lines[index]).__contains__("MSG:") and str(split_lines[index]).__contains__("Operation successfully completed"):
                # Check trailing TCOUNT line
                # First saftey check for index out of range


                if str(split_lines[index+1]).__contains__("TCOUNT"):
                    self.title_tracks_number = str(split_lines[index + 1]).split(":")[1]
                    print(self.title_tracks_number + " Title tracks found")
                    index += 2

            while str(split_lines[index]).__contains__("CINFO:"):
                index_value = int(str(split_lines[index]).split(':')[1].split(',')[0])
                meta_value = str(split_lines[index]).split(',')[-1]
                if int(index_value) is int(self.CINFO_INDEX.Media_Type.value):
                    if meta_value.__contains__(str(self.MEDIA_TYPE.BR.value)):
                        print("Detected media type!!!!")
                        self.media_type = str(self.MEDIA_TYPE.BR.name).replace('"','')
                        self.MediaType_Found = True

                if int(index_value) is int(self.CINFO_INDEX.Media_Title.value):
                    self.name = meta_value.replace('"','')
                    print("Disc name:",self.name)
                elif int(index_value) is int(self.CINFO_INDEX.Media_Lang.value):
                    self.lang = meta_value.replace('"','')
                    print("Disc main lang:",self.lang)

                self.disc_info_raw.append(str(split_lines[index]))
                index += 1

            title_track_line_num = 0
            current_title_number = 0
            if str(split_lines[index]).__contains__("INFO:"):
                print("Pre_check:"+str(split_lines[index]))

            while str(split_lines[index]).__contains__("TINFO:"):
                current_title_number = int(str(split_lines[index]).split(":")[1].split(",")[0])
                print(str(split_lines[index]))
                temp_vList[str(title_track_line_num)] = str(split_lines[index])
                title_track_line_num += 1
                index += 1

                if str(split_lines[index]).__contains__("TINFO:") is not True:
                    self.video_tracks["Title:" + str(current_title_number)] = temp_vList.copy()
                    temp_vList.clear()
                    title_track_line_num = 0

            sound_title_track_line_num = 0
            while str(split_lines[index]).__contains__("SINFO:"):

                current_sound_title_number = int(str(split_lines[index]).split(":")[1].split(",")[0])
                current_sound_track_number = int(str(split_lines[index]).split(":")[1].split(",")[1])
                while str(split_lines[index]).__contains__(":"+str(current_sound_title_number)+","+str(current_sound_track_number)) is True:
                    #Add to track dictionary.
                    temp_sList[str(sound_title_track_line_num)] = str(split_lines[index])
                    index += 1
                    sound_title_track_line_num += 1

                if self.sound_tracks.keys().__contains__("Title:" + str(current_sound_title_number)) is not True:

                    self.sound_tracks["Title:" + str(current_sound_title_number)] = {}
                    if dict(self.sound_tracks.get("Title:" + str(current_sound_title_number))).keys().__contains__("Track:" + str(current_sound_track_number)) is not True:
                        self.sound_tracks["Title:" + str(current_sound_title_number)][
                            "Track:" + str(current_sound_track_number)] = {}
                        self.sound_tracks["Title:" + str(current_sound_title_number)][
                            "Track:" + str(current_sound_track_number)] = temp_sList.copy()
                    else :
                        self.sound_tracks["Title:" + str(current_sound_title_number)]["Track:" + str(current_sound_track_number)] = temp_sList.copy()
                    sound_title_track_line_num = 0
                    temp_sList.clear()

                else :
                    self.sound_tracks["Title:" + str(current_sound_title_number)][
                        "Track:" + str(current_sound_track_number)] = temp_sList.copy()
                    sound_title_track_line_num = 0
                    temp_sList.clear()


            if str(split_lines[index]).__contains__("TINFO:"):
                continue
            else :
                index += 1

    def print_VideoTrackInfo(self):

        returned_title_string = "\n\nTINFO objects: \n\n"+str(self.video_tracks.keys())
        for key in self.video_tracks.keys():
            returned_title_string += "\n" + str(self.video_tracks.get(key))
        return returned_title_string

    def get_VideoTrackObject(self):
        return self.video_tracks

    def print_SoundTrackInfo(self):
        returned_sound_track_string = "\n\nSINFO objects: \n\n" + str(self.sound_tracks.keys())
        for key in self.sound_tracks.keys():
            returned_sound_track_string += "\n"+key
            for item in dict(self.sound_tracks.get(key)).keys():
                returned_sound_track_string += "\n-Track: "+str(item)+"\n"+str(dict(self.sound_tracks.get(key)).get(item))
        return returned_sound_track_string

    def print_Main_Title_SoundTracksInfo_Summary(self):
        if self.main_title_index is -1:
            raise ValueError("The Main Title has not been set!",str(self.main_title_index))
        titleIndex = "Title:"+str(self.main_title_index)
        returned_sound_track_string = "\n"+titleIndex+"\n"+"Sound Tracks: "+str(dict(self.sound_tracks.get(titleIndex)).keys())
        return returned_sound_track_string

    def print_Main_Title_SoundTracksInfo(self):
        if self.main_title_index is -1:
            raise ValueError("The Main Title has not been set!",str(self.main_title_index))
        titleIndex = "Title:"+str(self.main_title_index)
        returned_sound_track_string = "\n"+titleIndex
        for item in dict(self.sound_tracks.get(titleIndex)).keys():
            returned_sound_track_string += "\n-Track: "+str(item)+"\n"+str(dict(self.sound_tracks.get(titleIndex)).get(item))
        return returned_sound_track_string

    def print_DiskInfo(self):
        returned_string = "\n\nCINFO object:\n\n"
        for item in self.disc_info_raw:
            returned_string += "\n"+str(item)
        return returned_string

class device_Object(object):
    """
    Device object
    - Hold info about a optical device that is found on host machine
    """
    def __init__(self, data):
        '''
        Strips out raw data into usable variables
        :param data: the raw data as input

        NOTE:   This holds UUID, path and device name.
                Also hold basic details about current loaded disc, such as Title, and isRipped & isCached flags.
                IMPORTANT: THIS DOESN'T HOLD DISC METADATA OR TITLE INFO!!!
        '''

        '''
        Drive scan message format
        DRV:index,visible,enabled,flags,drive name,disc name,disc path
        index - drive index [0]
        visible - set to 1 if drive is present <-- same as enabled? [?]
        enabled - set to 1 if drive is accessible <-- same as visible? [?]
        flags - media flags, see AP_DskFsFlagXXX in apdefs.h <---- 999 seems default! [?]
        drive name - drive name string [4]
        disc name - disc name string [5]
        drive path - drive path string [6]
        '''
        self.data = str(data).split(',')
        self.driveID = self.data[0]
        # 2nd Value Unknown
        # 3rd Value Unknown
        # 4th Value Unknown
        self.deviceName = self.data[4]
        self.deviceTitle = self.data[5]
        self.devicePath = self.data[6]
        self.uuid = ""
        self.cached = False
        self.ripped = False
        self.raw = ""

    def getName(self):
        return self.deviceName

    def setRaw(self, dataString):
        self.raw = dataString

    def getPath(self):
        return self.devicePath

    def getTitle(self):
        if len(self.deviceTitle) > 2:
            logging.info("({} - {}) Has title: {}".format(self.devicePath, self.deviceName, self.deviceTitle))
            return self.deviceTitle
        logging.info("({} - {}) Has no title".format(self.devicePath, self.deviceName))
        return False


    def setTitle(self, title):
        self.deviceTitle = title

    def setUUID(self, id):
        self.uuid = id

    def getUUID(self):
        if len(self.uuid) > 2:
            logging.info("[Object-Device]({} - {}) Has UUID: {}".format(self.devicePath, self.deviceName, self.uuid))
            return self.uuid
        logging.info("[Object-Device]({} - {}) Has no UUID".format(self.devicePath, self.deviceName))
        return False

    def setIsRipped(self,isRipped):
        self.ripped = isRipped

    def isRipped(self):
        return self.ripped

    def setIsCached(self,isCached):
        self.cached = isCached

    def isCached(self):
        return self.cached

    def __str__(self):
        returned = ""
        for index in range(len(self.data)):
            returned += self.data[index] + "\n"
        return returned
    def print_Short_Raw(self):
        '''
        Prints out the raw values to a string (No added comments etc)
        :return: A string with the raw output values
        '''
        returned_value = "{},{},{},{},{}".format(self.driveID,self.deviceName,self.devicePath,self.uuid,self.deviceTitle)
        return returned_value


def grab_largest_titles_Size(titles_list):
    #Using a sort algorithm.
    #No need for super efficient algorithm. Only will contain max of 100 titles (Rarely)
    titlesList = dict(titles_list).copy()
    '''
    titlesList structure:
    
    titlesList { 'Title:#1' :  
                    
                            { 'line:#1' : line_data,
                              'line:#2' : line_data,
                              'line:#3' : line_data,
                              'line:#n' : line_data,
                             } ,
                      
                            { 'line:#1' : line_data,
                              'line:#2' : line_data,
                              'line:#3' : line_data,
                              'line:#n' : line_data,
                             } ,
                    } ,
                  'Title:#2' :  
                    
                            { 'line:#1' : line_data,
                              'line:#2' : line_data,
                              'line:#3' : line_data,
                              'line:#n' : line_data,
                             } ,
                       
                            { 'line:#1' : line_data,
                              'line:#2' : line_data,
                              'line:#3' : line_data,
                              'line:#n' : line_data,
                             } ,
                    } ,
                }
    #To iterate over Line# and line data per Track in each title:
    titles_list.get("title#") returns title dict {}
    titles_list.get("title#").keys() returns list of keys for Tracks in title.
    titles_list.get("title#").get("Track#) returns dict of lines for track.
    titles_list.get("title#").get("Track#).iterator
    
    '''
    return_summary_dict = {}

    #Find file size parameter
    # Note: is around the 10th line description loop through and grab correct lines

    for title_index in range(len(titlesList)):
        temp_Title_object = titlesList.get("Title:"+str(title_index))
        # Next need to loop through the titles dict/array and find example: 'TINFO:0,10,0,"4.1 GB"'
        # Note: this looks to be the 2-3 index, under line marked 'TINFO:x,10,x ; "value"'
        for internal_title_index in range(len(temp_Title_object)):
            track_size = str(dict(temp_Title_object).get(str(internal_title_index))).split(",")[3]
            if track_size.__contains__("GB") or track_size.__contains__("MB"):
                #remove other characters
                track_size = track_size.replace('"',"").replace("\'","").replace(" ","")
                #WE found it!
                if track_size.__contains__("GB"):
                    print("Before: "+track_size)
                    track_size = track_size.replace("GB","")
                    print("After: " + track_size)
                    track_size_float = float(track_size)*1000
                elif track_size.__contains__("MB"):
                    print("Before: " + track_size)
                    track_size = track_size.replace("MB", "")
                    print("After: " + track_size)
                    track_size_float = float(track_size)
                return_summary_dict[title_index] = track_size_float
                print("Title: "+str(title_index)+" Line "+str(internal_title_index),dict(temp_Title_object).get(str(internal_title_index))," Found size: "+str(track_size_float))
                track_size_float = 0
            
    return return_summary_dict

def order_largest_tracks(data_dictionary):
    '''Dictionary structured:
        { track# 0: file_size, track# 1: file_size, .... track# n+1: file_size }
    '''
    return_ordered_dictionary = dict(data_dictionary).copy()


    return sorted(return_ordered_dictionary, key=return_ordered_dictionary.get, reverse=True)

# def print_Tracks_Array(ordered_titles):
#     titles_array = list(ordered_titles).copy()
#     returned_title_string = "\n\nTINFO objects: \n\n"+str(titles_array)
#     for index in range(0,len(titles_array)):
#         returned_title_string += "\n" + str(titles_array[index])
#     return returned_title_string

class main_logging_thread_Class(threading.Thread):
    def __init__(self):
        super(main_logging_thread_Class, self).__init__()
        self.loggingThread = Thread(target=self.run)
        self._stop = threading.Event()
        self.loggingThread.name = "loggingThread"
        prctl.set_name("loggingThread")
        logging.info("Logging Class Initialized!")

    def stop(self):
        print(">>> Stop has been called on Logging thread! <<<")
        self._stop.set()

    def stopped(self):

        return self._stop.isSet()

    def run(self):
        logging.info("[Running] Logging Class Running!")
        while self.stopped() is not True:
            #message = message_Logging_Queue.get()
            #logging.info("Checing queue..")
            logging.debug("[Blocking] Logging thread waiting on: logging Queue.get() call!")
            try:
                log = message_Logging_Queue.get()
            #print("[2] logging Queue.get() has returned")
            except Queue.Empty:
                log = None
            if log is not None:
                logging.info(log)
                #print("[3] About to write to log file")
                self.write_to_log(log[0],log[1])
            #print("[4] Finished writing to log file")
            message_Logging_Queue.task_done()
            logging.debug("[Released] Logging thread Queue.get() call released!")
            #print("[5] Queue task is done!")
            if SHUTDOWN_TRIGGERED is True and main_drive_check_thread.is_alive() is not True:
                self.stop()
                logging.info("[Termination] Logging thread stop triggered!")

            logging.debug("[Pre-Check] Logging Thread checked for call to terminate")
            #logging.info("logging done!")

        logging.debug("Printing EOF: " + get_current_timestamp_footer())
        self.write_to_log(get_current_timestamp_footer(),"")
        self.stop()
        logging.info("[END] Logging thread stopped!")

    def write_to_log(self, debug_mesg, data):
        '''
            Assumes data is Array or string.
            Check which type then parses data to be written to log file.
            # Basically separating by new lines for log.
            Returns data of lines held in each index of new array.
        '''
        if type(data) is str:
            cleanData = data
            if data.startswith('b\''):
                '''
                Removing starting b\' from the string. Starting new substring at index 2.
                Removing trailing ' by stopping a character (index) short.
                '''
                cleanData = data[2:len(data) - 1]
            with open(DEFAULT_OUTPUT_FILE_PATH + DEFAULT_OUTPUT_FILE_NAME, 'a') as f:
                formatted_Array = cleanData.split('\\n')
                for nextline in formatted_Array:
                    f.write(debug_mesg + nextline + "\n")
                #returned_Data_Queue.put(formatted_Array)
                f.close()
        elif type(data) is object:
            pass


def start() :
    message_Logging_Queue.put((app_log_mesg,"----------------\n"))
    message_Logging_Queue.put((app_log_mesg,"Starting App...\n"))


    #TODO Figure out simple thread to handle disc insert on any drive See below details (Line 588)
    '''
        TODO
        Currently the programe handle tasks semi-synchronously.
        Most threads are asynchronus, but the program terminates on finding no disks after running.
        Need to setup another thread that starts at run, and waits on disk insert, then triggers other threads/function
        to read specific or all devices for new media.
        
        Once disc found, then need to handle the titles as normal.
        Program needs to "wait" for shutdown/terminal call, before stopping.
        *May need to setup a batch script to do this via command line call to function etc.
    '''
    '''[START] Refactor/re-write code'''    #<----------------- START
    #Wait on receving data
    '''
    if diskCheckResultsQueue.empty() is False :
        logging.debug("[Blocking]{diskCheckResultsQueue} Start blocking on return call from diskCheckResultsQueue.get()")
        returned_data = diskCheckResultsQueue.get()
        logging.debug(
            "[Released]{diskCheckResultsQueue} Start released from call to diskCheckResultsQueue.get()")
    #print("Returned data: "+returned_data)
        newDisc = disc_metaData(returned_data)
        start_title_rip(newDisc)

    else :
        results = diskCheckResultsQueue.get()
        logging.debug(
            "[Released]{diskCheckResultsQueue} :: INFO ::")
        print(results)
        logging.debug(
            "[Released]{diskCheckResultsQueue} :: ERROR :: Start released from diskCheckResultsQueue.get()!")
        diskCheckResultsQueue.task_done()

    newDisc.meta_parse(newDisc.raw)'''
    
    logging.debug("[END] Start function finished!")

    #[END] Refactor/re-write code  #<------------------- END

def start_title_rip(newDisc):

    print("===Media Type confirmed: ", newDisc.get_Media_Type(), "===")
    # print(tempObject.print_DiskInfo())
    # print(tempObject.print_VideoTrackInfo())
    print(newDisc.print_SoundTrackInfo())

    size_dict = grab_largest_titles_Size(newDisc.get_VideoTrackObject())

    print("Summarized title list [Un-ordered]", size_dict)
    ordered_list = order_largest_tracks(size_dict)
    print("Ordered indexes [Based on file size]: " + str(ordered_list))

    tracks_list = newDisc.get_VideoTrackObject()
    main_title = tracks_list.get("Title:" + str(ordered_list[0]))
    print("Largest title is", str(main_title))

    ''' 
        Usefull info:

        - Movie title/name
        - durration hh:mm:ss
        - # of Chapters
        - Size
        - file name
        - Language

        *Need to grab details from title track [done]
        *Also need to grab sTracks number and index start range [done]

    '''
    newDisc.update_Main_Title(str(ordered_list[0]))
    print(newDisc.movie_name)
    #print(meta_search.imdb_search(newDisc.get_movie_Name()))

    selected_title_index = ordered_list[0]
    '''if selected_title_index < 10 :
        selected_title_index = str(selected_title_index).zfill(1)
    print("Selected track:",selected_title_index)'''
    make_rip_command = ['makemkvcon', makeMkv_profile_options, makeMkv_messages_option, makeMkv_progress_command, 'mkv',
                        'disc:' + str(0), str(selected_title_index),makeMkv_media_dest_dir]
    test_rip_command = ['makemkvcon',test_profile_file, test_message_file, test_progress_file, 'mkv', 'disc:' + str(0), str(selected_title_index), makeMkv_media_dest_dir]
    disc = 0
    print(test_rip_command)
    subprocessCommandQueue.put(test_rip_command)
    rip_subprocess_thread = main_subprocess_thread_Class()
    rip_subprocess_thread.setName("rip_subprocess_thread")
    rip_subprocess_thread.subprocess_thread.start()
    results = subprocessResultsQueue.get()
    subprocessResultsQueue.task_done()
    print(results)

"""
    Drive checking thread.
    - Currently this is checking queue of devices.
    - Also is looping untill stopped. Need to change this to 
    just check and then terminate once done.
"""
class main_drive_check_thread_Class(threading.Thread):
    def __init__(self):
        super(main_drive_check_thread_Class, self).__init__()
        self.drive_Check_Thread = Thread(target=self.run)
        self._stop = threading.Event()
        self.drive_Check_Thread.name = "driveCheckThread"
        logging.info("driveCheck Thread Class Initialized!")

    def stop(self):
        self._stop.set()
        logging.info("[Termination] Return drive check thread stop triggered!")

    def stopped(self):
        return self._stop.isSet()

    def run(self):

        logging.info("[Running] driveCheck Thread Class started!")
        logging.debug("[Blocking] driveCheck Thread Blocking on call to disk_Check_Queue.get() {BRs}!")
        devices_to_check = disk_Check_Queue.get()
        logging.debug("[Released] driveCheck Thread released on call to disk_Check_Queue.get()! {BRs}")
        message_Logging_Queue.put([app_log_mesg, "Devices to check... {}".format(devices_to_check)])
        message_Logging_Queue.put([app_log_mesg, "checking devices {}".format(devices_to_check)])
        message_Logging_Queue.put([app_log_mesg, devices_to_check])
        if disk_Check_Queue.empty() is False :
            logging.debug("[Blocking] driveCheck Thread Blocking on call to disk_Check_Queue.get()! {DVDs}")
            dvd_devices_to_check = disk_Check_Queue.get()
            logging.debug("[Released] driveCheck Thread released on call to disk_Check_Queue.get()! {DVDs}")
            message_Logging_Queue.put([app_log_mesg, "Devices to check... {}".format(dvd_devices_to_check)])
            message_Logging_Queue.put([app_log_mesg, "checking devices {}".format(dvd_devices_to_check)])
            message_Logging_Queue.put([app_log_mesg, dvd_devices_to_check])
        disk_Check_Queue.task_done()
        result = ''

        while not self.stopped():
            itemCount = 0
            for item in devices_to_check:
                print("item {} : {}".format(itemCount,item))
                itemCount += 1

            for device in devices_to_check:
                # Running through devices to find discs
                device_value = devices_to_check[device]
                message_Logging_Queue.put([app_log_mesg, "Checking device... " + str(device_value)])
                #print("checking disk/drive {}", device_value)
                formatted_device_string = device_value.devicePath.replace("\"", "")
                check_for_disk_command = ['blkid', '' + formatted_device_string]
                message_Logging_Queue.put([app_log_mesg, "Running command ... " + str(check_for_disk_command)])
                subprocessCommandQueue.put(check_for_disk_command)
                main_subprocess_thread = main_subprocess_thread_Class()
                main_subprocess_thread.subprocess_thread.start()
                logging.debug("[Blocking]{Subprocess} driveCheck Thread Blocking on call to subprocessResultsQueue.get()!")
                disk_check_first = subprocessResultsQueue.get()
                print("Blkid",formatted_device_string,"return:",disk_check_first)
                if disk_check_first is "" :
                    print("Disk check returned nothing: ",disk_check_first)
                else :
                    subprocessResultsQueue.task_done()
                    #Format of return string: /dev/sr0: UUID="3b2fabba00000000" LABEL="PUBLIC_ENEMIES" TYPE="udf"
                    # path: UUID="" LABEL="" TYPE=""
                    if device_value.getUUID() is False :
                        split_string = disk_check_first.split(" ")
                        parsed_uuid = split_string[1].split('"')[1]
                        parsed_title = split_string[2].split('"')[1]
                        device_value.setUUID(parsed_uuid)
                        device_value.setTitle(parsed_title)
                        print("Testing presets: {}".format(device_value.print_Short_Raw()))
                    if device_value.isCached() is False :
                        logging.debug("[Released]{Subprocess} driveCheck Thread Released on call to subprocessResultsQueue.get()!")
                        message_Logging_Queue.put([app_log_mesg,"Scanning disk: "+disk_check_first])
                        make_disco_info_command = ['makemkvcon', '-r', '--cache=1', 'info',
                                                   'dev:' + formatted_device_string,makeMkv_profile_options, makeMkv_progress_command]
                        message_Logging_Queue.put([app_log_mesg, "Make run command on dev: test path: " + str(make_disco_info_command)])
                        logging.info("Make run command on dev: test path: " + str(make_disco_info_command))
                        subprocessCommandQueue.put(make_disco_info_command)
                        main_subprocess_thread = main_subprocess_thread_Class()
                        main_subprocess_thread.subprocess_thread.start()
                        logging.debug("[Blocking]{Subprocess} driveCheck Thread Blocking on call to subprocessResultsQueue.get()!")
                        result = subprocessResultsQueue.get()
                        subprocessResultsQueue.task_done()
                        logging.debug("[Released]{Subprocess} driveCheck Thread Released on call to subprocessResultsQueue.get()!")
                        message_Logging_Queue.put([make_log_mesg, result])
                        device_value.setRaw(result)
                        device_value.setIsCached(True)
                        devices_to_check[device] = device_value
                        print("Checking cached title: {}".format(device_value.getTitle()))
                        write_uuid_log(device_value)
                        logging.info("[Done] Device {} : {} Is now Cached!".format(device_value.getPath(),
                                                                                       device_value.getName()))
                    else :
                        logging.info("[Done] Device {} : {} Is Already Cached!".format(device_value.getPath(),device_value.getName()))
                    #print("Results printout after logging... >>> \n",result)
                    '''if diskCheckResultsQueue.empty() is False :
                        dumpObject = diskCheckResultsQueue.get()
                        logging.info("[Override] Disk check results queue...")'''
                    diskCheckResultsQueue.put(result)
            logging.info("[Sleeping] Disk check thread... 15s!")
            '''test_output = disc_metaData(result).print_DiskInfo()
            logging.info(">>>\n",test_output)'''
            time.sleep(15)

        logging.info("[END] Return drive check thread stopped!")

def clear_app_logs (driveLogs=CLEAR_DRIVE_LOGS_ONSTART) :
    with open(DEFAULT_OUTPUT_FILE_PATH + DEFAULT_OUTPUT_FILE_NAME, 'w') as f :
        f.truncate()
        f.close()
        logging.info("Debug log file cleared!")
    with open(DEFAULT_OUTPUT_FILE_PATH + DEFAULT_MESSAGES_FILE, 'w') as f :
        f.truncate()
        f.close()
        logging.info("Messaging log file cleared!")
    with open(DEFAULT_OUTPUT_FILE_PATH + DEFUALT_PROGRESS_FILE, 'w') as f :
        f.truncate()
        f.close()
        logging.info("Progress log file cleared!")

    if driveLogs :
        for file in os.listdir(DEFAULT_DEVICES_LOG_DIR):
            print("found "+str(file))
            try :
                os.remove()
                print("{} Deleted".format(str(file)))
            except Exception as e:
                print("Error deleting device log files!",e)




def check_app_files():
    #TODO Need to check for required log files to run application. Create if not found!
    '''
        /logs:
        messages.log
        progress.log
        debug.log

        /logs/devices/
        *UUID logs go in here once new device found* suffix .log
        /logs/jobs/
        *Ripp/encode job logs go in here*

        print("makeMkv_profile_dir", makeMkv_profile_dir)
        print("makeMkv_profile_file", makeMkv_profile_file)
        print("makeMkv_profile_options", makeMkv_profile_options)
        print("makeMkv_media_dest_dir", makeMkv_media_dest_dir)
    '''
    #First check base dirs
    #try :
    if os.path.isdir(DEFAULT_OUTPUT_LOG_DIR) is False :
        print("/logs NOT Found!")
        '''
        Create all of the things:
        /logs/debug.log
        /logs/messages.log
        /logs/progress.log
        /logs/devices/
        /logs/jobs/
        '''
        print("Creating /logs base directory...")
        os.makedirs(DEFAULT_OUTPUT_LOG_DIR)
        print("Creating /logs/"+DEFAULT_OUTPUT_FILE_NAME+" file...")
        mainlog = open(DEFAULT_OUTPUT_LOG_DIR+DEFAULT_OUTPUT_FILE_NAME, "w")
        mainlog.write("")
        mainlog.close()
        print("Creating /logs/" + DEFAULT_MESSAGES_FILE + " file...")
        messagelog = open(DEFAULT_OUTPUT_LOG_DIR+DEFAULT_MESSAGES_FILE, "w")
        messagelog.write("")
        messagelog.close()
        print("Creating /logs/" + DEFUALT_PROGRESS_FILE + " file...")
        progresslog = open(DEFAULT_OUTPUT_LOG_DIR+DEFUALT_PROGRESS_FILE, "w")
        progresslog.write("")
        progresslog.close()

        print("Creating /logs/devices base directory...")
        os.makedirs(DEFAULT_OUTPUT_LOG_DIR+'devices')
        print("Creating /logs/jobs base directory...")
        os.makedirs(DEFAULT_OUTPUT_LOG_DIR + 'jobs')

    else :
        print("/logs Directory Found!")

        if os.path.isdir(DEFAULT_OUTPUT_LOG_DIR + "/devices") is False:
            print("/logs/devices NOT Found!")
            print("Creating /logs/devices base directory...")
            os.makedirs(DEFAULT_OUTPUT_LOG_DIR + 'devices')
        else:
            print("/logs/devices Directory Found!")
        if os.path.isdir(DEFAULT_OUTPUT_LOG_DIR+"/jobs") is False:
            print("/logs/jobs NOT Found!")
            print("Creating /logs/jobs base directory...")
            os.makedirs(DEFAULT_OUTPUT_LOG_DIR + 'jobs')
        else:
            print("/logs/jobs Directory Found!")

        if os.path.isfile(DEFAULT_OUTPUT_LOG_DIR+DEFAULT_OUTPUT_FILE_NAME) is False:
            print("Creating /logs/" + DEFAULT_OUTPUT_FILE_NAME + " file...")
            mainlog = open(DEFAULT_OUTPUT_LOG_DIR + DEFAULT_OUTPUT_FILE_NAME, "w")
            mainlog.write("")
            mainlog.close()
        else :
            print("/logs/"+DEFAULT_OUTPUT_FILE_NAME + " file found!")

        if os.path.isfile(DEFAULT_OUTPUT_LOG_DIR+DEFAULT_MESSAGES_FILE) is False:
            print("Creating /logs/" + DEFAULT_MESSAGES_FILE + " file...")
            mainlog = open(DEFAULT_OUTPUT_LOG_DIR + DEFAULT_MESSAGES_FILE, "w")
            mainlog.write("")
            mainlog.close()
        else:
            print("/logs/" + DEFAULT_MESSAGES_FILE + " file found!")

        if os.path.isfile(DEFAULT_OUTPUT_LOG_DIR+DEFUALT_PROGRESS_FILE) is False:
            print("Creating /logs/" + DEFUALT_PROGRESS_FILE + " file...")
            mainlog = open(DEFAULT_OUTPUT_LOG_DIR + DEFUALT_PROGRESS_FILE, "w")
            mainlog.write("")
            mainlog.close()
        else :
            print("/logs/"+DEFUALT_PROGRESS_FILE + " file found!")

    #except IOError:
    #    print("Some Exception checking directories:")


def create_file(filename,data=""):
    #TODO
    pass

def write_uuid_log(drive):
    """ Writing out device logs to a file using uuid value as name.

    This function saves usefull state information regarding the device to a file, using its specific uuid.
    Note: Mainly a future proofing move, as currently not referencing device state from file,
     as it is in application memory/cache.

    Parameters
    ----------
    drive : device_Object, required
            Object containing all parameters, and current state information.

    Returns
    -------
    N/A

    ++++++++++
    UUID.log file Structure details below.

    Filename uses device uuid -> "uuid##.log"
    File contents start with device details in first two (2) lines, then third (3rd) line onwards is device state logs.

    path:"/dev/sr0"
    name:"BD-RE Test Device"

    *Following lines start with timestamp then, Title, Cached(True/False), Ripped(True/False)
    "2019-06-23 17:42:06.5634234","BATMAN","False","False"
    Format update lines with surrounded quotes " (Double quotes) and separate with , (Commas).

    """

    # Checkg DriveObject is correct type
    if type(drive) is device_Object :
        if os.path.isfile(DEFAULT_DEVICES_LOG_DIR+drive.uuid+'.log') is False :
            print(drive.uuid + ".log doesn't exist! Creating new file...")
            '''Create new file:
                *For new lines, first two are details on device. 
                path:"/dev/sr0"
                name:"BD-RE Test Device"
                *Following lines are timestamps with task done, Scanned(True/False), Ripped(True/False)
                "2019-06-23 17:42:06.5634234","False","False"
                Format update lines with surrounded quotes " (Double quotes) and separate with , (Commas).
            '''
            with open(DEFAULT_DEVICES_LOG_DIR+drive.uuid+'.log', 'w') as file :
                outputString = 'path:{}\nname:{}\n"{}","{}","{}","{}"'.format(str(drive.getPath()),str(drive.getName()),get_current_timestamp(),str(drive.getTitle()),str(drive.isCached()),str(drive.isRipped()))
                file.write(outputString)
                file.close()
            print("...completed")
        else :
            print(drive.uuid+'.log exists!')
            print("updating...")
            with open(DEFAULT_DEVICES_LOG_DIR+drive.uuid+'.log', 'a') as file :
                outputString = '\n"{}","{}","{}","{}"'.format(get_current_timestamp(),str(drive.getTitle()),str(drive.isCached()),str(drive.isRipped()))
                file.write(outputString)
                file.close()
            print("...completed")


class main_subprocess_thread_Class(threading.Thread):
    """
        Subprocess Handler Thread

        This thread handles commands; send to, and results returned from, the command line.
        It reads the subprocessCommandQueue (Blocking get() call) and runs these commands.
        Once done it processes the results and finaly places them onto the subprocessResultsQueue
        for other threads to use.
        subprocessCommandQueue.task_done() is then called to free up Queue.
    """
    def __init__(self):
        super(main_subprocess_thread_Class, self).__init__()
        self.subprocess_thread = Thread(target=self.run)
        self._stop = threading.Event()
        self.subprocess_thread.name = "subprocess_thread"

    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()

    def run(self):
        logging.debug("[Blocking] Subprocess thread blocking on subprocessCommandQueue.get() call!")
        process = subprocessCommandQueue.get()
        logging.debug("[Released] Subprocess thread released from subprocessCommandQueue.get() call!")
        p = subprocess.Popen(process, stdout=PIPE)
        logging.debug(process)
        #while p.returncode is None:
        returned_data = (p.communicate()[0])

        message_Logging_Queue.put([app_log_mesg, "== Executed Command without error! =="])
        formatted_data = returned_data.decode('ascii').replace("'", "")
        subprocessResultsQueue.put(formatted_data)
        subprocessCommandQueue.task_done()
        logging.info("[END] Return subprocess thread stopped!")

'''
class main_disk_check_thread_class(threading.Thread):
    def __init__(self):
        super(main_disk_check_thread_class, self).__init__()
        self.main_disk_check_thread = Thread(target=self.run)
        self._stop = threading.Event()
        self.main_disk_check_thread.name = "main_disk_check_thread"
        logging.info("Disk check thread Class Initialized!")

    def stop(self):
        print(">>> Stop has been called on Disk Check thread! <<<")
        self._stop.set()

    def stopped(self):

        return self._stop.isSet()

    def run(self):
        logging.info("[Running] Disk Check Class Running!")
        while self.stopped() is not True:
            value = True
        logging.info("[END] Disk Check thread stopped!")
'''

def initialize(search_bluray=True,search_Dvd=True, search_Cd=False, search_altDvd = True) :
    """ Initialize function

        Checks OS type, Runs Make command to scan all drives.
        Determines drive type and Maps found drive to correct device Queue.

        Args:
            search_bluray: Blueray search Flag
            search_Dvd: Dvd search Flag
            search_Cd: CD search Flag
            search_altDvd: Alt DVD Flag (????)
    """
    check_app_files()
    print("folder tests: ")
    print("BASE_DIR", BASE_DIR)
    print("output_log_dir", DEFAULT_OUTPUT_LOG_DIR)
    print("output_file_path", DEFAULT_OUTPUT_FILE_PATH)
    print("job progress_file_dir", DEFAULT_PROGRESS_FILE_DIR)
    print("job progress_file_path", DEFAULT_PROGRESS_FILE_RELATIVE_PATH)
    print("makeMkv_profile_dir", makeMkv_profile_dir)
    print("makeMkv_profile_file", makeMkv_profile_file)
    print("makeMkv_profile_options", makeMkv_profile_options)
    print("makeMkv_media_dest_dir", makeMkv_media_dest_dir)


    #Check for subprocess module (Linux OS library)
    if platform == "linux" or platform == "linux2":
        platform_lunix = True
    elif platform == "darwin":
        # OS X
        platform_lunix = False
    elif platform == "win32":
        # Windows...
        platform_lunix = False
    elif platform == "cygwin":
        #cygwin
        platform_lunix = False

    if platform_lunix :
        clear_app_logs()
        message_Logging_Queue.put([app_log_mesg,"Lunix Platform OS detected..."])
        time.sleep(1)
        #newLog = LogMessage(app_log_mesg, "Grabbing Device/Drive info:")
        message_Logging_Queue.put([app_log_mesg, "Grabbing Device/Drive info:"])
        #newLog = LogMessage(app_log_mesg, "Lunix Platform OS detected...")
        message_Logging_Queue.put([app_log_mesg,"==============================="])
        find_devices_command = ["makemkvcon", "-r", "--cache=1", "info", "disc:9999",makeMkv_profile_options]
        subprocessCommandQueue.put(find_devices_command)
        main_subprocess_thread = main_subprocess_thread_Class()
        main_subprocess_thread.subprocess_thread.start()
        #create_folder()

        result = subprocessResultsQueue.get()
        subprocessResultsQueue.task_done()
        # Writing out to file after parsing and sanitizing, also return formatted array
        message_Logging_Queue.put((make_log_mesg, result))
        data = str(result).replace("'","")
        formatted_lines = data.split("\n")



    # Displaying result
    bray_dev = ""
    dvd_dev = ""
    cd_dev = ""
    alt_dvd = ""
    global found_bray
    found_bray = False
    global found_dvd
    found_dvd = False


    for index in range(0,len(formatted_lines)):
        working_Object = formatted_lines[index]
        if working_Object.__contains__("BDDVD") :
            found_bray = True
            br_Device_Object = device_Object(working_Object)
            bray_dev = working_Object
            BR_Device_List[br_Device_Object.devicePath] = br_Device_Object
            '''message_Logging_Queue.put(
                (app_log_mesg, "Found and Added BR device: " + BR_Device_List[br_Device_Object].deviceName + " @ path: " +
                 BR_Device_List[br_Device_Object].devicePath))
            
            message_Logging_Queue.put([app_log_mesg, br_Device_Object.print_Short_Raw()])'''
        elif working_Object.__contains__("DVD") :
            found_dvd = True
            dvd_Device_Object = device_Object(working_Object)
            DVD_Device_List[dvd_Device_Object.devicePath] = dvd_Device_Object
            dvd_dev = working_Object
            '''message_Logging_Queue.put(
                (app_log_mesg, "Found and Added DVD device: " + DVD_Device_List[dvd_Device_Object].deviceName + " @ path: " +
                 DVD_Device_List[dvd_Device_Object].devicePath))
            message_Logging_Queue.put([app_log_mesg, dvd_Device_Object.print_Short_Raw()])'''

    '''
    if found_bray :
        message_Logging_Queue.put([app_log_mesg,"Found Blu-Ray device!"])


    if found_dvd :
        message_Logging_Queue.put([app_log_mesg,"Found DVD device!"])
    '''

    #blkid /dev/sr0

    if BR_Device_List:
        message_Logging_Queue.put((app_log_mesg,"Checking BR devices for discs..."))
        disk_Check_Queue.put(BR_Device_List)

    if DVD_Device_List:
        message_Logging_Queue.put((app_log_mesg, "Checking DVD devices for discs..."))
        disk_Check_Queue.put(DVD_Device_List)

    start()
    print("Finished init!")


def trigger_Shutdown():
    """ Trigger_Shutdown function
        -   Sets shutdown flag.
        -   Application Threads detects flag and starts shutdown process
    """
    SHUTDOWN_TRIGGERED = True
    logging.info("User Triggered Shutdown! "+str(SHUTDOWN_TRIGGERED))
    main_application_thread.stop()


def shutdown():
    """ Trigger stopping of program
        - Waits untill drive check thread stopped first (Process heavy).
        - Stops/joins all threads and queues, and tidy's up.
    """
    print("Application thread exited, Main Drive Checked Thread Shutting down")
    while main_logging_thread.stopped() is not True:
        if main_drive_check_thread.stopped() is True:
            message_Logging_Queue.put("Terminating Programe")
            message_Logging_Queue.join()
            main_logging_thread.stop()

            message_Logging_Queue.put("Terminating logging queue")

    print("finished waiting on main_logging thread! Is not not alive")

    """
            Post run cleanup

            Make sure to tidy up and stop other threads once subprocess has stopped
            - Subprocess is longest running process/thread. Call to Stop this thread first,
            and wait for it to end then close other threads.
    """
    ### After stopping call join, on each thread, which waits to handle termination
    subprocessCommandQueue.join()
    logging.info("[SHUTDOWN] subprocessCommandQueue joined!")
    subprocessResultsQueue.join()
    logging.info("[SHUTDOWN] subprocessResultsQueue joined!")
    subprocessQueue.join()
    logging.info("[SHUTDOWN] subprocessQueue joined!")
    disk_Check_Queue.join()
    logging.info("[SHUTDOWN] disk_Check_Queue joined!")
    diskCheckResultsQueue.join()
    logging.info("[SHUTDOWN] diskCheckResultsQueue joined!")
    returned_Data_Queue.join()
    logging.info("[SHUTDOWN] returned_Data_Queue joined!")

    print("End of program!")

class main_application_thread_Class(threading.Thread):
    """
        Main Application Running Thread.

        This will handle all interfacing to user/automation of ripping, and encoding,
        and managing job threads.

        Currently in testing: Is just sleeping for 45 seconds (Enough to populate application cache etc) 
        and then shutdown.
    """
    def __init__(self):
        super(main_application_thread_Class, self).__init__()
        self.application_thread = Thread(target=self.run)
        self._stop = threading.Event()
        self.application_thread.name = "applicationThread"

    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()

    def run(self):
        message_Logging_Queue.put((app_log_mesg,"[START] Application thread starting up!"))
        print("Sleeping Application Thread (30 Seconds)")
        time.sleep(30)
        while self.stopped() is False:
            print("Sleeping Application Thread (15 Seconds)")
            time.sleep(15)
            '''for device in BR_Device_List :
                temp_device_Object = BR_Device_List[device]
                logging.debug("Device on path {}, with title {} chached status of {}".format(temp_device_Object.getPath(),temp_device_Object.getTitle(),temp_device_Object.isCached()))
                if temp_device_Object.isRipped() is False :
                    temp_device_Object.setIsRipped(True)
                    start_title_rip(temp_device_Object)'''
            # Wait on receving data
            '''
            if diskCheckResultsQueue.empty() is False :
                logging.debug("[Blocking]{diskCheckResultsQueue} Application_thread blocking on return call from diskCheckResultsQueue.get()")
                returned_data = diskCheckResultsQueue.get()
                logging.debug(
                    "[Released]{diskCheckResultsQueue} Application_thread released from call to diskCheckResultsQueue.get()")
            #print("Returned data: "+returned_data)
                newDisc = disc_metaData(returned_data)
                diskCheckResultsQueue.task_done()
                start_title_rip(newDisc)

            else :
                results = diskCheckResultsQueue.get()
                logging.debug(
                    "[Released]{diskCheckResultsQueue} :: INFO ::")
                #print(results)
                logging.debug(
                    "[Released]{diskCheckResultsQueue} :: ERROR :: Start released from diskCheckResultsQueue.get()!")
                diskCheckResultsQueue.task_done()'''

            #newDisc.meta_parse(newDisc.raw)
                    #TODO: Add to queue to be ripped by a ripping Thread. Set isRipped to True
            #TODO: Check rip Queue, and create/spawn another thread with new rip to process (Rip Job)
            '''
                Rip Jobs have logs associated with them.
                
                - The progress log
                - The messages log
                - The job/debug log
                
            '''
            """
                Below code a placeholder untill main logic implemented

                TODO: Need to loop over device UUID files/logs OR cache and find un-ripped titles.
                        Then proceed to create rip_threads to run makemkv on title/device.
                        Note: MUST limit one thread per device.
            """
            '''logging.debug("Checking SHUTDOWN_TRIGGERED: "+str(SHUTDOWN_TRIGGERED))
            if SHUTDOWN_TRIGGERED:
                logging.info("Shutting down")
                self.stop()'''
        #Proceed to shutdown process to exit application/program       
        message_Logging_Queue.put((app_log_mesg,"[END] Application thread stopped!"))
        #Need to manually trigger drive thread to stop
        main_drive_check_thread.stop()
        #Calling Shutdown function
        shutdown()

def start_app_Threads():
    main_application_thread.application_thread.start()

    main_drive_check_thread.drive_Check_Thread.start()

    main_logging_thread.loggingThread.start()

'''
    Commented out main_disk_check_thread_class as not currently in use
    TODO: Need to remove this in future

    #main_disk_check_thread_class = main_disk_check_thread_class()
'''

#Keep these here!
main_application_thread = main_application_thread_Class()
main_logging_thread = main_logging_thread_Class()
main_drive_check_thread = main_drive_check_thread_Class()


"""
Need to call functions in this order:
- start_app_Threads() <- When starting server [Remove this!]
- initialize() <- starts server logic
- [ start_server() ] <- Need to add this
When shutting down:
- shutdown()
"""




