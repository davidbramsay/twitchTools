import socket
from emoji import demojize, emojize, emoji_count
from datetime import datetime
import random
from apscheduler.schedulers.background import BackgroundScheduler
import yaml
import subprocess
import urllib.request


#This sends a message to chat every minute with instructions for labeling David's behavior.
#It also receives chats, logs them all to chatLogs for the session that is open, and updates 'currentChatWindow.txt'
#with a string of recent annotations.

#Some of the basic structure of this code was inspired by https://github.com/whatuptkhere/SimpleTwitchCommander

EMOJIS=["Here are some to copy/paste: \U0001F600\U0001F603\U0001F604\U0001F601\U0001F606\U0001F605\U0001F923\U0001F602\U0001F642\U0001F643\U0001FAE0\U0001F609\U0001F60A\U0001F607\U0001F970\U0001F60D\U0001F929\U0001F618\U0001F617\U0001F61A\U0001F619\U0001F972","\U0001F60B\U0001F61B\U0001F61C\U0001F92A\U0001F61D\U0001F911\U0001F917\U0001F92D\U0001FAE2\U0001FAE3\U0001F92B\U0001F914\U0001FAE1", "\U0001F910\U0001F928\U0001F610\U0001F611\U0001F636\U0001F60F\U0001F612\U0001F644\U0001F62C\U0001F925\U0001F92F", "\U0001F615\U0001FAE4\U0001F61F\U0001F641\U0001F62E\U0001F62F\U0001F632\U0001F633\U0001F97A\U0001F979\U0001F626\U0001F627\U0001F628\U0001F630\U0001F625\U0001F622\U0001F62D\U0001F631\U0001F616\U0001F623\U0001F61E\U0001F613\U0001F629\U0001F62B\U0001F971\U0001F624\U0001F621\U0001F620\U0001F92C\U0001F47F", "\U0001F60C\U0001F614\U0001F62A\U0001F924\U0001F634\U0001F637\U0001F912\U0001F915\U0001F922\U0001F92E\U0001F927\U0001F975\U0001F976\U0001F974\U0001F635", "\U0001F920\U0001F973\U0001F978\U0001F60E\U0001F913\U0001F9D0\U0001F608\U0001F480\U0001F4A9\U0001F921. More at https://getemoji.com/"]

emojimessage = " | ".join(EMOJIS)

currentActivity = ''

with open('config.yaml', 'r') as f:
    OAUTH_TOKEN = yaml.load(f, Loader=yaml.FullLoader)['token']



class TwitchControl:

    def __init__(self):
        self.server = 'irc.chat.twitch.tv'
        self.port = 6667
        self.nickname = 'dramsay9'
        self.token = OAUTH_TOKEN
        self.channel = '#dramsay9'


        self.sched = BackgroundScheduler()

        self.sock = socket.socket()
        self.sock.connect((self.server,self.port))
        self.sock.send(f"PASS {self.token}\n".encode('utf-8'))
        self.sock.send(f"NICK {self.nickname}\n".encode('utf-8'))
        self.sock.send(f"JOIN {self.channel}\n".encode('utf-8'))

        self.lastAnnotations = []

        now = datetime.now()
        current_time = now.strftime("%m%d%y_%H%M%S")
        self.filename = 'chatLogs/' + current_time + '_chatlog.txt'

        self.sched.add_job(self.pullCurrentActivity, 'interval', seconds=3)
        self.sched.add_job(self.sendReminder, 'interval', seconds=60)
        self.sched.start()


    def loop(self):

        while True:
            resp = self.sock.recv(2048).decode('utf-8')
            if resp.startswith('PING'):
                self.sock.send("PONG\n".encode('utf-8'))
            elif len(resp) > 0:
                try:
                    now = datetime.now()
                    currentTime = now.strftime("%H:%M:%S")

                    respClean = demojize(resp)
                    msgComponents = respClean.split(" ",3)

                    msgUser = msgComponents[0]
                    msgUser = msgUser[msgUser.find(':')+1: msgUser.find('!')]

                    msgContent=msgComponents[3][1:]

                    print('TIME:' + currentTime)
                    print('USER:' + msgUser)
                    print('CONTENT:' + msgContent)
                except:
                    msgUser = 'PARSE_FAILED'
                    msgContent = respClean

                #no matter what, append/log the chat
                with open(self.filename, 'a+') as f:
                    f.write(currentTime + ',' + msgUser + ',' + msgContent)

                IS_COMMAND=True

                if msgContent.find("!stress") >=0:
                    try:
                        val = int(msgContent.replace("!stress",''))
                        if(val==1):
                            desc = "very calm"
                            self.lastAnnotations.append(currentTime + ': ' + msgUser + ' says David looks ' + desc + '.')
                        elif(val==2):
                            desc = "calm"
                            self.lastAnnotations.append(currentTime + ': ' + msgUser + ' says David looks ' + desc + '.')
                        elif(val==3):
                            desc = "neither calm nor stressed"
                            self.lastAnnotations.append(currentTime + ': ' + msgUser + ' says David looks ' + desc + '.')
                        elif(val==4):
                            desc = "stressed"
                            self.lastAnnotations.append(currentTime + ': ' + msgUser + ' says David looks ' + desc + '.')
                        elif(val==5):
                            desc = "very stressed"
                            self.lastAnnotations.append(currentTime + ': ' + msgUser + ' says David looks ' + desc + '.')

                    except Exception as e:
                        print('failed on stress message: ' + msgContent)
                        print(e)
                elif msgContent.find("!focus") >=0:
                    try:
                        val = int(msgContent.replace("!focus",''))
                        if(val==1):
                            desc = "very distracted"
                            self.lastAnnotations.append(currentTime + ': ' + msgUser + ' says David looks ' + desc + '.')
                        elif(val==2):
                            desc = "distracted"
                            self.lastAnnotations.append(currentTime + ': ' + msgUser + ' says David looks ' + desc + '.')
                        elif(val==3):
                            desc = "neither distracted nor focused"
                            self.lastAnnotations.append(currentTime + ': ' + msgUser + ' says David looks ' + desc + '.')
                        elif(val==4):
                            desc = "focused"
                            self.lastAnnotations.append(currentTime + ': ' + msgUser + ' says David looks ' + desc + '.')
                        elif(val==5):
                            desc = "totally lost in what he's doing"
                            self.lastAnnotations.append(currentTime + ': ' + msgUser + ' says David looks ' + desc + '.')

                    except:
                        print('failed on focus message: ' + msgContent)
                elif msgContent.find("!tired") >=0:
                    try:
                        val = int(msgContent.replace("!tired",''))
                        if(val==1):
                            desc = "very energized"
                            self.lastAnnotations.append(currentTime + ': ' + msgUser + ' says David looks ' + desc + '.')
                        elif(val==2):
                            desc = "energized"
                            self.lastAnnotations.append(currentTime + ': ' + msgUser + ' says David looks ' + desc + '.')
                        elif(val==3):
                            desc = "neither energized nor tired"
                            self.lastAnnotations.append(currentTime + ': ' + msgUser + ' says David looks ' + desc + '.')
                        elif(val==4):
                            desc = "tired"
                            self.lastAnnotations.append(currentTime + ': ' + msgUser + ' says David looks ' + desc + '.')
                        elif(val==5):
                            desc = "very tired"
                            self.lastAnnotations.append(currentTime + ': ' + msgUser + ' says David looks ' + desc + '.')
                    except:
                        print('failed on tired message: ' + msgContent)
                elif msgContent.find("!mood") >=0:
                    try:
                        isolated_emoji = msgContent.split(':')[1]
                        sanitized_emoji = emojize(':'+isolated_emoji+':')
                        if (emoji_count(sanitized_emoji)):
                            self.lastAnnotations.append(currentTime + ': ' + msgUser + ' says David is feeling ' + sanitized_emoji + '.')
                        else:
                            print('failed on mood message' + msgContent)
                    except:
                        print('failed on mood message: ' + msgContent)
                else:
                    IS_COMMAND=False

                if IS_COMMAND:
                    #update display file with the last annotations, capped at 50
                    if (len(self.lastAnnotations)>=50):
                        self.lastAnnotations.pop(0)

                    with open(r'currentChatWindow.txt', 'w') as f:
                        for line in self.lastAnnotations:
                            f.write("%s\n" % line)

    def pullCurrentActivity(self):
        global currentActivity
        try:
            contents = urllib.request.urlopen("http://streampi.media.mit.edu:5000/currentActivity.txt").read()
            activity = str(contents).split('\'')[-2]
            if activity != currentActivity:
                print('got new activity:' + activity)
                subprocess.Popen('echo "' + activity + '" > /Users/davidramsay/Documents/TwitchTools/CurrentActivity.txt', shell=True)
                currentActivity = activity

        except Exception as e:
            print(e)
            print('Failed to grab current activity.txt')

    #subprocess.Popen('curl http://streampi.media.mit.edu:5000/currentActivity.txt > /Users/davidramsay/Documents/TwitchTools/CurrentActivity.txt', shell=True)

    def sendReminder(self):
        outMessages = ["Is David looking focused? Rate David's focus using the command !focus {1-5}, where 1=very distracted, 2=distracted, 3=neutral, 4=focused, 5=totally lost in what he's doing (i.e '!focus 2').", "Is David looking stressed?  Rate David's stress using the command !stress {1-5}, where 1=very calm, 2=calm, 3=neutral, 4=stressed, 5=very stressed (i.e. '!stress 4').", "Is David looking tired?  Rate David's energy using the command !tired {1-5}, where 1=very energized, 2=energized, 3=neutral, 4=tired, 5=very tired (i.e. '!tired 5').", "How's David's feeling? Post a unicode emoji that represents his current emotion with the !mood command (i.e. `!mood \U0001F600'). " + emojimessage]

        message = 'PRIVMSG {} :{}\r\n'.format(self.channel.lower(), random.choice(outMessages))
        self.sock.send(message.encode('utf-8'))

    def close(self):
        console.log('CLOSE CALLED')
        self.sched.shutdown()

    def __enter__(self):
        return self

    def __exit__(self, *_, **__):
        self.close()

def main(argv=None):
    TwitchControl().loop()

main()
