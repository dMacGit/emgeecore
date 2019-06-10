from threading import Thread
from subprocess import PIPE
from queue import Queue
import threading
import meta_search
import core
import os
import subprocess

'''
    This Results_parser_Test.py class is used to debug/test the core.py code
    without running the entire application.
    
    Results_parser_Test.py will not be part of the Front end. 
'''

# While still testing named "test.log. Change to "makemkvcon.log" later
output_file_name = 'test.log'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

output_log_dir = os.path.join(BASE_DIR, 'logs/') #'/logs'
output_file_path = output_log_dir

test_log_data = None

def open_test_log () :
    whole_file_path = output_file_path + output_file_name
    print(whole_file_path)
    with open(whole_file_path, 'r') as f :
        test_log_data = f.read()
        f.close()
    return test_log_data

def parse_log_data(data):
    print("test log data as follows:")
    print("="*20)
    print(data)
    print("=" * 20)

    split_lines = data.split("\n")
    line_count = 0
    for line in split_lines:
        #First check "MSG:" and string "Operation successfully completed"
        if str(line).__contains__("MSG:") and str(line).__contains__("Operation successfully completed"):
            #Check trailing TCOUNT line
            #First saftey check for index out of range
            if len(split_lines) > line_count+1:
                if str(split_lines[line_count+1]).__contains__("TCOUNT"):
                    track_number = str(split_lines[line_count+1]).split(":")[1]
                    print(track_number+" Title tracks found")
        line_count += 1

tempObject = core.disc_metaData(open_test_log())
print("===Media Type confirmed: ",tempObject.get_Media_Type(),"===")
#print(tempObject.print_DiskInfo())
#print(tempObject.print_VideoTrackInfo())
print(tempObject.print_SoundTrackInfo())

size_dict = core.grab_largest_titles_Size(tempObject.get_VideoTrackObject())
'''
Need to use tempObject.get_VideoTrackObject() to return list, then grab resutling largest title and input file name
into meta_core search for media meta data info.
'''
#tempObject.get_VideoTrackObject()
#titlesList.get("Title:"+str(title_index))



print("Summarized title list [Un-ordered]",size_dict)
ordered_list = core.order_largest_tracks(size_dict)
print("Ordered indexes [Based on file size]: "+str(ordered_list))

tracks_list = tempObject.get_VideoTrackObject()
main_title = tracks_list.get("Title:"+str(ordered_list[0]))
print("Largest title is",str(main_title))

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
tempObject.update_Main_Title(str(ordered_list[0]))
print(tempObject.movie_name)
print(meta_search.imdb_search(tempObject.get_movie_Name()))

'''print("+++++++++++++++++++++\n")
print(tempObject.print_Main_Title_SoundTracksInfo_Summary())
print(tempObject.print_Main_Title_SoundTracksInfo())'''
#print(meta_search.imdb_search("ant man"))

selected_title_index = ordered_list[0]
'''if selected_title_index < 10 :
    selected_title_index = str(selected_title_index).zfill(1)
print("Selected track:",selected_title_index)'''
#makemkvcon --profile=/home/phantom/.MakeMKV/phantoms.mmcp.xml --messages="/media/phantom/My Files/Documents/Python Projects/Emgee_Core/logs/messages.log" --progress="/media/phantom/My Files/Documents/Python Projects/Emgee_Core/logs/progress.log" mkv disc:0 0 /media/media/Rips/
rip_command = 'makemkvcon --profile=~/.MakeMKV/phantoms.mmcp.xml '+core.makeMkv_progress_command+' mkv disc:0 '+str(selected_title_index),'c:\Rip\\'

disc = 0
make_rip_command = ['makemkvcon', core.makeMkv_profile_options, core.makeMkv_messages_option, core.makeMkv_progress_command, 'mkv', 'disc:'+str(disc),str(selected_title_index),core.makeMkv_media_dest_dir]

print(rip_command)
print(make_rip_command)

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
       print(process)
       p = subprocess.Popen(process, stdout=PIPE)
       #while p.returncode is None:
       returned_data = (p.communicate()[0])

       print("== Executed Command without error! ==")
       formatted_data = returned_data.decode('ascii').replace("'", "")
       print(formatted_data)
       subprocessReturnQueue.task_done()

       print("=>Return subprocess thread end!<=")
       main_return_subprocess_thread.stop()



subprocessReturnQueue = Queue()
#find_devices_command = ["makemkvcon", "-r", "--cache=1", "info", "disc:9999",core.makeMkv_profile_options]

main_return_subprocess_thread = main_return_subprocess_thread_Class()
main_return_subprocess_thread.subprocess_return_thread.start()
subprocessReturnQueue.put(make_rip_command)
while main_return_subprocess_thread.stopped() is False:
    pass
    #wait
subprocessReturnQueue.join()