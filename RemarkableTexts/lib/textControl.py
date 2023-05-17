from subprocess import Popen, PIPE
from imessage_reader import fetch_data
from datetime import datetime
import os
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
        set img to (POSIX file targetFileToSend)

        tell application "Messages" #Open Messages application to type in details
            activate
            send img to participant phoneNumber of account 2 --1 =imessage, 2=SMS, did not try other numbers
            delay 1
            quit
        end tell
    end run'''

SEND_IMAGE_LAPTOP = '''
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
DB_PATH = os.path.expanduser("~") + "/Library/Messages/chat.db-wal"


class textController:
    def __init__(self, debug=False):
        self.mtime_last = os.path.getmtime(DB_PATH)
        self.recent_attachments = self.get_most_recent_hundred_attachments()
        self.debug = debug

    def _get_attachments_sorted_by_modified_date(self):
        folder_path = '~/Library/Messages/Attachments'
        folder_path = os.path.expanduser(folder_path)

        files = []

        for root, _, filenames in os.walk(folder_path):
            for filename in filenames:
                if '.DS_Store' not in filename:
                    file_path = os.path.join(root, filename)
                    created_date = datetime.fromtimestamp(os.path.getmtime(file_path))
                    files.append((file_path, created_date))

        sorted_files = sorted(files, key=lambda f: f[1])
        return sorted_files

    def get_most_recent_hundred_attachments(self):
        return self._get_attachments_sorted_by_modified_date()[-100:]


    def get_new_attachments(self):
        latest = self.get_most_recent_hundred_attachments()

        index=0
        while(latest[index-1] not in self.recent_attachments):
              index -= 1

        self.recent_attachments = latest

        if index==0:
              print('no new attachments recognized')
              return []

        else:
              print('got ' + str(abs(index)) + ' new attachments')
              return latest[index:]


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
        mtime_cur = os.path.getmtime(DB_PATH)

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


    def getTextsWithAttachments(self):
        '''returns texts with attachment texts replacing '<Message with no text, but an attachment.>' with
        ATTACHFILE:<filename> if there is a clear 1-to-1 map from messages to filenames of new attachments.
        Otherwise, messages are unaltered. '''

        #get new texts and new attachments
        messages = self.getTexts()
        attachments = self.get_new_attachments()

        #check count of '<Message with no text, but an attachment.>' in texts
        count = sum([m[1] == '<Message with no text, but an attachment.>' for m in messages])

        if count != len(attachments):
            print('new attachments and attachment texts are not equal lengths; skipping')
            return messages

        try:
            #fill in the attachment return None array with appropriate filepaths to attachments
            new_messages = []
            attach_index=0
            for i in range(len(messages)):
                if (messages[i][1] == '<Message with no text, but an attachment.>'):
                    m = list(messages[i])
                    m[1] = 'ATTACHFILE:' + attachments[attach_index][0]
                    attach_index += 1
                    new_messages.append(tuple(m))
                else:
                    new_messages.append(messages[i])

            return new_messages

        except Exception as e:
            #on error, fall back to just texts
            print('Error aligning attachments with messages')
            print(e)
            return messages





