import cv2
import numpy as np
import time


video=cv2.VideoCapture(2)  #requisting the input from the webcam or camera

img_new = cv2.imread("templates/emotion_template_gaze.png")


while video.isOpened():  #checking if are getting video feed and using it
    _,frame = video.read()
    img_new[233:233+314,49:49+314] = cv2.resize(frame, (314,314))

    #img_resize = cv2.resize(img_new, (308,483))
    img_resize = cv2.resize(img_new, (462,725))

    #this is the part where we display the output to the user
    cv2.imshow('classifier', img_resize)

    key=cv2.waitKey(1) 
    if key==ord('q'):   # here we are specifying the key which will stop the loop and stop all the processes going
        break

video.release()
