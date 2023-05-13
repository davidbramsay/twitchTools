from subprocess import Popen, PIPE
from imessage_reader import fetch_data
from datetime import datetime
from os.path import expanduser, getmtime
import time

from .addresses import ADDRESS_BOOK


#osascript to send texts
SEND_TEXT = '''
    on run {phoneNumber, message}
	  tell application "Messages"
		activate
		send message to participant phoneNumber of account 2 --1 =imessage, 2=SMS, did not try other numbers
        delay 1
        quit
	  end tell
    end run'''

SEND_IMAGE = '''
    on run {phoneNumber, targetFileToSend}
        tell application "System Events" to set targetMessage to (targetFileToSend as POSIX file)
	
        tell application "Messages"                 #Open Messages application to type in details
            activate
        end tell
	
        tell application "System Events" to tell application process "Messages"
            keystroke "n" using {command down}	    #This command opens a new message tab
            delay 0.8
            keystroke phoneNumber			    #The reciepient's number is typed in
            delay 0.2
            keystroke return
            delay 0.2
            keystroke tab
            delay 0.2
            set the clipboard to targetMessage	    #The file is then pasted in
            keystroke "v" using {command down}
            delay 0.3
            keystroke return					    #Message is sent
            delay 1
            quit
        end tell
    end run    
'''

#the path to the iMessage database
DB_PATH = expanduser("~") + "/Library/Messages/chat.db-wal"


class textController:
    def __init__(self, debug=False):
        self.mtime_last = getmtime(DB_PATH)
        self.debug = debug


    def sendText(self, numstring, text):
        ''' sends a text to numstring.  Be sure numstring == '+10123456789' (has no delimiters)'''

        p = Popen(['osascript', '-'] + [numstring, text], stdin=PIPE, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate(SEND_TEXT.encode(encoding='UTF-8'))
        print (p.returncode, stdout, stderr)
        return p.returncode

    def sendImage(self, numstring, imageFile):
        ''' sends an image (full filepath) to numstring.  Be sure numstring == '+10123456789' (has no delimiters)'''

        p = Popen(['osascript', '-'] + [numstring, imageFile], stdin=PIPE, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate(SEND_IMAGE.encode(encoding='UTF-8'))
        print (p.returncode, stdout, stderr)
        return p.returncode


    def getName(self, numstring):
        '''given a numstring with +12223334444, return name associated if in dictionary (otherwise return string) '''

        if len(numstring) != 13:
            print('Invalid numstring')
            return numstring

        try:
            return ADDRESS_BOOK[numstring]
        except:
            return numstring


    def getAllSortedTexts(self):
        '''grab all texts sorted by date (user id, message, date, service, account, is_from_me) '''

        fd = fetch_data.FetchData()
        messages = fd.get_messages()

        #sort by converted timestamp strings to datetime
        return sorted(messages, key=lambda tup: datetime.strptime(tup[2], '%Y-%m-%d %H:%M:%S'))


    def getLatestTexts(self, extranums=None):
        ''' return a dict of nums from addressbook, and any extranums, indexing their most recent text '''

        returnvals = {}

        #get numstrings from addressbook as a set 
        nums = set(ADDRESS_BOOK.keys())

        #add any additional numstrings (set removes duplicates)
        for k in extranums:
            nums.add(k)

        #get sorted messages
        messages = self.getAllSortedTexts()

        #iterate backwards until we have the latest for each num in set nums
        index = len(messages)-1

        while len(nums) and index>=0:
            m = messages[index]

            if not m[5] and m[0] in nums:
                if self.debug:
                    print('GOT LATEST TEXT FOR ' + str(m[0]))

                returnvals[m[0]] = m[1]    
                nums.remove(m[0])

            index -= 1    

        return returnvals
            


    def getTexts(self):
        '''get any new texts since last time we got new texts, or since initialized'''

        #get last modified time for db
        mtime_cur = getmtime(DB_PATH)

        #if its been modified since we last looked...
        if mtime_cur > self.mtime_last:

            if self.debug:
                print('DB: prev mtime = ' + str(self.mtime_last) + ' | ' + datetime.fromtimestamp(self.mtime_last).strftime("%m/%d/%Y, %H:%M:%S"))
                print('DB:  new mtime = ' + str(mtime_cur) + ' | ' + datetime.fromtimestamp(mtime_cur).strftime("%m/%d/%Y, %H:%M:%S"))

            #get all sorted messages
            messages = self.getAllSortedTexts()    

            #get cutoff time based on last time we had a modification to the database
            cutoff_time = datetime.fromtimestamp(self.mtime_last)

            #get index of earliest text that is past the cutoff-time
            index = 0
            while(datetime.strptime(messages[index-1][2], '%Y-%m-%d %H:%M:%S') > cutoff_time):
                index -= 1

            if self.debug:
                print('New Text Count = ' + str(-1*index))
                print('Earliest New Text Time = ' + datetime.strptime(messages[index][2], '%Y-%m-%d %H:%M:%S').strftime("%m/%d/%Y, %H:%M:%S"))    

            #update out cut-off time
            self.mtime_last = mtime_cur 

            #return just the new messages, in order, if we have some
            if index<0:
                return messages[index:]    


        #else not modified since we last checked
        #return empty array
        return []



