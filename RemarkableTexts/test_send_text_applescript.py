from subprocess import Popen, PIPE

scpt = '''
    on run {phoneNumber, message}
	  tell application "Messages"
		activate
		send message to participant phoneNumber of account 2 --1 =imessage, 2=SMS, did not try other numbers
	  end tell
    end run'''

args = ['0123456789', 'this text will get sent to 012-345-6789']

p = Popen(['osascript', '-'] + args, stdin=PIPE, stdout=PIPE, stderr=PIPE)
stdout, stderr = p.communicate(scpt.encode(encoding='UTF-8'))
print (p.returncode, stdout, stderr)

