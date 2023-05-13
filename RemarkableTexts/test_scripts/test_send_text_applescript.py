from subprocess import Popen, PIPE

scpt = '''
    on run {phoneNumber, message}
	  tell application "Messages"
		activate
		send message to participant phoneNumber of account 2 --1 =imessage, 2=SMS, did not try other numbers
	  end tell
    end run'''



scpt_image_BKUP = '''
    on run {phoneNumber, targetFile}

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
            set the clipboard to (read (POSIX file targetFile) as JPEG picture)
            keystroke "v" using {command down}
            delay 0.3
            keystroke return					    #Message is sent
        end tell
    end run    
'''

scpt_image = '''
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
        end tell
    end run    
'''

scpt_image_BKUP = '''
    on run {phoneNumber, imageFolder}
        tell application "System Events"
            set paths to POSIX path of disk items of folder imageFolder
        end tell

        set imgs to {}
        repeat with f in paths
            set imgs to imgs & (POSIX file f)
        end repeat

        tell application "Messages"
            activate
            repeat with img in imgs
                send img to participant phoneNumber of account 2 --1 =imessage, 2=SMS, did not try other numbers
            end repeat    
        end tell
    end run'''


scpt_image_BKUP2 = '''
    on run {phoneNumber, imagePath}
        tell application "Messages"
            activate
            set theAttachment to POSIX file imagePath
            send theAttachment to participant phoneNumber of account 2 --1 =imessage, 2=SMS, did not try other numbers
        end tell
    end run'''

'''


args = ['0123456789', 'this text will get sent to 012-345-6789']

p = Popen(['osascript', '-'] + args, stdin=PIPE, stdout=PIPE, stderr=PIPE)
stdout, stderr = p.communicate(scpt.encode(encoding='UTF-8'))
print (p.returncode, stdout, stderr)
'''

args = ['+12223334444', '/Users/davidramsay/Documents/TwitchTools/RemarkableTexts/temp/13105931914bec658c4.jpg']

p = Popen(['osascript', '-'] + args, stdin=PIPE, stdout=PIPE, stderr=PIPE)
stdout, stderr = p.communicate(scpt_image.encode(encoding='UTF-8'))
print (p.returncode, stdout, stderr)
