from multiprocessing import Process, Pipe
import cv2
import numpy as np
import time

# in the previous, we had the main loop grab frames and queue them
# off to two display processes.  This doesn't seem to work well
# on Linux; it seems one display process
# perhaps there is an issue with copy by reference?

#in this example, we'll try the inverse:
#we'll have a main loop which grabs a frame, sends it off to the secondary
#processing thread, and then displays both-- but only displays the second
#if it has been updated by the secondary thread

def proc_display(pipe):

   img_new = cv2.imread("templates/emotion_template_gaze.png")
   frame = img_new
   while True:

       time.sleep(3)
       cv2.putText(frame, 'TESTING', (300,200), cv2.FONT_HERSHEY_TRIPLEX, 1.6, (76,52,5), 2, cv2.LINE_AA)

       #send it and wait for a new one
       pipe.send(frame)
       frame = pipe.recv()



if __name__ == '__main__':

   cv2.namedWindow ('raw_stream')
   cv2.namedWindow ('processed_stream')

   secondary_p, primary_p = Pipe(duplex=True)

   p = Process(target=proc_display, args=(secondary_p,))
   p.daemon = True
   p.start()

   video=cv2.VideoCapture(1)  #requisting the input from the webcam or camera

   while video.isOpened():
      _,frame = video.read()

      if primary_p.poll():
          proc_frame = primary_p.recv()
          cv2.imshow('processed_stream', proc_frame)
          primary_p.send(frame)

      cv2.imshow('raw_stream', frame)
      key=cv2.waitKey(1) 
      if key==ord('q'):   # here we are specifying the key which will stop the loop and stop all the processes going
         break

   video.release() 
   cv2.destroyWindow('raw_stream')
   cv2.destroyWindow('processed_stream')
