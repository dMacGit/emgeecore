from core import start_app_Threads, initialize, trigger_Shutdown
import signal
import sys

'''
    This Main.py class is the entry point to run the core.py
    application standalone.
    
    Main.py will not be part of the Front end. 
    Currently this is just used to test/debug and develop this core.py logic.
'''

def signal_handler(sig, frame):
        print('You pressed Ctrl+C!')
        trigger_Shutdown()
        sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
start_app_Threads()
initialize()

print('Press Ctrl+C')
signal.pause()


#Wait for termination
#shutdown()