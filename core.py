from sys import platform
from pathlib import Path
from threading import Thread
from queue import Queue
from subprocess import Popen, PIPE

import threading
import datetime
import subprocess
import logging
import time
import os

message_Logging_Queue = Queue()
subprocessQueue = Queue()
subprocessReturnQueue = Queue()
disk_Check_Queue = Queue()


# special queues to pass data/results back from subprocess/diskCheck threads to main
subprocessResultsQueue = Queue()
diskCheckResultsQueue = Queue()


returned_Data_Queue = Queue()

logging.basicConfig(level=logging.INFO,format='(%(threadName)-10s) %(message)s',)

USER_HOME = str(Path.home())

platform_lunix = False

#Important thread classes


# App configs

# While still testing named "test.log. Change to "makemkvcon.log" later
output_file_name = 'test.log'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

output_log_dir = os.path.join(BASE_DIR, 'logs/') #'/logs'
output_file_path = output_log_dir

#Setting custom profile for makemkv to use
makeMkv_profile_dir = USER_HOME+"/.MakeMKV/"
makeMkv_profile_file = "phantoms.mmcp.xml" #This is some profile to match your ripping requirements
makeMkv_profile_options = "--profile=" + makeMkv_profile_dir + makeMkv_profile_file

makeMkv_media_dest_dir = "/media/media/Rips"

print("folder tests: ")
print("BASE_DIR",BASE_DIR)
print("output_log_dir",output_log_dir)
print("output_file_path",output_file_path)
print("makeMkv_profile_dir",makeMkv_profile_dir)
print("makeMkv_profile_file",makeMkv_profile_file)
print("makeMkv_profile_options",makeMkv_profile_options)
print("makeMkv_media_dest_dir",makeMkv_media_dest_dir)


#Command to rip first title on dev:/dev/sr01 using profile
#makemkvcon --profile=makeMkv_profile_dir + makeMkv_profile_file+"mkv dev:/dev/sr0 0 /media/media/Rips"


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

# Formatting / Debug log values
app_log_mesg = "|Media_Grabber| "
make_log_mesg = "<<Makemkvcon>> "
handbrake_log_mesg = "<<[Handbrake>]> "


# Exit variables

SHUTDOWN_TRIGGERED = False

def get_current_timestamp_footer():
    # End notes on log files upon app exit
    CURRENT_TIMESTAMP = str(datetime.datetime.now())
    LOG_FILE_EXIT_FOOTER = "=== Media Grabber (Emgee) application exit @ " + CURRENT_TIMESTAMP + " ==="
    return LOG_FILE_EXIT_FOOTER


def return_str_tracks(dictionary):
    titles = dict(dictionary).keys()
    all_titles_str = ""
    for title in titles:
        all_titles_str += title
        title_value = dict(dictionary).get(title)
        all_titles_str += "\n "+title_value
    return all_titles_str


class disc_metaData(object):

    def __init__(self, result):
        self.raw = result
        self.title_tracks_number = 0
        self.video_tracks = {}
        self.sound_tracks = {}
        self.disc_info = []
        print(self.raw)
        self.meta_parse(self.raw)


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
                self.disc_info.append(str(split_lines[index]))
                index += 1

            title_track_line_num = 0
            current_title_number = 0
            if str(split_lines[index]).__contains__("INFO:"):
                print("Pre_check:"+str(split_lines[index]))

            while str(split_lines[index]).__contains__("TINFO:"):
                #for cIndex in range(index,max_lines):

                #for cinfo_start_index in range(index,MAX_LINES):

                current_title_number = int(str(split_lines[index]).split(":")[1].split(",")[0])
                print(str(split_lines[index]))
                # print("Video title track: "+str(current_title_number))
                #while str(split_lines[index]).__contains__("TINFO:" + str(current_title_number)) is True:
                temp_vList[str(title_track_line_num)] = str(split_lines[index])
                title_track_line_num += 1
                index += 1
                '''if current_title_number < int(self.title_tracks_number):
                    temp_vList[str(title_track_line_num)] = str(split_lines[index])
                title_track_line_num += 1'''

                '''if str(split_lines[index+1]).__contains__("TINFO:") is not True:
                    self.video_tracks["Title:"+str(current_title_number)] = temp_vList.copy()
                
                    '''
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

    def return_VideoTrackInfo(self):

        returned_title_string = "\n\nTINFO objects: \n\n"+str(self.video_tracks.keys())
        for key in self.video_tracks.keys():
            returned_title_string += "\n" + str(self.video_tracks.get(key))
        return returned_title_string

    def return_VideoTrackObject(self):
        return self.video_tracks

    def return_SoundTrackInfo(self):
        returned_sound_track_string = "\n\nSINFO objects: \n\n" + str(self.sound_tracks.keys())
        for key in self.sound_tracks.keys():
            returned_sound_track_string += "\n"+key
            for item in dict(self.sound_tracks.get(key)).keys():
                returned_sound_track_string += "\n-Track: "+str(item)+"\n"+str(dict(self.sound_tracks.get(key)).get(item))
        return returned_sound_track_string

    def return_DiskInfo(self):
        returned_string = "\n\nCINFO object:\n\n"
        for item in self.disc_info:
            returned_string += "\n"+str(item)
        return returned_string

class device_Object(object):
    '''
    Device object
    - Hold info about a device that is found on computer
    '''
    def __init__(self, data):
        '''
        Strips out raw data into usable variables
        :param data: the raw data as input
        '''
        self.data = str(data).split(',')
        self.driveID = self.data[0]
        # 2nd Value Unknown
        # 3rd Value Unknown
        # 4th Value Unknown
        self.deviceName = self.data[4]
        # 6th Value Unknown
        self.devicePath = self.data[6]

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
        returned_value = "" + self.driveID + "," + self.deviceName + "," + self.devicePath
        return returned_value


def grab_largest_titles_Size(titles_list):
    #Using a selection sort algorithm.
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
        #print(str(temp_Title_object))
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
            

        #return_summary_dict[title_index] = titlesList

        temp_Title_object = ""

    '''for title_index in range(len(titlesList)):
        return_summary_dict[title_index] = titlesList
        print("TODO")'''


    return return_summary_dict

def order_largest_tracks(data_dictionary):
    '''Dictionary structured:
        { track# 0: file_size, track# 1: file_size, .... track# n+1: file_size }
    '''
    return_ordered_dictionary = dict(data_dictionary).copy()


    return sorted(return_ordered_dictionary, key=return_ordered_dictionary.get, reverse=True)

def print_Tracks_Array(ordered_titles):
    titles_array = list(ordered_titles).copy()
    returned_title_string = "\n\nTINFO objects: \n\n"+str(titles_array)
    for index in range(0,len(titles_array)):
        returned_title_string += "\n" + str(titles_array[index])
    return returned_title_string

class main_logging_thread_Class(threading.Thread):
    def __init__(self):
        super(main_logging_thread_Class, self).__init__()
        self.loggingThread = Thread(target=self.run)
        self._stop = threading.Event()
        self.loggingThread.name = "loggingThread"
        logging.info("Logging Class started!")

    def stop(self):
        print(">>> Stop has been called on Logging thread! <<<")
        self._stop.set()

    def stopped(self):

        return self._stop.isSet()

    def run(self):
        while self.stopped() is not True:
            #message = message_Logging_Queue.get()
            #logging.info("Checing queue..")
            print("[1] wainting on logging Queue.get()")
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
            #print("[5] Queue task is done!")
            if SHUTDOWN_TRIGGERED is True and main_drive_check_thread.is_alive() is not True:
                self.stop()
                print("___Logging thread stop triggered!")

            print("[6] Checked for termination")
            #logging.info("logging done!")

        print("Printing EOF: " + get_current_timestamp_footer())
        self.write_to_log(get_current_timestamp_footer(),"")
        self.stop()
        print("=>Logging thread End!<=")

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
            with open(output_file_path + output_file_name, 'a') as f:
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
    if BR_Device_List:
        for device in BR_Device_List :
            message_Logging_Queue.put((app_log_mesg,"Found and Added BR device: " + BR_Device_List[device].deviceName + " @ path: "+BR_Device_List[device].devicePath))

    if DVD_Device_List:
        for device in DVD_Device_List :
            message_Logging_Queue.put((app_log_mesg,"Found and Added DVD device: " + DVD_Device_List[device].deviceName + " @ path: " + DVD_Device_List[device].devicePath))

    #blkid /dev/sr0

    if BR_Device_List:
        message_Logging_Queue.put((app_log_mesg,"Checking BR devices for discs..."))
        disk_Check_Queue.put(BR_Device_List)

    if DVD_Device_List:
        message_Logging_Queue.put((app_log_mesg, "Checking DVD devices for discs..."))
        disk_Check_Queue.put(DVD_Device_List)

    #Wait on receving data
    returned_data = diskCheckResultsQueue.get()
    #print("Returned data: "+returned_data)
    newDisc = disc_metaData(returned_data)
    #newDisc.meta_parse(newDisc.raw)
    diskCheckResultsQueue.task_done()
'''
    Drive checking thread.
    - Currently this is checking queue of devices.
    - Also is looping untill stopped. Need to change this to 
    just check and then terminate once done.
'''
class main_drive_check_thread_Class(threading.Thread):
    def __init__(self):
        super(main_drive_check_thread_Class, self).__init__()
        self.drive_Check_Thread = Thread(target=self.run)
        self._stop = threading.Event()
        self.drive_Check_Thread.name = "driveCheckThread"

        logging.info("driveCheck Thread Class started!")

    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()

    def run(self):
        while not self.stopped():
            devices_to_check = disk_Check_Queue.get()
            message_Logging_Queue.put([app_log_mesg, "Devices to check... {}".format(devices_to_check)])
            message_Logging_Queue.put([app_log_mesg,"checking devices {}".format(devices_to_check)])
            message_Logging_Queue.put([app_log_mesg, devices_to_check])
            disk_Check_Queue.task_done()

            #<<<--------Trigger shutdown went here! [Bellow commented out]
            print("___Return drive check thread stop triggered!")

            """Example of subprocess call
            find_devices_command = ["makemkvcon", "-r", "--cache=1", "info", "disc:9999",makeMkv_profile_options]
            subprocessReturnQueue.put(find_devices_command)
            main_return_subprocess_thread = main_return_subprocess_thread_Class()
            main_return_subprocess_thread.subprocess_return_thread.start()
            

            result = subprocessResultsQueue.get()
            subprocessResultsQueue.task_done()
            """

            for item in devices_to_check:
                print(item)
            for device in devices_to_check:
                # Running through devices to find discs
                device_value = devices_to_check[device]
                message_Logging_Queue.put([app_log_mesg, "Checking device... " + str(device_value)])
                #print("checking disk/drive {}", device_value)
                formatted_device_string = device_value.devicePath.replace("\"", "")
                check_for_disk_command = ['blkid', '' + formatted_device_string]
                message_Logging_Queue.put([app_log_mesg, "Running command ... " + str(check_for_disk_command)])
                subprocessReturnQueue.put(check_for_disk_command)
                main_return_subprocess_thread = main_return_subprocess_thread_Class()
                main_return_subprocess_thread.subprocess_return_thread.start()
                disk_check_first = subprocessResultsQueue.get()
                subprocessResultsQueue.task_done()
                message_Logging_Queue.put([app_log_mesg,"Scanning disk: "+disk_check_first])
                """disk_check_echo = run_subprocess_command(['echo','$?'])
                returnCode = disk_check_first[1]
                #print(check_for_disk_command, "returned:", disk_check_first[1])
                # If disc detected get info
                # No disk[2] > 0 error.
                """
                make_disco_info_command = ['makemkvcon', '-r', '--cache=1', 'info',
                                           'dev:' + formatted_device_string,makeMkv_profile_options]
                message_Logging_Queue.put([app_log_mesg, "Make run command on dev: test path: " + str(make_disco_info_command)])
                print("Make run command on dev: test path: " + str(make_disco_info_command))
                subprocessReturnQueue.put(make_disco_info_command)
                main_return_subprocess_thread = main_return_subprocess_thread_Class()
                main_return_subprocess_thread.subprocess_return_thread.start()
                result = subprocessResultsQueue.get()
                subprocessResultsQueue.task_done()
                #print(result)
                message_Logging_Queue.put([make_log_mesg, result])
                diskCheckResultsQueue.put(result)

                
                #disk_Check_Queue.task_done()
                self.stop()
                trigger_Shutdown()
        print("=>Return drive check thread End!<=")
        #[Above was commented out to here]

def clear_test_log () :

    with open(output_file_path + output_file_name, 'w') as f :
        f.truncate()
        f.close()
    logging.info("Test log file cleared!")

class main_return_subprocess_thread_Class(threading.Thread):
   def __init__(self):
       super(main_return_subprocess_thread_Class, self).__init__()
       self.subprocess_return_thread = Thread(target=self.run)
       self._stop = threading.Event()
       self.subprocess_return_thread.name = "subprocess_return_thread"

   def stop(self):
       self._stop.set()

   def stopped(self):
       return self._stop.isSet()

   def run(self):
       process = subprocessReturnQueue.get()
       p = subprocess.Popen(process, stdout=PIPE)
       #while p.returncode is None:
       returned_data = (p.communicate()[0])

       message_Logging_Queue.put([app_log_mesg, "== Executed Command without error! =="])
       formatted_data = returned_data.decode('ascii').replace("'", "")
       subprocessResultsQueue.put(formatted_data)
       subprocessReturnQueue.task_done()

       print("=>Return subprocess thread end!<=")

#def run_subprocess_command(command_arg):


def initialize(search_bluray=True,search_Dvd=True, search_Cd=False, search_altDvd = True) :
    """Initialize function

        Main entry point into program.
        Checks OS type, Runs Make command to scan all drives.
        Determines drive type and Maps found drive to correct device Queue.

        Args:
            search_bluray: Blueray search Flag
            search_Dvd: Dvd search Flag
            search_Cd: CD search Flag
            search_altDvd: Alt DVD Flag (????)
    """

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
        clear_test_log()
        message_Logging_Queue.put([app_log_mesg,"Lunix Platform OS detected..."])
        time.sleep(1)
        #newLog = LogMessage(app_log_mesg, "Grabbing Device/Drive info:")
        message_Logging_Queue.put([app_log_mesg, "Grabbing Device/Drive info:"])
        #newLog = LogMessage(app_log_mesg, "Lunix Platform OS detected...")
        message_Logging_Queue.put([app_log_mesg,"==============================="])
        find_devices_command = ["makemkvcon", "-r", "--cache=1", "info", "disc:9999",makeMkv_profile_options]
        subprocessReturnQueue.put(find_devices_command)
        main_return_subprocess_thread = main_return_subprocess_thread_Class()
        main_return_subprocess_thread.subprocess_return_thread.start()
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
        if not found_bray and working_Object.__contains__("BDDVD") :
            found_bray = True
            br_Device_Object = device_Object(working_Object)
            bray_dev = working_Object
        elif not found_dvd and working_Object.__contains__("DVD") :
            found_dvd = True
            dvd_Device_Object = device_Object(working_Object)
            dvd_dev = working_Object


    if found_bray :
        message_Logging_Queue.put([app_log_mesg,"Found Blu-Ray device!"])
        message_Logging_Queue.put([app_log_mesg, br_Device_Object.print_Short_Raw()])
        BR_Device_List[br_Device_Object.deviceName] = br_Device_Object
    if found_dvd :
        message_Logging_Queue.put([app_log_mesg,"Found DVD device!"])
        message_Logging_Queue.put([app_log_mesg, dvd_Device_Object.print_Short_Raw()])
        DVD_Device_List[dvd_Device_Object.deviceName] = dvd_Device_Object
        #print("Added to DVD list: "+DVD_Device_List[dvd_Device_Object.deviceName].print_Short_Raw())

    start()
    print("Finished init!")


def trigger_Shutdown():
    SHUTDOWN_TRIGGERED = True


def shutdown():
    """
        Trigger stopping of program
        - Stopping main longest running thread first.
    """

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
    subprocessReturnQueue.join()
    subprocessResultsQueue.join()
    subprocessQueue.join()
    disk_Check_Queue.join()
    diskCheckResultsQueue.join()
    returned_Data_Queue.join()

    print("End of program!")

def start_app_Threads():
    main_drive_check_thread.drive_Check_Thread.start()

    main_logging_thread.loggingThread.start()

#Keep these here!
main_logging_thread = main_logging_thread_Class()
main_drive_check_thread = main_drive_check_thread_Class()


"""
Need to call functions in this order:
- start_app_Threads() <- When starting server
- initialize() <- starts server logic

When shutting down:
- shutdown()
"""




