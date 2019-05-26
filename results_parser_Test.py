import meta_search
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
    
    *Need to grab details from title track
    *Also need to grab sTracks number and index start range
    
'''
tempObject.update_Main_Title(str(ordered_list[0]))
print(tempObject.movie_name)
print(meta_search.imdb_search(tempObject.get_movie_Name()))

print("+++++++++++++++++++++\n")
print(tempObject.print_Main_Title_SoundTracksInfo_Summary())
print(tempObject.print_Main_Title_SoundTracksInfo())
#print(meta_search.imdb_search("ant man"))