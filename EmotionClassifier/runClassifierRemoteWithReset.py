import socket
import sys
import pickle
import struct
import cv2
import numpy as np
import time
import paramiko
import yaml

with open('config.yml', 'r') as yml_file:
    cfg = yaml.load(yml_file, Loader=yaml.SafeLoader)
ssh_client = paramiko.SSHClient()
ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh_client.connect(cfg['server'], username=cfg['username'], password=cfg['password'])
stdin,stdout,_ = ssh_client.exec_command("pm2 restart 0")
print(stdin)
print(stdout)
time.sleep(3)

s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.connect((cfg['server'],cfg['port']))

data = b''
payload_size = struct.calcsize("L")

video=cv2.VideoCapture(2)  #requisting the input from the webcam or camera

while video.isOpened():  #checking if are getting video feed and using it
    _,frame = video.read()

    cv2.imwrite('temp.jpg', frame)
    #SEND IT OFF
    # Serialize frame
    data = pickle.dumps(frame)
    # Send message length first
    message_size = struct.pack("L", len(data))
    # then data
    s.sendall(message_size + data)

    print('sent: ' + str(frame.shape))

    #GET IT BACK
    data = b''

    #get message size
    while len(data) < payload_size:
        data += s.recv(4096)

    packed_msg_size = data[:payload_size]
    data = data[payload_size:]
    msg_size = struct.unpack("L", packed_msg_size)[0]

    #get all data based on message size
    while len(data) < msg_size:
        data += s.recv(4096)

    print('got message size:' + str(msg_size))

    frame_data = data[:msg_size]
    data = data[msg_size:]

    # Extract frame
    new_frame = pickle.loads(frame_data)

    #this is the part where we display the output to the user
    cv2.imshow('classifier', new_frame)

    key=cv2.waitKey(1) 
    if key==ord('q'):   # here we are specifying the key which will stop the loop and stop all the processes going
        break

video.release()
