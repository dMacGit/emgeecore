import core
import os

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
print(tempObject.return_DiskInfo())
print(tempObject.return_VideoTrackInfo())
print(tempObject.return_SoundTrackInfo())

size_dict = core.grab_largest_titles_Size(tempObject.return_VideoTrackObject())
print(size_dict)
print("Ordered tracks: "+str(core.order_largest_tracks(size_dict)))
#print(core.print_Tracks_Array(core.grab_largest_titles_Size(tempObject.return_VideoTrackObject())))
