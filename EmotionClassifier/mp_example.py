from multiprocessing import Process, Queue
import cv2
import numpy as np
import time


def raw_display(q):
   cv2.namedWindow ('raw_stream')

   while True:

       #get latest frame
       frame = q.get()
       while not q.empty():
           frame = q.get()

       cv2.imshow ('raw_stream', frame)
       cv2.waitKey(1)


def proc_display(q):
   cv2.namedWindow ('classifier')

   while True:

       #get latest frame
       frame = q.get()
       while not q.empty():
           frame = q.get()

       time.sleep(3)

       cv2.imshow ('classifier', frame)
       cv2.waitKey(1)


if __name__ == '__main__':

   q1 = Queue()
   q2 = Queue()

   p1 = Process(target=raw_display, args=(q1,))
   p2 = Process(target=proc_display, args=(q2,))

   p1.start()
   p2.start()

   video=cv2.VideoCapture(1)  #requisting the input from the webcam or camera

   while video.isOpened():  #checking if are getting video feed and using it
      _,frame = video.read()
      q1.put(frame)
      q2.put(frame)

   p.join()
   cv2.cv.DestroyAllWindows()
