import argparse
import sys
from datetime import datetime

def logtext(text,log_path="dronepi.log"):
    """
        print plain text to logfile
    """
    f = open(log_path, 'a+')
    f.write(f'{text}\n')
    f.close()
    print(text)

def logevent(event,level=1,log_path="dronepi.log",counter=None):
    """
        Event = message
        level: 0 = DEBUG, 1 = INFO, 2 = WARNING, 3 = ERROR, 4 = FATAL
        Prints to logfile and terminal. 
    """
    # Only check for a verbose argument
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-v", "--verbose", help="Increase output verbosity",action="store_true")
    args, unknown = parser.parse_known_args()
    
    # 0 = DEBUG
    # 1 = INFO
    # 2 = WARNING
    # 3 = ERROR
    # 5 = SUCCESS
    levelcode = ["DEBUG","INFO","WARNING","ERROR","FATAL"]
    
    if counter:
        counter.increment(level)
    
    if level>=1 or args.verbose:
        if (level == 3 or level == 4):
            # Enable red bold if Error
            formatStart = "\033[91m\033[1m"
        elif (level == 2):
            # Enable orange bold if Warning
            formatStart = "\033[93m\033[1m"
        elif (level == 5):
            # Enable green if Success
            formatStart = "\033[92m\033[1m"
        else:
            formatStart = ""
            
        if (level >= 2):
            # Disable formatting
            formatEnd = "\033[0m"
        else:
            formatEnd = ""
            
        print(f"{formatStart}[{levelcode[level]}] {event}{formatEnd}")
        
        
        
    f = open(log_path, 'a+')
    f.write(f'[{levelcode[level]}; {datetime.now().isoformat()}] {event}\n')
    f.close()
    
    if (level == 4):
        # raise Exception(f"FATAL ERROR: {event}")
        exit()

class logCounter:
    success = 0
    fatal = 0
    error = 0
    warning = 0
    info = 0
    debug = 0
    
    def increment(self, type):
        if type == 0:
            self.debug = self.debug+1
        elif type == 1:
            self.info = self.info+1
        elif type == 2:
            self.warning = self.warning+1
        elif type == 3:
            self.error = self.error+1
        elif type == 4:
            self.fatal = self.fatal+1
            
    def get(self,type=None):
        if type == 0:
            return self.debug
        elif type == 1:
            return self.info
        elif type == 2:
            return self.warning
        elif type == 3:
            return self.error
        elif type == 4:
            return self.fatal
        elif type == None:
            return [self.debug,self.info,self.warning,self.error]
        